import cv2
import mediapipe as mp
import sys

try:
    mp_pose = mp.solutions.pose
except AttributeError:
    try:
        from mediapipe import solutions as mp_solutions

        mp_pose = mp_solutions.pose
    except Exception as exc:
        raise ImportError(
            "MediaPipe Pose API is unavailable in this environment. "
            "Detected Python "
            f"{sys.version_info.major}.{sys.version_info.minor}. "
            "Use Python 3.10-3.12 (3.11 recommended), recreate venv, and reinstall mediapipe."
        ) from exc

pose = mp_pose.Pose()


def get_pose_landmarks(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    if result.pose_landmarks:
        return result.pose_landmarks.landmark
    return None
