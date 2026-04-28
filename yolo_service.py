from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2
import base64
import numpy as np
import os

from src.mp_module.fallDetection import detect_fall
from src.mp_module.motionAnalysis import compute_motion
from src.mp_module.poseService import get_pose_landmarks

app = FastAPI()
model = YOLO("yolov8n.pt")

FRAME_COUNT = 10
VERTICAL_DROP_THRESHOLD = 0.12

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGIN", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in allowed_origins else allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n", ""}:
            return False
    return bool(value)


def parse_float(value, fallback=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def decode_image(base64_str):
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    img_bytes = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


def encode_image(img):
    _, buffer = cv2.imencode(".jpg", img)
    return base64.b64encode(buffer).decode()


def get_pose(frame):
    return get_pose_landmarks(frame)


def posture_horizontal(pose):
    if pose is None or len(pose) <= 24:
        return False

    left_shoulder = pose[11]
    right_shoulder = pose[12]
    left_hip = pose[23]
    right_hip = pose[24]

    shoulder_width = abs(left_shoulder.x - right_shoulder.x)
    torso_height = abs(
        ((left_shoulder.y + right_shoulder.y) / 2) - ((left_hip.y + right_hip.y) / 2)
    )
    return shoulder_width > (torso_height * 1.2)


def hip_center_y(pose):
    if pose is None or len(pose) <= 24:
        return None
    left_hip = pose[23]
    right_hip = pose[24]
    return (left_hip.y + right_hip.y) / 2


def run_mediapipe_pipeline(frames):
    if not frames:
        return {"fall_detected": False, "motion_score": 0.0}

    prev_pose = None
    motions = []
    valid_poses = []

    for i, frame in enumerate(frames):
        resized = cv2.resize(frame, (640, 480))
        pose = get_pose(resized)
        motion = compute_motion(prev_pose, pose)

        print("Frame:", i)
        print("Pose detected:", pose is not None)
        print("Motion:", motion)

        motions.append(float(motion))
        if pose is not None:
            valid_poses.append(pose)
            prev_pose = pose

    if len(valid_poses) <= (len(frames) // 2):
        motion_score = 0.2
    else:
        motion_score = max(motions) if motions else 0.0

    if motion_score < 0.1:
        motion_score = 0.2

    print("Motion values:", motions)
    print("Final motion_score:", motion_score)

    motion_score = max(0.0, min(1.0, motion_score))

    vertical_drop = 0.0
    if len(valid_poses) >= 2:
        start_y = hip_center_y(valid_poses[0])
        end_y = hip_center_y(valid_poses[-1])
        if start_y is not None and end_y is not None:
            vertical_drop = end_y - start_y

    horizontal_posture = posture_horizontal(valid_poses[-1]) if valid_poses else False
    fall_detected = detect_fall(motion_score) or (
        vertical_drop > VERTICAL_DROP_THRESHOLD and horizontal_posture
    )

    return {
        "fall_detected": bool(fall_detected),
        "motion_score": round(float(motion_score), 4),
    }


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/detect")
async def detect(data: dict):
    image = decode_image(data["image"])
    fall_detected = parse_bool(data.get("fall_detected", False))
    motion_score = parse_float(data.get("motion_score", 0.0))

    results = model(image)[0]

    detections = []

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls == 0:  # person
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            detections.append({"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1})

            # 🎯 DRAW BOX
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # label
            cv2.putText(
                image,
                "Person",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

    fall_color = (0, 0, 255) if fall_detected else (0, 255, 0)
    cv2.putText(
        image,
        f"YOLO Fall: {fall_detected}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        fall_color,
        2,
    )

    cv2.putText(
        image,
        f"YOLO Motion: {motion_score:.5f}",
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 200, 0),
        2,
    )

    # 🔁 Convert annotated image back to base64
    annotated_base64 = encode_image(image)

    print("len(annotated_base64):", len(annotated_base64))

    return {
        "detections": detections,
        "fall_detected": fall_detected,
        "motion_score": motion_score,
        "image": annotated_base64,
    }


@app.post("/mediapipe")
async def mediapipe(data: dict):
    image_data = data.get("image")
    if not image_data:
        return {"fall_detected": False, "motion_score": 0.0}

    frame = decode_image(image_data)
    if frame is None:
        return {"fall_detected": False, "motion_score": 0.0}

    frames = [frame.copy() for _ in range(FRAME_COUNT)]
    return run_mediapipe_pipeline(frames)
