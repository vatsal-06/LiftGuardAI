from fastapi import FastAPI
from ultralytics import YOLO
import cv2
import base64
import numpy as np

app = FastAPI()
model = YOLO("yolov8n.pt")


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
