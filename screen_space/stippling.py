from dataclasses import dataclass
from collections import deque
import math
import random
import numpy as np

from .grid import PixelDataGrid
from .point_registry import PointRegistry


@dataclass
class Stipple:
    x: float
    y: float
    depth: float
    direction: tuple[float, float]  # (cos, sin) of the orientation angle

def radius_from_luminance(luminance: float, r_min: float, r_max: float, gamma: float) -> float:
    return r_min + (r_max - r_min) * pow(luminance, 0.5 * gamma)

def poisson_disk_stipples(
        grid: PixelDataGrid,
        rng_seed: int,
        seed_box_size: int,
        r_max: float,
        r_min: float,
        gamma: float,
        max_stippled_luminance: float = 1.0,
        child_count: int = 100
    ) -> list[Stipple]:
    width = grid.width
    height = grid.height
    registry = PointRegistry(width, height, r_max)
    queue: deque = deque()
    stipples: list[Stipple] = []

    random.seed(rng_seed)

    # Seed points on a jittered grid
    cell_count_x = int(width / seed_box_size)
    cell_count_y = int(height / seed_box_size)
    cell_width = float(width) / float(cell_count_x)
    cell_height = float(height) / float(cell_count_y)
    for iy in range(cell_count_y):
        for ix in range(cell_count_x):
            sx = cell_width * (ix + random.random())
            sy = cell_height * (iy + random.random())
            p = (sx, sy)

            gv = grid.grid_value(sx, sy)
            r = radius_from_luminance(gv.luminance, r_min, r_max, gamma)
            if (gv.is_covered() and 
                gv.luminance <= max_stippled_luminance and
                registry.is_point_allowed(p, r, r, 0)):
                pid = registry.add_point(p)
                queue.append((pid, r, p))
                stipples.append(Stipple(p[0], p[1], gv.depth, gv.direction))


    # Grow from queue
    while queue:
        id_center, r_center, center = queue.popleft()
        for _ in range(child_count):
            angle = 2.0 * math.pi * random.random()
            d = r_center * (1.0 + random.random())
            p_candidate = (
                center[0] + d * math.cos(angle),
                center[1] + d * math.sin(angle)
            )
            gv = grid.grid_value(p_candidate[0], p_candidate[1])
            r_candidate = radius_from_luminance(gv.luminance, r_min, r_max, gamma)
            if (gv.is_covered() and 
                gv.luminance <= max_stippled_luminance and
                registry.is_point_allowed(p_candidate, r_candidate, 0.0, id_center)):
                pid = registry.add_point(p_candidate)
                queue.append((pid, r_candidate, p_candidate))
                stipples.append(Stipple(p_candidate[0], p_candidate[1], gv.depth, gv.direction))

    return stipples

def stipples_to_stroke_positions(
    width: int,
    height: int,
    drawing_origin: tuple[float, float, float],
    drawing_x_axis: tuple[float, float, float],
    drawing_y_axis: tuple[float, float, float],
    stipples: list[Stipple],
    stroke_length: float = 0.0
) -> np.ndarray:
    width_inv = 1.0 / width
    height_inv = 1.0 / height

    def project_point(x: float, y: float) -> tuple[float, float, float]:
        x_coord = x * width_inv
        y_coord = y * height_inv
        return (
            drawing_origin[0] + x_coord * drawing_x_axis[0] + y_coord * drawing_y_axis[0],
            drawing_origin[1] + x_coord * drawing_x_axis[1] + y_coord * drawing_y_axis[1],
            drawing_origin[2] + x_coord * drawing_x_axis[2] + y_coord * drawing_y_axis[2]
        )

    positions = []
    for s in stipples:
        if stroke_length > 0.0:
            dx = 0.5 * stroke_length * s.direction[0]
            dy = 0.5 * stroke_length * s.direction[1]
            positions.append(project_point(s.x - dx, s.y - dy))
            positions.append(project_point(s.x + dx, s.y + dy))
        else:
            positions.append(project_point(s.x, s.y))

    return np.array(positions, dtype=np.float32)
