import argparse
import base64
import json

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from src.mp_module.fallDetection import detect_fall
from src.mp_module.motionAnalysis import compute_motion
from src.mp_module.poseService import get_pose_landmarks


app = FastAPI()

FRAME_COUNT = 10
VERTICAL_DROP_THRESHOLD = 0.12


class MediaPipeRequest(BaseModel):
    image: str | None = None


def get_pose(frame):
    return get_pose_landmarks(frame)


def decode_image(base64_str: str):
    if not base64_str:
        return None
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(base64_str)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


def read_video_frames(video_path: str, frame_index: int = 0, count: int = FRAME_COUNT):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    if frame_index > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    frames = []
    for _ in range(count):
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)

    cap.release()
    return frames


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


def run_pipeline(frames):
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


@app.post("/mediapipe")
async def mediapipe_endpoint(payload: MediaPipeRequest):
    frame = decode_image(payload.image)
    if frame is None:
        return {"fall_detected": False, "motion_score": 0.0}

    frames = [frame.copy() for _ in range(FRAME_COUNT)]
    return run_pipeline(frames)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--video", dest="video_path")
    parser.add_argument("--image-base64", dest="image_base64")
    parser.add_argument("--frame-index", type=int, default=0)
    args = parser.parse_args()

    if args.serve:
        uvicorn.run(
            "src.mediapipeRunner:app", host=args.host, port=args.port, reload=False
        )
        return

    if args.video_path:
        frames = read_video_frames(args.video_path, args.frame_index, FRAME_COUNT)
        result = run_pipeline(frames)
        print(json.dumps(result))
        return

    if args.image_base64:
        frame = decode_image(args.image_base64)
        if frame is None:
            print(json.dumps({"fall_detected": False, "motion_score": 0.0}))
            return
        frames = [frame.copy() for _ in range(FRAME_COUNT)]
        result = run_pipeline(frames)
        print(json.dumps(result))
        return

    print(json.dumps({"fall_detected": False, "motion_score": 0.0}))


if __name__ == "__main__":
    main()
