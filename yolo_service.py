from fastapi import FastAPI
from ultralytics import YOLO
import cv2
import base64
import numpy as np

app = FastAPI()
model = YOLO("yolov8n.pt")


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

    results = model(image)[0]

    detections = []

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls == 0:  # person
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            detections.append({
                "x": x1,
                "y": y1,
                "w": x2 - x1,
                "h": y2 - y1
            })

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
                2
            )

    # 🔁 Convert annotated image back to base64
    annotated_base64 = encode_image(image)

    print("len(annotated_base64):", len(annotated_base64))

    return {
        "detections": detections,
        "image": annotated_base64
    }