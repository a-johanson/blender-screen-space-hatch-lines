def catmull_rom_spline(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float], t: float) -> tuple[float, float]:
    t2 = t * t
    t3 = t2 * t

    b0 = -0.5 * t3 + t2 - 0.5 * t
    b1 = 1.5 * t3 - 2.5 * t2 + 1
    b2 = -1.5 * t3 + 2 * t2 + 0.5 * t
    b3 = 0.5 * t3 - 0.5 * t2

    x = b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0]
    y = b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1]

    return (x, y)


def catmull_rom_interpolate(points: list[tuple[float, float]], points_per_segment: int = 10) -> list[tuple[float, float]]:
    assert len(points) >= 4, "At least 4 points are required for Catmull-Rom interpolation"

    generated_points = []

    for i in range(len(points) - 3):
        p0 = points[i]
        p1 = points[i + 1]
        p2 = points[i + 2]
        p3 = points[i + 3]

        for j in range(points_per_segment):
            t = j / points_per_segment
            generated_points.append(catmull_rom_spline(p0, p1, p2, p3, t))

    return generated_points
