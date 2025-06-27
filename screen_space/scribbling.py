import random


def scribbles_from_stipples(
        stipples: list[tuple[float, float, float]], # (x, y, depth)
        initial_sampling_rate: int = 50,
        min_remaining_point_fraction: float = 0.025,
        depth_factor: float = 1.0
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

        last_x, last_y, last_d = path[-1]
        i = min(len(points) - 1, random.randint(0, sampling_rate))
        while i < len(points):
            x, y, d = points[i]

            spatial_dist = (x - last_x)**2 + (y - last_y)**2
            depth_dist = 0.0
            if last_d + d > 0.0:
                depth_dist = depth_factor * abs(d - last_d) / (last_d + d)

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

    return [(x, y) for x, y, _ in path]
