# LiftGuardAI Run Guide

This guide runs the full pipeline:

- YOLO service (FastAPI, port 8000)
- MediaPipe service (FastAPI, port 8001)
- Node backend (Express, port 5500)
- Client call to `/api/analyze` with base64 image

MediaPipe behavior in current build:

- CLI video mode processes 10 consecutive frames starting at `--frame-index`
- API mode (`POST /mediapipe`) decodes one image and duplicates it 10 times to simulate a short sequence
- Motion score uses spike detection (`max` motion across 10 frames) with a minimum activation floor
- Demo fall trigger uses `motion_score > 0.35`
- Output shape is:
  - `{ "fall_detected": boolean, "motion_score": 0..1 }`

## 1. Prerequisites

- macOS with Python 3.10-3.12 (Python 3.11 recommended) and Node.js 18+
- `yolov8n.pt` present in project root
- A test image or video frame to convert to base64 for API requests

## 2. Open project

```bash
cd /Users/vatsalgupta/Developer/LiftGuardAI
```

## 3. Install Node dependencies

```bash
npm install
```

## 4. Prepare Python environment

If you already have `venv/`, activate it. Otherwise create one.

Use Python 3.11 explicitly (recommended for MediaPipe compatibility):

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn ultralytics opencv-python numpy "mediapipe==0.10.14" python-dotenv requests
```

## 5. Start services (3 terminals)

Use three separate terminals.

### Terminal 1: YOLO FastAPI service

```bash
cd /Users/vatsalgupta/Developer/LiftGuardAI
source venv/bin/activate
uvicorn yolo_service:app --host 0.0.0.0 --port 8000 --reload
```

Expected: FastAPI server running on `http://localhost:8000`.

### Terminal 2: MediaPipe FastAPI service

```bash
cd /Users/vatsalgupta/Developer/LiftGuardAI
source venv/bin/activate
python -m src.mediapipeRunner --serve --host 0.0.0.0 --port 8001
```

Expected: FastAPI server running on `http://localhost:8001`.

### Terminal 3: Node backend

```bash
cd /Users/vatsalgupta/Developer/LiftGuardAI
node src/server.js
```

Expected: `Server running on http://localhost:5500`.

## 6. Send analyze request

`/api/analyze` now expects only `image` in request body.

Example request:

```bash
curl -X POST http://localhost:5500/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"image":"<BASE64_IMAGE>"}'
```

## 7. Optional helper to test MediaPipe directly

```bash
cd /Users/vatsalgupta/Developer/LiftGuardAI
source venv/bin/activate
python -m src.mediapipeRunner --video test_videos/fall.mp4 --frame-index 10
```

Expected:

- Processes frames from `frame-index` to `frame-index + 9`.
- Prints debug logs per frame (`Frame`, `Pose detected`, `Motion`).
- Prints aggregate debug logs (`Motion values`, `Final motion_score`).
- Outputs JSON with `fall_detected` and `motion_score`.

Optional base64 CLI mode:

```bash
python -m src.mediapipeRunner --image-base64 "<BASE64_IMAGE>"
```

## 8. Quick health checks (optional)

### Backend check

```bash
curl http://localhost:5500/debug
```

Expected response:

```json
{ "message": "Server is running" }
```

### YOLO endpoint check

YOLO `/detect` expects JSON with a base64 image:

```json
{
  "image": "<BASE64_IMAGE>"
}
```

### MediaPipe endpoint check

MediaPipe `/mediapipe` expects JSON with base64 image:

```json
{
  "image": "<BASE64_IMAGE>"
}
```

Example curl:

```bash
curl -X POST http://localhost:8001/mediapipe \
  -H "Content-Type: application/json" \
  -d '{"image":"<BASE64_IMAGE>"}'
```

## 9. Stop the project

- In each terminal, press `Ctrl+C`.

## 10. Common issues

- Node returns timeout from YOLO:
  - Verify Terminal 1 is running on port 8000.
- Node returns timeout from MediaPipe:
  - Verify Terminal 2 is running on port 8001.
- `ModuleNotFoundError` in Python:
  - Activate `venv` and reinstall required packages.
- `AttributeError: module 'mediapipe' has no attribute 'solutions'`:
  - This usually means unsupported Python (for example 3.14) or wrong MediaPipe wheel.
  - Recreate venv with Python 3.11 and reinstall:

```bash
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn ultralytics opencv-python numpy "mediapipe==0.10.14" python-dotenv requests
```

- If `mediapipe` install fails on Apple Silicon, try:

```bash
pip install mediapipe-silicon
```
