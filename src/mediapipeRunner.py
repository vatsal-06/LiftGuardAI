import cv2
import requests
import os
from dotenv import load_dotenv

from src.mp_module.poseService import get_pose_landmarks
from src.mp_module.fallDetection import detect_fall
from src.mp_module.motionAnalysis import detect_sudden_motion

# ✅ Load .env
load_dotenv()

# ✅ Get API from env
BACKEND_API = os.getenv("BACKEND_API")

if not BACKEND_API:
    raise ValueError("BACKEND_API not found in .env file")

# 🎥 Video input
cap = cv2.VideoCapture("test_videos/fall.mp4")

while True:
    ret, frame = cap.read()

    # 🔁 Loop video
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    landmarks = get_pose_landmarks(frame)

    fall = detect_fall(landmarks)
    motion = detect_sudden_motion(landmarks)

    data = {
        "fall_detected": fall,
        "motion_score": float(motion)
    }

    print("Sending:", data)

    try:
        response = requests.post(BACKEND_API, json=data)
        result = response.json()

        print("Response:", result)

        risk = result.get("risk", "UNKNOWN")
        action = result.get("action", "NONE")

    except Exception as e:
        print("Error:", e)
        risk = "NO BACKEND"
        action = "NONE"

    # 🖥️ Display
    cv2.putText(frame, f"Fall: {fall}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.putText(frame, f"Motion: {round(motion, 2)}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.putText(frame, f"Risk: {risk}", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.putText(frame, f"Action: {action}", (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("LiftGuard AI - Test", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()