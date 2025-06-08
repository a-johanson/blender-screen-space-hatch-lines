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

    def add_strokes(self, strokes: Sequence[np.ndarray], radius: float):
        if len(strokes) == 0:
            return

        self.drawing.add_strokes([s.shape[0] for s in strokes])

        gp_attributes = self.drawing.attributes

        gp_rad_attr = gp_attributes.get("radius")
        if gp_rad_attr is None:
            gp_rad_attr = gp_attributes.new("radius", "FLOAT", "POINT")

        gp_pos_attr = gp_attributes.get("position")
        if gp_pos_attr is None:
            raise KeyError(f"Grease Pencil position attribute not found.")

        stroke_data = np.vstack(strokes).flatten()
        radius_data = np.full(stroke_data.shape[0] // 3, radius, dtype=np.float32)

        gp_pos_attr.data.foreach_set("vector", stroke_data)
        gp_rad_attr.data.foreach_set("value", radius_data)
