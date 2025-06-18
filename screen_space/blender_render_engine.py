import math
import time

import bpy
from mathutils import Matrix, Vector
import numpy as np


class BlenderRenderEngine:
    def __init__(self, target_gp_obj: bpy.types.Object, far_clip_tolerance: float = 0.001, finite_difference_offset: float = 0.001):
        self.target_gp_obj = target_gp_obj
        self.far_clip_tolerance = far_clip_tolerance
        self.finite_difference_offset = finite_difference_offset

        bpy.context.scene.use_nodes = True
        compositor_tree = bpy.context.scene.node_tree
        self.compositor_links = compositor_tree.links
        self.compositor_nodes = compositor_tree.nodes
        self.render_layers = None
        self.viewer_node = None
        self.composite_node = None

        self.backup_use_combined = True
        self.backup_use_z = False
        self.backup_use_normal = False
        self.backup_use_position = False

    def initialize_compositor(self):
        """
        Clear all existing compositor nodes and links and initialize the compositor for BlenderRenderEngine.

        Warning:
            This will delete the current compositor node tree, removing all existing nodes and links.
            Any unsaved changes to the compositor setup will be lost.
        """
        self.compositor_links.clear()
        self.compositor_nodes.clear()
        self.render_layers = self.compositor_nodes.new("CompositorNodeRLayers")
        self.viewer_node = self.compositor_nodes.new("CompositorNodeViewer")
        self.viewer_node.use_alpha = True
        self.composite_node = self.compositor_nodes.new("CompositorNodeComposite")
        self.compositor_links.new(self.render_layers.outputs["Image"], self.composite_node.inputs[0])

    def _backup_render_passes(self):
        """
        Backup the current render pass settings.
        """
        view_layer = bpy.context.view_layer
        self.backup_use_combined = view_layer.use_pass_combined
        self.backup_use_z = view_layer.use_pass_z
        self.backup_use_normal = view_layer.use_pass_normal
        self.backup_use_position = view_layer.use_pass_position

    def _restore_render_passes(self):
        """
        Restore the render pass settings to their previous state.
        """
        view_layer = bpy.context.view_layer
        view_layer.use_pass_combined = self.backup_use_combined
        view_layer.use_pass_z = self.backup_use_z
        view_layer.use_pass_normal = self.backup_use_normal
        view_layer.use_pass_position = self.backup_use_position

    @staticmethod
    def _set_render_passes_from_render_layer(render_layer: str):
        """
        Enable only the necessary render pass for the given render layer.

        Args:
            render_layer (str): The name of the render layer ("Image", "Depth", "Normal", or "Position").
        """
        view_layer = bpy.context.view_layer
        view_layer.use_pass_combined = render_layer == "Image"
        view_layer.use_pass_z = render_layer == "Depth"
        view_layer.use_pass_normal = render_layer == "Normal"
        view_layer.use_pass_position = render_layer == "Position"

    @staticmethod
    def _viewer_rgb_pixels() -> np.ndarray:
        """
        Retrieve the RGB pixel data from the 'Viewer Node' image as a numpy array.

        Returns:
            np.ndarray: The RGB pixel data with shape (height, width, 3).

        Raises:
            ValueError: If the 'Viewer Node' image data is unavailable.
        """
        viewer_image = bpy.data.images.get("Viewer Node")
        if viewer_image is None or not viewer_image.has_data:
            raise ValueError("Viewer Node image data unavailable.")
        pixels = np.array(viewer_image.pixels[:], dtype=np.float32)
        width = viewer_image.size[0]
        height = viewer_image.size[1]
        assert pixels.shape[0] == width * height * 4, "Pixel data does not match image dimensions."
        return pixels.reshape(height, width, 4)[:, :, :3]  # Return RGB channels only

    def _render_pass_pixels(self, render_layer: str) -> np.ndarray:
        """
        Get the pixel data for a specific render layer pass.

        Args:
            render_layer (str): The name of the render layer to get the pass from. 
                Can be "Image", "Depth", "Normal", or "Position".

        Returns:
            np.ndarray: A numpy array of RGBA pixel data.

        Raises:
            ValueError: If compositor nodes are not initialized or the render layer output is not found.
        """
        if self.render_layers is None or self.viewer_node is None or self.composite_node is None:
            raise ValueError("Compositor nodes not initialized. Call initialize_compositor() first.")

        start_time = time.time()
        self.compositor_links.clear()
        BlenderRenderEngine._set_render_passes_from_render_layer(render_layer)
        self.compositor_links.new(self.render_layers.outputs["Image"], self.composite_node.inputs[0])

        render_layer_output = self.render_layers.outputs.get(render_layer)
        if render_layer_output is None:
            raise ValueError(f"Render layer output '{render_layer}' not found.")

        self.compositor_links.new(render_layer_output, self.viewer_node.inputs[0])

        bpy.ops.render.render(write_still=False)
        elapsed = time.time() - start_time
        print(f"Render pass '{render_layer}' took {elapsed:.3f} seconds.")

        return BlenderRenderEngine._viewer_rgb_pixels()

    def render_coverage_luminance_depth_direction(
            self,
            view_projection_matrix: Matrix,
            light: Vector,
            is_directional_light: bool = False,
            clip_luminance: bool = False,
            normalize_luminance: bool = False,
            orientation_offset: float = 0.0,
            camera_far_clip: float = 1.0
        ) -> np.ndarray:
        """
        Render a scene and extract coverage, luminance, depth, and direction information.

        This method performs multiple render passes to collect various scene attributes and
        processes them to compute a coverage masks, luminance, depth information, and
        screen-space direction vectors based on light direction.

        Args:
            view_projection_matrix (Matrix): The combined view and projection matrix.
            light (Vector): The light position (for point lights) or direction (for directional lights).
            is_directional_light (bool, optional): Whether the light is directional. Defaults to False.
            clip_luminance (bool, optional): Whether to clip luminance values to [0, 1]. Defaults to False.
            normalize_luminance (bool, optional): Whether to normalize luminance values. Defaults to False.
            orientation_offset (float, optional): Angular offset for orientation calculation in radians. Defaults to 0.0.
            camera_far_clip (float, optional): Camera's far clip distance. Defaults to 1.0.

        Returns:
            np.ndarray: A 5-channel array with shape (height, width, 5) containing:
                - Channel 0: Coverage mask (1.0 where geometry exists, 0.0 otherwise)
                - Channel 1: Luminance values
                - Channel 2: Depth values
                - Channel 3: Cosine of orientation angle
                - Channel 4: Sine of orientation angle
        """
        self._backup_render_passes()
        target_gp_hide_render = self.target_gp_obj.hide_render
        self.target_gp_obj.hide_render = True

        z = self._render_pass_pixels("Depth")[:, :, :1]
        z_threshold = camera_far_clip * (1.0 - self.far_clip_tolerance)
        coverage = (z < z_threshold).astype(np.float32)
        z = z * coverage

        rgb = self._render_pass_pixels("Image")
        luminance = (
            rgb[:, :, 0] * 0.299 +
            rgb[:, :, 1] * 0.587 +
            rgb[:, :, 2] * 0.114
        )[..., np.newaxis] * coverage
        if clip_luminance:
            luminance = np.clip(luminance, 0.0, 1.0)
        if normalize_luminance:
            # Only normalize over covered pixels
            covered = coverage > 0.5
            if np.any(covered):
                min_lum = luminance[covered].min()
                max_lum = luminance[covered].max()
                print(f"Luminance range before normalization: [{min_lum}, {max_lum}]")
                if max_lum > min_lum:
                    luminance[covered] = (luminance[covered] - min_lum) / (max_lum - min_lum)

        normal = self._render_pass_pixels("Normal")
        position = self._render_pass_pixels("Position")
        light_np = np.array(light, dtype=np.float32)
        height, width = normal.shape[:2]

        # Calculate direction to light (vectorized)
        if is_directional_light:
            # For directional light, the direction is the same for all pixels
            to_light = np.broadcast_to(light_np, (height, width, 3))
        else:
            to_light = light_np - position
            to_light = to_light / np.linalg.norm(to_light, axis=-1, keepdims=True)

        # Dot product of normal and to_light
        normal_amount = np.sum(normal * to_light, axis=-1, keepdims=True)

        # Basis (u, v) of tangent plane
        v = to_light - normal * normal_amount
        v = v / np.linalg.norm(v, axis=-1, keepdims=True)
        u = np.cross(normal, v)

        cos_offset = math.cos(orientation_offset)
        sin_offset = math.sin(orientation_offset)
        direction_world = u * cos_offset + v * sin_offset

        # Project points slightly offset along world_direction to normalized device coordinates
        pos_p = position + direction_world * self.finite_difference_offset
        pos_m = position - direction_world * self.finite_difference_offset

        # Apply view-projection matrix to homogeneous coordinates
        ones = np.ones((height, width, 1))
        pos_p_h = np.concatenate([pos_p, ones], axis=-1)
        pos_m_h = np.concatenate([pos_m, ones], axis=-1)
        vp_matrix_t = np.array(view_projection_matrix, dtype=np.float32).T

        # Matrix multiplication with einsum
        pp_clip = np.einsum("ijk,kl->ijl", pos_p_h, vp_matrix_t)
        pm_clip = np.einsum("ijk,kl->ijl", pos_m_h, vp_matrix_t)

        pp_ndc = pp_clip[:, :, :2] / pp_clip[:, :, 3:4]
        pm_ndc = pm_clip[:, :, :2] / pm_clip[:, :, 3:4]

        # Screen-space direction
        direction_ndc = pp_ndc - pm_ndc

        # Orientation angle
        orientation = np.arctan2(direction_ndc[:, :, 1], direction_ndc[:, :, 0])[..., np.newaxis] * coverage
        orientation = np.nan_to_num(orientation, nan=0.0, posinf=0.0, neginf=0.0)

        self._restore_render_passes()
        self.target_gp_obj.hide_render = target_gp_hide_render
        return np.concatenate((coverage, luminance, z, np.cos(orientation), np.sin(orientation)), axis=-1)
