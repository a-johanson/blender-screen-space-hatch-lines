import bpy
from mathutils import Vector

from screen_space import BlenderRenderEngine, BlenderScene, GreasePencilDrawing, PixelDataGrid, ShaderRenderEngine, catmull_rom_interpolate, poisson_disk_stipples, scribbles_from_stipples, streamlines_to_stroke_positions, visvalingam_whyatt


render_resolution = 1000

scene = BlenderScene(bpy.context.scene.objects["Light"])

blender_width, blender_height = scene.render_resolution()

if blender_width >= blender_height:
    width = render_resolution
    height = int(width * blender_height / blender_width)
else:
    height = render_resolution
    width = int(height * blender_width / blender_height)

aspect_ratio = width / height
aspect_ratio_inverse = height / width
ratio_sensor_size_to_focal_length = scene.ratio_sensor_size_to_focal_length()
print(f"Image size: {width} x {height}, Aspect ratio: {aspect_ratio:.5f}")

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
print(f"Camera clip range: {camera_clip_range[0]} to {camera_clip_range[1]}")
print("Light position:", light_position)
print("Light direction:", light_direction)

gp_stroke_distance = 2.0

frame_center = camera_position + (camera_rotation @ Vector((0.0, 0.0, -gp_stroke_distance)))
frame_dir_x = camera_rotation @ Vector((1.0, 0.0, 0.0))
frame_dir_y = camera_rotation @ Vector((0.0, 1.0, 0.0))
frame_x_axis = ratio_sensor_size_to_focal_length * gp_stroke_distance * min(aspect_ratio, 1.0) * frame_dir_x
frame_y_axis = ratio_sensor_size_to_focal_length * gp_stroke_distance * min(aspect_ratio_inverse, 1.0) * frame_dir_y
frame_origin = frame_center - (0.5 - 0.5/width) * frame_x_axis - (0.5 - 0.5/height) * frame_y_axis

is_directional_light = False

# blender_render = BlenderRenderEngine()
# blender_render.initialize_compositor()
# pixels = blender_render.render_coverage_luminance_depth_direction(
#     view_projection_matrix=view_projection_matrix,
#     light=light_direction if is_directional_light else light_position,
#     is_directional_light=is_directional_light,
#     clip_luminance=True,
#     normalize_luminance=False,
#     orientation_offset=0.0,
#     camera_far_clip=camera_clip_range[1],
#     far_clip_tolerance=0.001
# )
# print("Pixels shape:", pixels.shape)
# print("Coverage range:", pixels[:, :, 0].min(), pixels[:, :, 0].max())
# print("L range:", pixels[:, :, 1].min(), pixels[:, :, 1].max())
# print("Z range:", pixels[:, :, 2].min(), pixels[:, :, 2].max())
# print("Direction cos range:", pixels[:, :, 3].min(), pixels[:, :, 3].max())
# print("Direction sin range:", pixels[:, :, 4].min(), pixels[:, :, 4].max())

shader_render = ShaderRenderEngine()
triangle_data = scene.world_triangle_data()
pixels = shader_render.render_coverage_luminance_depth_direction(
    triangle_data,
    view_projection_matrix,
    camera_clip_range,
    light_direction if is_directional_light else light_position,
    is_directional_light,
    0.0,
    width,
    height
)

print("Pixels shape:", pixels.shape)
print("Coverage range:", pixels[:, :, 0].min(), pixels[:, :, 0].max())
print("L range:", pixels[:, :, 1].min(), pixels[:, :, 1].max())
print("Z range:", pixels[:, :, 2].min(), pixels[:, :, 2].max())
print("Direction cos range:", pixels[:, :, 3].min(), pixels[:, :, 3].max())
print("Direction sin range:", pixels[:, :, 4].min(), pixels[:, :, 4].max())

grid = PixelDataGrid(pixels)

stipples = poisson_disk_stipples(
    grid,
    rng_seed=42,
    seed_box_size=10,
    r_max=15.0,
    r_min=3.0,
    gamma=3.0,
    max_stippled_luminance=1.0,
    child_count=30
)
print(f"Generated {len(stipples)} stipples")

# stroke_lengths = [1] * len(stipples)
# stroke_positions = stipples_to_stroke_positions(
#     width,
#     height,
#     frame_origin.to_tuple(),
#     frame_x_axis.to_tuple(),
#     frame_y_axis.to_tuple(),
#     stipples
# )

scribbles = []
for _ in range(2):
    scribbles.append(scribbles_from_stipples(stipples, initial_sampling_rate=65, min_remaining_point_fraction=0.025, depth_factor=10000.0))
scribbles = [catmull_rom_interpolate(sl, points_per_segment=10) for sl in scribbles]
print("Number of points in the scribble lines:", sum(len(sl) for sl in scribbles))
scribbles = [visvalingam_whyatt(sl, max_area=0.05) for sl in scribbles]
print("Number of points after simplification:", sum(len(sl) for sl in scribbles))

stroke_positions = streamlines_to_stroke_positions(
    width,
    height,
    frame_origin.to_tuple(),
    frame_x_axis.to_tuple(),
    frame_y_axis.to_tuple(),
    scribbles
)
stroke_lengths = [len(sl) for sl in scribbles]
print("Number of points in the strokes:", stroke_positions.shape[0])

gp_drawing = GreasePencilDrawing(bpy.context.scene.objects["HatchLines"], "Layer")
gp_drawing.clear()
gp_drawing.add_strokes(stroke_lengths, stroke_positions, radius=0.0005)
