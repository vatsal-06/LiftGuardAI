import math

_prev_pose = None


def _to_points(pose):
    if pose is None:
        return []
    points = []
    for lm in pose:
        x = getattr(lm, "x", None)
        y = getattr(lm, "y", None)
        if x is None or y is None:
            try:
                x, y = lm[0], lm[1]
            except Exception:
                continue
        points.append((float(x), float(y)))
    return points


def compute_motion(prev_pose, curr_pose):
    if prev_pose is None or curr_pose is None:
        return 0.0

    prev_points = _to_points(prev_pose)
    curr_points = _to_points(curr_pose)

    if not prev_points or not curr_points:
        return 0.0

    count = min(len(prev_points), len(curr_points))
    if count == 0:
        return 0.0

    total = 0.0
    for i in range(count):
        dx = curr_points[i][0] - prev_points[i][0]
        dy = curr_points[i][1] - prev_points[i][1]
        total += math.sqrt((dx * dx) + (dy * dy))

    avg_distance = total / count
    avg_distance_px = avg_distance * 800.0
    motion = avg_distance_px / 200.0
    motion = motion * 5.0
    motion = min(max(motion, 0.0), 1.0)
    return round(motion, 4)


def detect_sudden_motion(landmarks):
    global _prev_pose
    motion = compute_motion(_prev_pose, landmarks)
    if landmarks is not None:
        _prev_pose = landmarks
    return motion
