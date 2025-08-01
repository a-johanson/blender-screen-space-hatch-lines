import bpy
from mathutils import Vector

from .screen_space import BlenderRenderEngine, BlenderScene, ShaderRenderEngine, PixelDataGrid, GreasePencilDrawing, catmull_rom_interpolate, flow_field_streamlines, poisson_disk_stipples, scribbles_from_stipples, stipples_to_stroke_positions, streamlines_to_stroke_positions, visvalingam_whyatt


class HATCH_OT_generate(bpy.types.Operator):
    bl_idname = "hatch.generate"
    bl_label = "Generate artistic shading"
    bl_description = "Create screen-space shading effects with Grease Pencil"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        hatch_props = context.scene.hatch_line_props
        return hatch_props.target_gp is not None and hatch_props.input_light is not None

    def execute(self, context):
        hatch_props = context.scene.hatch_line_props

        print("Generating screen-space shading effect...")
        scene = BlenderScene(hatch_props.input_light)

        blender_width, blender_height = scene.render_resolution()
        print(f"Blender render resolution: {blender_width} x {blender_height} px")

        if blender_width >= blender_height:
            width = hatch_props.render_resolution
            height = int(width * blender_height / blender_width)
        else:
            height = hatch_props.render_resolution
            width = int(height * blender_width / blender_height)
        print(f"Render resolution for effect: {width} x {height} px")

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

        frame_center = camera_position + (camera_rotation @ Vector((0.0, 0.0, -hatch_props.gp_stroke_distance)))
        frame_dir_x = camera_rotation @ Vector((1.0, 0.0, 0.0))
        frame_dir_y = camera_rotation @ Vector((0.0, 1.0, 0.0))
        frame_x_axis = ratio_sensor_size_to_focal_length * hatch_props.gp_stroke_distance * min(aspect_ratio, 1.0) * frame_dir_x
        frame_y_axis = ratio_sensor_size_to_focal_length * hatch_props.gp_stroke_distance * min(aspect_ratio_inverse, 1.0) * frame_dir_y
        frame_origin = frame_center - (0.5 - 0.5/width) * frame_x_axis - (0.5 - 0.5/height) * frame_y_axis
        print("Frame center:", frame_center)
        print("Frame direction X:", frame_dir_x)
        print("Frame direction Y:", frame_dir_y)
        print("Frame X axis:", frame_x_axis)
        print("Frame Y axis:", frame_y_axis)
        print("Frame origin:", frame_origin)

        def render_pixel_grid(orientation_offset) -> PixelDataGrid:
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
                    orientation_offset,
                    width,
                    height
                )
            else:
                scene.set_render_resolution(width, height)
                renderer = BlenderRenderEngine(hatch_props.target_gp)
                renderer.initialize_compositor()
                pixels = renderer.render_coverage_luminance_depth_direction(
                    view_projection_matrix,
                    light_direction if hatch_props.is_directional_light else light_position,
                    hatch_props.is_directional_light,
                    clip_luminance = hatch_props.clip_luminance,
                    normalize_luminance = hatch_props.normalize_luminance,
                    orientation_offset = orientation_offset,
                    camera_far_clip = camera_clip_range[1]
                )
                scene.set_render_resolution(blender_width, blender_height)

            print("Luminance range:", pixels[:, :, 1].min(), pixels[:, :, 1].max())
            print("Z range:", pixels[:, :, 2].min(), pixels[:, :, 2].max())

            return PixelDataGrid(pixels)


        if hatch_props.technique == "HATCHING":
            print("Using hatch lines...")
            hatching_settings = [(hatch_props.orientation_offset, hatch_props.max_hatched_luminance)]
            if hatch_props.crosshatching_enabled:
                hatching_settings.append((
                    hatch_props.orientation_offset + hatch_props.crossing_orientation_offset,
                    hatch_props.max_crosshatched_luminance
                ))

            streamlines = []

            for orientation_offset, max_hatched_luminance in hatching_settings:
                print(f"Hatching pass for orientation offset: {orientation_offset:.5f} rad")
                grid = render_pixel_grid(orientation_offset)

                streamlines.extend(
                        flow_field_streamlines(
                        grid,
                        rng_seed=hatch_props.rng_seed,
                        seed_box_size=hatch_props.seed_box_size_factor * hatch_props.d_sep,
                        d_sep_max=hatch_props.d_sep,
                        d_sep_shadow_factor=hatch_props.d_sep_shadow_factor,
                        gamma_luminance=hatch_props.gamma_hatching,
                        d_test_factor=hatch_props.d_test_factor,
                        d_step=hatch_props.d_step,
                        max_depth_step=hatch_props.max_depth_step,
                        max_accum_angle=hatch_props.max_accum_angle,
                        max_hatched_luminance=max_hatched_luminance,
                        max_steps=hatch_props.max_steps,
                        min_steps=hatch_props.min_steps
                    )
                )

            print("Number of streamlines generated:", len(streamlines))
            print("Number of points in the streamlines:", sum(len(sl) for sl in streamlines))
            streamlines = [visvalingam_whyatt(sl, max_area=hatch_props.line_simplification_error_hatching) for sl in streamlines]
            stroke_lengths = [len(sl) for sl in streamlines]
            print("Number of points in the streamlines after simplification:", sum(stroke_lengths))
            stroke_positions = streamlines_to_stroke_positions(
                width,
                height,
                frame_origin.to_tuple(),
                frame_x_axis.to_tuple(),
                frame_y_axis.to_tuple(),
                streamlines
            )
        elif hatch_props.technique == "STIPPLING":
            print("Using stippling and scribbling...")
            grid = render_pixel_grid(hatch_props.orientation_offset)

            stipples = poisson_disk_stipples(
                grid,
                rng_seed=hatch_props.rng_seed,
                seed_box_size=hatch_props.seed_box_size_factor * hatch_props.max_radius,
                r_max=hatch_props.max_radius,
                r_min=hatch_props.min_radius,
                gamma=hatch_props.gamma_stippling,
                max_stippled_luminance=hatch_props.max_stippled_luminance,
                child_count=hatch_props.child_count
            )
            print(f"Generated {len(stipples)} stipples")

            if not hatch_props.scribbling_enabled:
                stroke_lengths = [2 if hatch_props.stroke_length > 0.0 else 1] * len(stipples)
                stroke_positions = stipples_to_stroke_positions(
                    width,
                    height,
                    frame_origin.to_tuple(),
                    frame_x_axis.to_tuple(),
                    frame_y_axis.to_tuple(),
                    stipples,
                    hatch_props.stroke_length
                )
            else:
                scribbles = []
                for _ in range(hatch_props.scribbling_iterations):
                    scribbles.append(scribbles_from_stipples(
                            stipples,
                            initial_sampling_rate=hatch_props.initial_sub_sampling_rate,
                            min_remaining_point_fraction=hatch_props.min_remaining_point_share,
                            depth_factor=hatch_props.depth_factor,
                            stipple_stroke_length=hatch_props.stroke_length
                        ))
                scribbles = [catmull_rom_interpolate(sl, points_per_segment=hatch_props.bezier_points_per_segment) for sl in scribbles if len(sl) >= 4]
                print("Number of points in the scribble lines:", sum(len(sl) for sl in scribbles))
                scribbles = [visvalingam_whyatt(sl, max_area=hatch_props.line_simplification_error_scribbling) for sl in scribbles]
                print("Number of points after simplification:", sum(len(sl) for sl in scribbles))

                stroke_lengths = [len(sl) for sl in scribbles]
                stroke_positions = streamlines_to_stroke_positions(
                    width,
                    height,
                    frame_origin.to_tuple(),
                    frame_x_axis.to_tuple(),
                    frame_y_axis.to_tuple(),
                    scribbles
                )

        print("Number of points in the strokes:", stroke_positions.shape[0])
        gp_drawing = GreasePencilDrawing(hatch_props.target_gp, hatch_props.target_gp_layer)
        if hatch_props.clear_layer:
            gp_drawing.clear()
        gp_drawing.add_strokes(stroke_lengths, stroke_positions, hatch_props.gp_stroke_radius)

        self.report({"INFO"}, "Screen-space effect generated successfully")
        return {"FINISHED"}


classes = (
    HATCH_OT_generate,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
