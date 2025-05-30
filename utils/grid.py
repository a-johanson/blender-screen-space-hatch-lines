from collections.abc import Sequence
from dataclasses import dataclass
import math


@dataclass
class GridValue:
    coverage_value: float # in [0, 1], where 1 means fully covered
    depth: float
    direction: tuple[float, float]  # (cos, sin) of the orientation angle
    value: float

    def is_covered(self) -> bool:
        return self.coverage_value > 0.9

class DepthDirectionValueGrid:
    def __init__(self, width: int, height: int, pixels_depth_orientation_value: Sequence[tuple[float, float, float]]):
        assert len(pixels_depth_orientation_value) == width * height, "The number of pixels must match the width and height dimensions"
        self.width = width
        self.height = height
        self.pixels_coverage_depth_direction_value = [
            (coverage := (1.0 if t[0] > 0.0 else 0.0), 
            coverage * t[0],
            coverage * math.cos(t[1]), 
            coverage * math.sin(t[1]), 
            coverage * t[2])
            for t in pixels_depth_orientation_value
        ]

    def grid_value(self, x: int, y: int) -> GridValue:
        x = max(x, 0.0)
        y = max(y, 0.0)
        EPS = 1.0e-5
        x = min(x, float(self.width - 1) - EPS)
        y = min(y, float(self.height - 1) - EPS)

        x_frac, x_int = math.modf(x)
        y_frac, y_int = math.modf(y)
        x_frac_ai = 1.0 - x_frac
        y_frac_ai = 1.0 - y_frac

        idx_00 = int(y_int) * self.width + int(x_int)
        idx_01 = idx_00 + 1
        idx_10 = idx_00 + self.width
        idx_11 = idx_10 + 1

        w_00 = y_frac_ai * x_frac_ai
        w_01 = y_frac_ai * x_frac
        w_10 = y_frac * x_frac_ai
        w_11 = y_frac * x_frac

        v_00 = self.pixels_coverage_depth_direction_value[idx_00]
        v_01 = self.pixels_coverage_depth_direction_value[idx_01]
        v_10 = self.pixels_coverage_depth_direction_value[idx_10]
        v_11 = self.pixels_coverage_depth_direction_value[idx_11]

        coverage = w_00 * v_00[0] + w_01 * v_01[0] + w_10 * v_10[0] + w_11 * v_11[0]
        if coverage < EPS:
            return GridValue(0.0, 0.0, (1.0, 0.0), 0.0)
        coverage_inv = 1.0 / coverage
        depth = (w_00 * v_00[1] + w_01 * v_01[1] + w_10 * v_10[1] + w_11 * v_11[1]) * coverage_inv
        direction_cos = (w_00 * v_00[2] + w_01 * v_01[2] + w_10 * v_10[2] + w_11 * v_11[2])
        direction_sin = (w_00 * v_00[3] + w_01 * v_01[3] + w_10 * v_10[3] + w_11 * v_11[3])
        direction_mag = math.sqrt(direction_cos * direction_cos + direction_sin * direction_sin)
        direction = (direction_cos / direction_mag, direction_sin / direction_mag) if direction_mag > EPS else (1.0, 0.0)
        value = (w_00 * v_00[4] + w_01 * v_01[4] + w_10 * v_10[4] + w_11 * v_11[4]) * coverage_inv
        return GridValue(coverage, depth, direction, value)
