from collections import deque
import math
import random
import numpy as np

from .grid import PixelDataGrid
from .point_registry import PointRegistry


def d_sep_from_luminance(d_sep_max: float, d_sep_shadow_factor: float, gamma_luminance: float, luminance: float) -> float:
    d_sep_min = d_sep_max * d_sep_shadow_factor
    return d_sep_min + (d_sep_max - d_sep_min) * math.pow(luminance, gamma_luminance)

def flow_field_streamline(
    grid: PixelDataGrid,
    point_registry: PointRegistry,
    start_from_streamline_id: int,
    p_start: tuple[float, float],
    d_sep_max: float,
    d_sep_shadow_factor: float,
    gamma_luminance: float,
    d_test_factor: float,
    d_step: float,
    max_depth_step: float,
    max_accum_angle: float,
    max_hatched_luminance: float,
    max_steps: int,
    min_steps: int,
) -> list[tuple[float, float]] | None:
    gv_start = grid.grid_value(p_start[0], p_start[1])
    if gv_start is None or not gv_start.is_covered() or gv_start.luminance > max_hatched_luminance:
        return None

    d_sep_start = d_sep_from_luminance(d_sep_max, d_sep_shadow_factor, gamma_luminance, gv_start.luminance)
    if not point_registry.is_point_allowed(
        p_start, d_sep_start, d_test_factor * d_sep_start, start_from_streamline_id
    ):
        return None

    def continue_line(
        lp0: tuple[float, float],
        direction0: tuple[float, float],
        depth0: float,
        step: float,
        accum_limit: float,
        step_count: int
    ) -> list[tuple[float, float]]:
        line: list[tuple[float, float]] = []
        lp_last = lp0
        next_dir = direction0
        last_depth = depth0
        accum_angle = 0.0

        for _ in range(step_count):
            p_new = (
                lp_last[0] + next_dir[0] * step,
                lp_last[1] + next_dir[1] * step
            )
            gv = grid.grid_value(p_new[0], p_new[1])
            new_dir = gv.direction
            dot = max(-1.0, min(1.0, next_dir[0]*new_dir[0] + next_dir[1]*new_dir[1]))
            accum_angle += math.acos(dot)
            d_sep = d_sep_from_luminance(d_sep_max, d_sep_shadow_factor, gamma_luminance, gv.luminance)
            d_sep_l = d_test_factor * d_sep
            if (not gv.is_covered() or
                accum_angle > accum_limit or
                abs(gv.depth - last_depth) > max_depth_step or
                gv.luminance > max_hatched_luminance or
                not point_registry.is_point_allowed(p_new, d_sep_l, d_sep_l, 0)):
                break

            line.append(p_new)
            lp_last = p_new
            next_dir = gv.direction
            last_depth = gv.depth
        return line

    gv_start = grid.grid_value(p_start[0], p_start[1])

    # forward and backward
    fwd = continue_line(p_start, gv_start.direction, gv_start.depth,
                        d_step, 0.5 * max_accum_angle, max_steps // 2)
    bwd = continue_line(p_start, gv_start.direction, gv_start.depth,
                        -d_step, 0.5 * max_accum_angle, max_steps // 2)
    # combine
    line = list(reversed(bwd)) + [p_start] + fwd
    return line if len(line) > (min_steps + 1) else None

def flow_field_streamlines(
    grid: PixelDataGrid,
    rng_seed: int,
    seed_box_size: int,
    d_sep_max: float,
    d_sep_shadow_factor: float,
    gamma_luminance: float,
    d_test_factor: float,
    d_step: float,
    max_depth_step: float,
    max_accum_angle: float,
    max_hatched_luminance: float,
    max_steps: int,
    min_steps: int
) -> list[list[tuple[float, float]]]:
    width = grid.width
    height = grid.height
    registry = PointRegistry(width, height, d_sep_max)
    queue: deque = deque()
    streamlines: list[list[tuple[float, float]]] = []

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
            sl = flow_field_streamline(
                grid,
                registry,
                start_from_streamline_id=0,
                p_start=(sx,sy),
                d_sep_max=d_sep_max,
                d_sep_shadow_factor=d_sep_shadow_factor,
                gamma_luminance=gamma_luminance,
                d_test_factor=d_test_factor,
                d_step=d_step,
                max_depth_step=max_depth_step,
                max_accum_angle=max_accum_angle,
                max_hatched_luminance=max_hatched_luminance,
                max_steps=max_steps,
                min_steps=min_steps
            )
            if sl is not None:
                sid = registry.add_points(sl)
                queue.append((sid, sl))
                streamlines.append(sl)

    # Grow from queue
    while queue:
        sid, sl = queue.popleft()
        for lp in sl:
            gv = grid.grid_value(lp[0], lp[1])
            d_sep = d_sep_from_luminance(d_sep_max, d_sep_shadow_factor, gamma_luminance, gv.luminance)
            for sign in (-1.0, 1.0):
                dir = gv.direction
                new_seed = (
                    lp[0] - dir[1] * sign * d_sep,
                    lp[1] + dir[0] * sign * d_sep
                )
                new_sl = flow_field_streamline(
                    grid,
                    registry,
                    start_from_streamline_id=sid,
                    p_start=new_seed,
                    d_sep_max=d_sep_max,
                    d_sep_shadow_factor=d_sep_shadow_factor,
                    gamma_luminance=gamma_luminance,
                    d_test_factor=d_test_factor,
                    d_step=d_step,
                    max_depth_step=max_depth_step,
                    max_accum_angle=max_accum_angle,
                    max_hatched_luminance=max_hatched_luminance,
                    max_steps=max_steps,
                    min_steps=min_steps
                )
                if new_sl:
                    new_sid = registry.add_points(new_sl)
                    queue.append((new_sid, new_sl))
                    streamlines.append(new_sl)

    return streamlines

def streamlines_to_stroke_positions(
    width: int,
    height: int,
    drawing_origin: tuple[float, float, float],
    drawing_x_axis: tuple[float, float, float],
    drawing_y_axis: tuple[float, float, float],
    streamlines: list[list[tuple[float, float]]]
) -> np.ndarray:
    width_inv = 1.0 / width
    height_inv = 1.0 / height

    return np.array([(
            drawing_origin[0] + (x_coord := (p[0]*width_inv)) * drawing_x_axis[0] + (y_coord := (p[1]*height_inv)) * drawing_y_axis[0],
            drawing_origin[1] + x_coord * drawing_x_axis[1] + y_coord * drawing_y_axis[1],
            drawing_origin[2] + x_coord * drawing_x_axis[2] + y_coord * drawing_y_axis[2]
        ) for sl in streamlines for p in sl], dtype=np.float32)
