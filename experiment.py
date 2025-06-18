import bpy
from screen_space import BlenderRenderEngine, BlenderScene, ShaderRenderEngine

blender_render = BlenderRenderEngine()
blender_render.initialize_compositor()

scene = BlenderScene(bpy.context.scene.objects["Light"])

width, height = scene.render_resolution()
aspect_ratio = width / height
print(f"Image size: {width} x {height}, Aspect ratio: {aspect_ratio:.5f}")

view_matrix = scene.camera_view_matrix()
projection_matrix = scene.camera_projection_matrix(aspect_ratio)
view_projection_matrix = projection_matrix @ view_matrix
camera_clip_range = scene.camera_near_far_clip()
light_position = scene.light_position()
light_direction = scene.light_direction()
print("View matrix:", view_matrix)
print("Projection matrix:", projection_matrix)
print("View-projection matrix:", view_projection_matrix)
print(f"Camera clip range: {camera_clip_range[0]} to {camera_clip_range[1]}")
print("Light position:", light_position)
print("Light direction:", light_direction)

is_directional_light = False

pixels = blender_render.render_coverage_luminance_depth_direction(
    view_projection_matrix=view_projection_matrix,
    light=light_direction if is_directional_light else light_position,
    is_directional_light=is_directional_light,
    clip_luminance=True,
    normalize_luminance=False,
    orientation_offset=0.0,
    camera_far_clip=camera_clip_range[1],
    far_clip_tolerance=0.001
)
print("Pixels shape:", pixels.shape)
print("Coverage range:", pixels[:, :, 0].min(), pixels[:, :, 0].max())
print("L range:", pixels[:, :, 1].min(), pixels[:, :, 1].max())
print("Z range:", pixels[:, :, 2].min(), pixels[:, :, 2].max())
print("Direction cos range:", pixels[:, :, 3].min(), pixels[:, :, 3].max())
print("Direction sin range:", pixels[:, :, 4].min(), pixels[:, :, 4].max())

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
