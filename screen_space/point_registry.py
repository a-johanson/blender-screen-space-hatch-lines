from dataclasses import dataclass
import math


@dataclass
class PointRegistryEntry:
    point: tuple[float, float]
    entity_id: int

class PointRegistry:
    def __init__(self, width: int, height: int, cell_size: float):
        self.width = float(width)
        self.height = float(height)
        self.cell_size = cell_size
        self.cells_x = math.ceil(self.width / cell_size)
        self.cells_y = math.ceil(self.height / cell_size)
        self.next_entity_id = 1
        self.cell_content: list[list[PointRegistryEntry]] = [[] for _ in range(self.cells_x * self.cells_y)]

    def _cell_coordinates(self, p: tuple[float, float]) -> tuple[int, int]:
        cx = max(min(int(p[0] / self.cell_size), self.cells_x - 1), 0)
        cy = max(min(int(p[1] / self.cell_size), self.cells_y - 1), 0)
        return (cx, cy)

    def _cell_index(self, p: tuple[float, float]) -> int:
        ix, iy = self._cell_coordinates(p)
        return iy * self.cells_x + ix

    def _cell(self, ix: int, iy: int) -> list[PointRegistryEntry]:
        idx = iy * self.cells_x + ix
        return self.cell_content[idx]

    def add_point(self, p: tuple[float, float]) -> int:
        sid = self.next_entity_id
        self.next_entity_id += 1
        idx = self._cell_index(p)
        self.cell_content[idx].append(PointRegistryEntry(p, sid))
        return sid

    def add_points(self, streamline: list[tuple[float, float]]) -> int:
        sid = self.next_entity_id
        self.next_entity_id += 1
        for p in streamline:
            idx = self._cell_index(p)
            self.cell_content[idx].append(PointRegistryEntry(p, sid))
        return sid

    def is_point_allowed(
        self,
        p: tuple[float, float],
        d_sep: float,
        d_sep_relaxed: float,
        relaxed_entity_id: int
    ) -> bool:
        if not (0.0 <= p[0] < self.width - 1.0 and 0.0 <= p[1] < self.height - 1.0):
            return False

        cell_radius = math.ceil(d_sep / self.cell_size)
        ix_cell, iy_cell = self._cell_coordinates(p)
        ix_min = max(ix_cell - cell_radius, 0)
        ix_max = min(ix_cell + cell_radius, self.cells_x - 1)
        iy_min = max(iy_cell - cell_radius, 0)
        iy_max = min(iy_cell + cell_radius, self.cells_y - 1)

        d_sep_squared = d_sep * d_sep
        d_sep_relaxed_squared = d_sep_relaxed * d_sep_relaxed

        for iy in range(iy_min, iy_max + 1):
            for ix in range(ix_min, ix_max + 1):
                cell = self._cell(ix, iy)
                for candidate in cell:
                    min_dist_squared = d_sep_relaxed_squared if candidate.entity_id == relaxed_entity_id else d_sep_squared
                    x_diff = candidate.point[0] - p[0]
                    y_diff = candidate.point[1] - p[1]
                    dist_squared = x_diff * x_diff + y_diff * y_diff
                    if dist_squared < min_dist_squared:
                        return False
        return True
