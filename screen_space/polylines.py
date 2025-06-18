import heapq


def triangle_area(p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> float:
    """Calculate the area of a triangle using the cross product of p2-p1 and p3-p1."""
    return 0.5 * abs((p2[0]-p1[0])*(p3[1]-p1[1]) - (p2[1]-p1[1])*(p3[0]-p1[0]))

def visvalingam_whyatt(points: list[tuple[float, float]], max_area: float) -> list[tuple[float, float]]:
    """
    Simplify a polyline using the Visvalingam-Whyatt algorithm.
    """
    if not points or max_area <= 0.0 or len(points) < 3:
        return points.copy()

    # Track deleted points
    is_deleted = [False] * len(points)
    active_point_count = len(points)

    # Store adjacency information for efficient updates
    # Track current version of point metadata to ignore stale heap entries
    point_metadata = {} # index -> (area, version, prev_idx, next_idx)
    areas_heap = []  # (area, index, version) as a priority queue

    # Initialize adjacency links (like a doubly linked list)
    for i in range(len(points)):
        prev_idx = i - 1 if i > 0 else None
        next_idx = i + 1 if i < len(points) - 1 else None

        # Calculate area for interior points
        if 0 < i < len(points) - 1:
            area = triangle_area(points[i-1], points[i], points[i+1])
            point_metadata[i] = (area, 0, prev_idx, next_idx)
            heapq.heappush(areas_heap, (area, i, 0))
        else:
            # End points have no area but still need adjacency info
            point_metadata[i] = (float("inf"), 0, prev_idx, next_idx)

    # Process points until too few points remain
    while areas_heap and active_point_count > 2:
        area, idx, version = heapq.heappop(areas_heap)

        # Skip already deleted or stale entry
        if is_deleted[idx] or point_metadata[idx][1] != version:
            continue

        # Stop if area threshold reached
        if area >= max_area:
            break

        # Mark point as deleted
        is_deleted[idx] = True
        active_point_count -= 1

        # Get adjacent point indices
        _, _, prev_idx, next_idx = point_metadata[idx]

        # Update adjacency links to bypass deleted point and recalculate areas for affected points
        if prev_idx is not None:
            _, prev_version, prev_prev_idx, _ = point_metadata[prev_idx]
            new_version = prev_version + 1
            if prev_prev_idx is not None and next_idx is not None:
                new_area = triangle_area(points[prev_prev_idx], points[prev_idx], points[next_idx])
                heapq.heappush(areas_heap, (new_area, prev_idx, new_version))
            else:
                new_area = float("inf")
            point_metadata[prev_idx] = (new_area, new_version, prev_prev_idx, next_idx)

        if next_idx is not None:
            _, next_version, _, next_next_idx = point_metadata[next_idx]
            new_version = next_version + 1
            if prev_idx is not None and next_next_idx is not None:
                new_area = triangle_area(points[prev_idx], points[next_idx], points[next_next_idx])
                heapq.heappush(areas_heap, (new_area, next_idx, new_version))
            else:
                new_area = float("inf")
            point_metadata[next_idx] = (new_area, new_version, prev_idx, next_next_idx)

    return [p for i, p in enumerate(points) if not is_deleted[i]]
