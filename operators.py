import bpy
from mathutils import Vector

from .screen_space import BlenderRenderEngine, BlenderScene, ShaderRenderEngine, PixelDataGrid, GreasePencilDrawing, flow_field_streamlines, streamlines_to_strokes


class HATCH_OT_create_lines(bpy.types.Operator):
    bl_idname = "hatch.create_lines"
    bl_label = "Create Hatch Lines"
    bl_description = "Create screen-space hatch lines with Grease Pencil"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        hatch_props = context.scene.hatch_line_props
        return hatch_props.target_gp is not None and hatch_props.input_light is not None

    def execute(self, context):
        hatch_props = context.scene.hatch_line_props

        print("Creating hatch lines...")
        scene = BlenderScene(hatch_props.input_light)

        width, height = scene.render_resolution()
        aspect_ratio = width / height
        aspect_ratio_inverse = height / width
        ratio_sensor_size_to_focal_length = scene.ratio_sensor_size_to_focal_length()
        print(f"Image size: {width} x {height}, Aspect ratio: {aspect_ratio:.5f}")
        print(f"Sensor size to focal length ratio: {ratio_sensor_size_to_focal_length:.5f}")

        view_matrix = scene.camera_view_matrix()
        projection_matrix = scene.camera_projection_matrix(aspect_ratio)
        view_projection_matrix = projection_matrix @ view_matrix
        camera_rotation = scene.camera_rotation_matrix()
        camera_position = scene.camera_position()
        camera_clip_range = scene.camera_near_far_clip()
        light_position = scene.light_position()
        light_direction = scene.light_direction()
        print("View matrix:", view_matrix)
        print("Projection matrix:", projection_matrix)
        print("View-projection matrix:", view_projection_matrix)
        print("Camera rotation matrix:", camera_rotation)
        print("Camera position:", camera_position)
        print(f"Camera clip range: {camera_clip_range[0]} to {camera_clip_range[1]}")
        print("Light position:", light_position)
        print("Light direction:", light_direction)

        frame_center = camera_position + (camera_rotation @ Vector((0.0, 0.0, -1.0)))
        frame_dir_x = camera_rotation @ Vector((1.0, 0.0, 0.0))
        frame_dir_y = camera_rotation @ Vector((0.0, 1.0, 0.0))
        frame_x_axis = ratio_sensor_size_to_focal_length * min(aspect_ratio, 1.0) * frame_dir_x
        frame_y_axis = ratio_sensor_size_to_focal_length * min(aspect_ratio_inverse, 1.0) * frame_dir_y
        frame_origin = frame_center - (0.5 - 0.5/width) * frame_x_axis - (0.5 - 0.5/height) * frame_y_axis
        print("Frame center:", frame_center)
        print("Frame direction X:", frame_dir_x)
        print("Frame direction Y:", frame_dir_y)
        print("Frame X axis:", frame_x_axis)
        print("Frame Y axis:", frame_y_axis)
        print("Frame origin:", frame_origin)

        if hatch_props.render_engine == "SHADER":
            renderer = ShaderRenderEngine()
            triangle_data = scene.world_triangle_data()
            print("Vertex count:", len(triangle_data.vertices))
            print("Normal count:", len(triangle_data.normals))
            pixels = renderer.render_coverage_luminance_depth_direction(
                triangle_data,
                view_projection_matrix,
                camera_clip_range,
                light_direction if hatch_props.is_directional_light else light_position,
                hatch_props.is_directional_light,
                hatch_props.orientation_offset,
                width,
                height
            )
        else:
            renderer = BlenderRenderEngine(hatch_props.target_gp)
            renderer.initialize_compositor()
            pixels = renderer.render_coverage_luminance_depth_direction(
                view_projection_matrix,
                light_direction if hatch_props.is_directional_light else light_position,
                hatch_props.is_directional_light,
                clip_luminance = hatch_props.clip_luminance,
                normalize_luminance = hatch_props.normalize_luminance,
                orientation_offset = 0.0,
                camera_far_clip = camera_clip_range[1]
            )

        print("Luminance range:", pixels[:, :, 1].min(), pixels[:, :, 1].max())
        print("Z range:", pixels[:, :, 2].min(), pixels[:, :, 2].max())

        grid = PixelDataGrid(pixels)

        streamlines = flow_field_streamlines(
            grid,
            rng_seed=hatch_props.rng_seed,
            seed_box_size=hatch_props.seed_box_size_factor * hatch_props.d_sep,
            d_sep_max=hatch_props.d_sep,
            d_sep_shadow_factor=hatch_props.d_sep_shadow_factor,
            shadow_gamma=hatch_props.shadow_gamma,
            d_test_factor=hatch_props.d_test_factor,
            d_step=hatch_props.d_step,
            max_depth_step=hatch_props.max_depth_step,
            max_accum_angle=hatch_props.max_accum_angle,
            max_steps=hatch_props.max_steps,
            min_steps=hatch_props.min_steps
        )

        strokes = streamlines_to_strokes(
            width,
            height,
            frame_origin.to_tuple(),
            frame_x_axis.to_tuple(),
            frame_y_axis.to_tuple(),
            streamlines
        )
        print("Number of strokes to generate:", len(strokes))

        gp_drawing = GreasePencilDrawing(hatch_props.target_gp, hatch_props.target_gp_layer)
        gp_drawing.clear()
        gp_drawing.add_strokes(strokes, radius=hatch_props.gp_stroke_radius)

        self.report({"INFO"}, "Hatch lines created successfully")
        return {"FINISHED"}


classes = (
    HATCH_OT_create_lines,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
