import bpy
import numpy as np
from collections.abc import Sequence


class GreasePencilDrawing:
    def __init__(self, gp_obj: bpy.types.Object, layer_name: str):
        if not gp_obj or gp_obj.type != "GREASEPENCIL":
            raise ValueError(f"Object is not a Grease Pencil v3 object.")

        gp_data = gp_obj.data

        layer = gp_data.layers.get(layer_name)
        if layer is None:
            raise KeyError(f"Grease Pencil Layer '{layer_name}' not found.")

        frame = layer.current_frame()
        if frame is None:
            current_frame_number = bpy.context.scene.frame_current
            frame = layer.frames.new(current_frame_number)
        self.drawing = frame.drawing

    def clear(self):
        self.drawing.remove_strokes()

    def add_strokes(self, stroke_lengths: list[int], stroke_positions: np.ndarray, radius: float):
        if len(stroke_lengths) == 0:
            return

        assert sum(stroke_lengths) == stroke_positions.shape[0], f"Sum of stroke lengths {sum(stroke_lengths)} does not match the number of positions provided {stroke_positions.shape[0]}."

        gp_attributes = self.drawing.attributes
        gp_pos_attr = gp_attributes.get("position")
        if gp_pos_attr is None:
            raise KeyError(f"Grease Pencil position attribute not found.")

        existing_point_count = len(gp_pos_attr.data)
        print(f"Existing point count in Grease Pencil: {existing_point_count}")
        total_point_count = existing_point_count + stroke_positions.shape[0]

        self.drawing.add_strokes(stroke_lengths)

        gp_rad_attr = gp_attributes.get("radius")
        if gp_rad_attr is None:
            gp_rad_attr = gp_attributes.new("radius", "FLOAT", "POINT")

        gp_pos_attr = gp_attributes.get("position")
        if gp_pos_attr is None:
            raise KeyError(f"Grease Pencil position attribute not found.")

        pos_data = np.zeros(total_point_count * 3, dtype=np.float32)
        rad_data = np.zeros(total_point_count, dtype=np.float32)

        gp_pos_attr.data.foreach_get("vector", pos_data)
        gp_rad_attr.data.foreach_get("value", rad_data)

        pos_data[existing_point_count*3:] = stroke_positions.ravel()
        rad_data[existing_point_count:] = radius

        gp_pos_attr.data.foreach_set("vector", pos_data)
        gp_rad_attr.data.foreach_set("value", rad_data)
