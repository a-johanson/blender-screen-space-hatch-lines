from dataclasses import dataclass
from collections.abc import Sequence
from typing import Any

import bpy
from mathutils import Matrix, Vector


@dataclass
class MeshTriangles:
    vertices: Sequence[Vector]
    normals: Sequence[Vector]
    indices: Sequence[Sequence[int]] | None # One index sequence per triangle; if None, each triplet of vertices forms a triangle.

class BlenderScene:
    def __init__(self, light_obj: bpy.types.Object):
        self.camera = bpy.context.scene.camera
        assert self.camera is not None, "No active camera found in the scene"
        self.light = light_obj
        assert self.light.type in ["EMPTY", "LIGHT"], "Light object is not an empty or a light"

    def render_resolution(self) -> tuple[int, int]:
        render = bpy.context.scene.render
        return render.resolution_x, render.resolution_y

    def set_render_resolution(self, width: int, height: int):
        render = bpy.context.scene.render
        render.resolution_x = width
        render.resolution_y = height

    def ratio_sensor_size_to_focal_length(self) -> float:
        camera_data = self.camera.data
        focal_length = camera_data.lens
        sensor_size = camera_data.sensor_width
        return sensor_size / focal_length

    def camera_view_matrix(self) -> (Any | Matrix):
        return self.camera.matrix_world.inverted()

    def camera_projection_matrix(self, aspect_ratio: float) -> Matrix:
        return self.camera.calc_matrix_camera(depsgraph=bpy.context.evaluated_depsgraph_get(), scale_x=aspect_ratio)

    def camera_rotation_matrix(self) -> Matrix:
        return self.camera.matrix_world.to_3x3()

    def camera_position(self) -> Vector:
        return self.camera.matrix_world.to_translation()

    def camera_near_far_clip(self) -> tuple[float, float]:
        camera_data = self.camera.data
        return camera_data.clip_start, camera_data.clip_end

    def light_position(self) -> Vector:
        return self.light.matrix_world.to_translation()

    def light_direction(self) -> Vector:
        direction = self.light.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
        return direction.normalized()

    def world_triangle_data(self) -> MeshTriangles:
        all_vertices = []
        all_normals = []

        depsgraph = bpy.context.evaluated_depsgraph_get()

        for inst in depsgraph.object_instances:
            obj = inst.object
            if obj.type != "MESH" or not inst.show_self:
                continue

            mesh = obj.data
            model_matrix = inst.matrix_world
            normal_matrix = model_matrix.inverted().transposed().to_3x3()

            world_vertices = [(model_matrix @ vertex.co.to_4d()).to_3d() for vertex in mesh.vertices]
            world_vertex_normals = [(normal_matrix @ vertex.normal).normalized() for vertex in mesh.vertices]

            for face in mesh.polygons:
                face_loops = [mesh.loops[loop_index] for loop_index in face.loop_indices]
                face_vertices = [world_vertices[loop.vertex_index] for loop in face_loops]
                if face.use_smooth:
                    face_normals = [world_vertex_normals[loop.vertex_index] for loop in face_loops]
                else:
                    face_normals = [(normal_matrix @ loop.normal).normalized() for loop in face_loops]
                if len(face_vertices) == 3:
                    all_vertices.extend(face_vertices)
                    all_normals.extend(face_normals)
                elif len(face_vertices) == 4: # Triangulate quads on the fly
                    all_vertices.extend(face_vertices[:3])
                    all_normals.extend(face_normals[:3])
                    all_vertices.extend([face_vertices[0], face_vertices[2], face_vertices[3]])
                    all_normals.extend([face_normals[0], face_normals[2], face_normals[3]])
                else:
                    raise ValueError("Only triangles and quads are supported")

        return MeshTriangles(all_vertices, all_normals, None)
