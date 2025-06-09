from collections.abc import Sequence
from dataclasses import dataclass
import math

import numpy as np


@dataclass
class GridValue:
    coverage: float # in [0, 1], where 1 means fully covered
    luminance: float
    depth: float
    direction: tuple[float, float]  # (cos, sin) of the orientation angle

    def is_covered(self) -> bool:
        return self.coverage > 0.9

class PixelDataGrid:
    def __init__(self, pixels: np.ndarray):
        assert pixels.ndim == 3 and pixels.shape[2] == 5, "pixels must have shape (height, width, 5) for coverage, luminance, depth, cos(orientation), sin(orientation)"
        self.width = pixels.shape[1]
        self.height = pixels.shape[0]
        self.pixels = pixels.reshape(-1, 5)

    def grid_value(self, x: int, y: int) -> GridValue:
        x = max(x, 0.0)
        y = max(y, 0.0)
        EPS = 1.0e-5
        x = min(x, float(self.width - 1) - EPS)
        y = min(y, float(self.height - 1) - EPS)

        x_int = int(x)
        y_int = int(y)
        x_frac = x - x_int
        y_frac = y - y_int

        # Indices of the four corners
        idx_00 = y_int * self.width + x_int
        idx_01 = idx_00 + 1
        idx_10 = idx_00 + self.width
        idx_11 = idx_10 + 1

        # Bilinear weights
        weights = np.array([
            (1.0 - y_frac) * (1.0 - x_frac),  # w_00
            (1.0 - y_frac) * x_frac,          # w_01
            y_frac * (1.0 - x_frac),          # w_10
            y_frac * x_frac                   # w_11
        ])[:, np.newaxis]

        values = self.pixels[[idx_00, idx_01, idx_10, idx_11]]

        result = np.sum(values * weights, axis=0)

        coverage = result[0]
        if coverage < EPS:
            return GridValue(0.0, 0.0, 0.0, (1.0, 0.0))

        inverse_coverage = 1.0 / coverage
        luminance = result[1] * inverse_coverage
        depth = result[2] * inverse_coverage

        direction_cos, direction_sin = result[3], result[4]
        direction_mag = np.sqrt(direction_cos*direction_cos + direction_sin*direction_sin)

        if direction_mag > EPS:
            inverse_direction_mag = 1.0 / direction_mag
            direction = (direction_cos * inverse_direction_mag, direction_sin * inverse_direction_mag)
        else:
            direction = (1.0, 0.0)

        return GridValue(coverage, luminance, depth, direction)
