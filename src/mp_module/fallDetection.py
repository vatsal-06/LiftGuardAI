# Fall Detection Module
def detect_fall(landmarks):
    if not landmarks:
        return False

    # Example logic:
    nose = landmarks[0]
    hip = landmarks[24]

    # If body becomes horizontal (y values similar)
    if abs(nose.y - hip.y) < 0.05:
        return True

    return False