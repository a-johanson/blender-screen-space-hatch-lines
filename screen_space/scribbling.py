import random

from .stippling import Stipple


def scribbles_from_stipples(
        stipples: list[Stipple],
        initial_sampling_rate: int = 50,
        min_remaining_point_fraction: float = 0.025,
        depth_factor: float = 1.0,
        stipple_stroke_length: float = 0.0
) -> list[tuple[float, float]]:
    if len(stipples) < 2:
        return []

    path = []
    points = stipples.copy()
    random.shuffle(points)

    path.append(points.pop(0))

    while len(points) / len(stipples) > min_remaining_point_fraction:
        min_distance = float("inf")
        nearest_index = 0
        sampling_rate = max(1, int(initial_sampling_rate * len(points) / len(stipples)))

        last_p = path[-1]
        i = min(len(points) - 1, random.randint(0, sampling_rate))
        while i < len(points):
            p = points[i]

            spatial_dist = (p.x - last_p.x)**2 + (p.y - last_p.y)**2
            depth_dist = 0.0
            if last_p.depth + p.depth > 0.0:
                depth_dist = depth_factor * abs(p.depth - last_p.depth) / (last_p.depth + p.depth)

            distance = spatial_dist + depth_dist

            if distance < min_distance:
                min_distance = distance
                nearest_index = i

            i_next = i + 1 + random.randint(0, sampling_rate)
            if i_next >= len(points):
                break
            i = i_next

        if nearest_index < len(points):
            path.append(points.pop(nearest_index))

    def stipple_to_point(stipple: Stipple) -> tuple[float, float]:
        if stipple_stroke_length > 0.0:
            t = (random.random() - 0.5) * stipple_stroke_length
            return (
                stipple.x + t * stipple.direction[0],
                stipple.y + t * stipple.direction[1]
            )
        else:
            return (stipple.x, stipple.y)

    return [stipple_to_point(s) for s in path]
