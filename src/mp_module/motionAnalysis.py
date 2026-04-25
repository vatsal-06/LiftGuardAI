# Motion Analysis Module
previous_positions = []

def detect_sudden_motion(landmarks):
    global previous_positions

    if not landmarks:
        return 0

    current = [(lm.x, lm.y) for lm in landmarks]

    if not previous_positions:
        previous_positions = current
        return 0

    movement = 0
    for i in range(len(current)):
        dx = current[i][0] - previous_positions[i][0]
        dy = current[i][1] - previous_positions[i][1]
        movement += (dx**2 + dy**2)

    previous_positions = current

    return movement