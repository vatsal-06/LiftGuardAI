from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import cv2
import base64
import numpy as np
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict

from src.mp_module.fallDetection import detect_fall
from src.mp_module.motionAnalysis import compute_motion
from src.mp_module.poseService import get_pose_landmarks

app = FastAPI()
model = YOLO("yolov8n.pt")

# Warm up the model once at startup with a small zero image to reduce
# first-request latency and ensure device initialization.
try:
    _warmup_img = np.zeros((640, 640, 3), dtype=np.uint8)
    _ = model(_warmup_img)
    print("YOLO model warmup completed")
except Exception as e:
    print(f"YOLO warmup failed: {e}")

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

    try:
        img_bytes = base64.b64decode(base64_str)
    except Exception:
        return None

    if not img_bytes:
        return None

    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img


def encode_image(img):
    if img is None:
        raise ValueError("empty image")
    if getattr(img, "size", None) == 0:
        raise ValueError("empty image")

    ok, buffer = cv2.imencode(".jpg", img)
    if not ok or buffer is None:
        raise ValueError("failed to encode image")
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
    image = decode_image(data.get("image", ""))
    if image is None:
        return JSONResponse(
            status_code=400, content={"error": "invalid or empty image"}
        )

    fall_detected = parse_bool(data.get("fall_detected", False))
    motion_score = parse_float(data.get("motion_score", 0.0))

    # Resize image to the model's expected input for more consistent performance
    try:
        model_input = cv2.resize(image, (640, 640))
    except Exception:
        model_input = image

    results = model(model_input)[0]

    detections = []

    # Draw on a copy of the model_input so encoding and annotations are consistent
    annotated = model_input.copy()

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls == 0:  # person
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            detections.append({"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1})

            # 🎯 DRAW BOX
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # label
            cv2.putText(
                annotated,
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
        annotated,
        f"YOLO Motion: {motion_score:.5f}",
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 200, 0),
        2,
    )

    # 🔁 Convert annotated image back to base64
    try:
        annotated_base64 = encode_image(annotated)
    except Exception as e:
        print(f"Failed to encode annotated image: {e}")
        return JSONResponse(
            status_code=500, content={"error": "failed to encode annotated image"}
        )

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


@app.post("/process-video")
async def process_video(data: dict):
    """
    Process video data (base64-encoded in JSON) and return annotated video with real-time metrics.

    Returns:
    - status: "success" if processing completed
    - video: Base64 encoded annotated MP4 video with overlaid metrics
    - metrics: Frame-by-frame detection data
    - summary: Overall video statistics
    """

    video_base64 = data.get("video")
    filename = data.get("filename", "video.mp4")

    if not video_base64:
        return {
            "error": "No video data provided. Use 'video' key with base64-encoded data"
        }

    if not filename.endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")):
        return {"error": "Invalid video format. Supported: MP4, AVI, MOV, MKV, WebM"}

    temp_dir = tempfile.mkdtemp()

    try:
        # Decode base64 and save video
        try:
            video_bytes = base64.b64decode(video_base64)
        except Exception as e:
            return {"error": f"Invalid base64 encoding: {str(e)}"}

        video_path = os.path.join(temp_dir, filename)
        with open(video_path, "wb") as buffer:
            buffer.write(video_bytes)

        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Failed to open video file"}

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps == 0 or width == 0 or height == 0:
            return {"error": "Invalid video properties"}

        # Output video path
        output_path = os.path.join(temp_dir, "annotated_output.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Process frames
        metrics = []
        frame_count = 0
        fall_count = 0
        prev_pose = None
        motion_buffer = []  # Track last 10 frames for motion

        print(f"Processing video: {total_frames} frames @ {fps} FPS")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_num = frame_count

            # YOLO Detection
            results = model(frame)[0]
            num_people = 0
            detections = []

            for box in results.boxes:
                cls = int(box.cls[0])
                if cls == 0:  # person
                    num_people += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    detections.append({"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1})

                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        "Person",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

            # MediaPipe Analysis
            resized = cv2.resize(frame, (640, 480))
            pose = get_pose(resized)
            motion = compute_motion(prev_pose, pose)
            motion_buffer.append(float(motion))

            # Keep last 10 frames for aggregation
            if len(motion_buffer) > FRAME_COUNT:
                motion_buffer.pop(0)

            motion_score = max(motion_buffer) if motion_buffer else 0.0
            if motion_score < 0.1:
                motion_score = 0.2
            motion_score = max(0.0, min(1.0, motion_score))

            # Fall detection
            fall_detected = detect_fall(motion_score)
            if fall_detected:
                fall_count += 1

            prev_pose = pose

            # Draw metrics on frame
            fall_color = (0, 0, 255) if fall_detected else (0, 255, 0)
            cv2.putText(
                frame,
                f"Frame: {frame_num}/{total_frames}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"People: {num_people}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"Motion: {motion_score:.3f}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 200, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Fall: {'YES' if fall_detected else 'NO'}",
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                fall_color,
                2,
            )

            # Store frame metrics
            metrics.append(
                {
                    "frame": frame_num,
                    "timestamp_sec": frame_num / fps,
                    "num_people": num_people,
                    "motion_score": round(float(motion_score), 4),
                    "fall_detected": bool(fall_detected),
                    "detections": detections,
                }
            )

            # Write annotated frame to output video
            out.write(frame)

            frame_count += 1

            # Progress indicator
            if frame_count % 30 == 0:
                print(f"  Processed {frame_count}/{total_frames} frames...")

        cap.release()
        out.release()

        # Encode output video to base64
        with open(output_path, "rb") as video_file:
            video_base64 = base64.b64encode(video_file.read()).decode()

        # Calculate summary statistics
        summary = {
            "total_frames": total_frames,
            "duration_sec": total_frames / fps,
            "fps": fps,
            "video_resolution": {"width": width, "height": height},
            "total_falls_detected": fall_count,
            "avg_motion_score": (
                round(sum(m["motion_score"] for m in metrics) / len(metrics), 4)
                if metrics
                else 0.0
            ),
            "max_motion_score": (
                round(max(m["motion_score"] for m in metrics), 4) if metrics else 0.0
            ),
            "frames_with_people": len([m for m in metrics if m["num_people"] > 0]),
            "fall_frames": len([m for m in metrics if m["fall_detected"]]),
            "people_in_video": len(set(p for m in metrics for p in [m["num_people"]])),
        }

        print(f"Video processing complete!")
        print(f"  Falls detected: {fall_count}")
        print(f"  Average motion: {summary['avg_motion_score']}")

        return {
            "status": "success",
            "video": video_base64,
            "metrics": metrics,
            "summary": summary,
        }

    except Exception as e:
        print(f"Error processing video: {e}")
        return {"error": f"Video processing failed: {str(e)}"}

    finally:
        # Cleanup temp files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
