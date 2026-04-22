# 🚨 LiftGuard AI  
**AI-powered Emergency Detection & Crisis Coordination for Smart Elevators**

---

## 🧠 Overview

LiftGuard AI is a real-time intelligent safety system designed for **hospitality environments (hotels, malls, offices)** to detect emergencies inside elevators and confined spaces.

It combines:
- 👁️ YOLOv8 (Computer Vision) → Detects people & spatial relationships  
- 🧍 MediaPipe (Human Behavior Analysis) → Detects falls & abnormal motion  
- ⚙️ Node.js Backend → Risk scoring + decision engine  

---

## 🎯 Problem

- CCTV feeds are passively monitored  
- Emergency response is delayed  
- Communication is fragmented  

---

## 💡 Solution

- Real-time video analysis  
- Instant risk detection  
- Actionable alerts  
- Unified coordination layer  

---

## ⚙️ System Architecture

- Camera Feed
- ↓
- MediaPipe → fall_detected, motion_score
- YOLOv8 → detections, bounding boxes
- ↓
- Node.js Backend → proximity + risk scoring
- ↓
- API Response → risk, action, structured data

---

## 🧩 Tech Stack

- Backend: Node.js (Express), Axios  
- CV: YOLOv8 (Ultralytics), OpenCV  
- Behavior: MediaPipe  
- Frontend: Flutter  

---

## 🚀 Features

- Person detection  
- Proximity analysis  
- Fall detection  
- Motion analysis  
- Risk scoring (LOW / MEDIUM / HIGH)  
- Debug image output  

---

## 🧠 Risk Logic

```js
if (num_people === 1 && fall_detected) score += 6;
if (num_people === 2 && distance < 0.2) score += 3;
if (num_people >= 3) score += 2;
if (motion_score > 0.7) score += 2;

## 📡 API

## POST /api/analyze

### Request

{
  "image": "<BASE64_IMAGE>",
  "fall_detected": false,
  "motion_score": 0.6
}

### Response

{
  "summary": {
    "num_people": 2,
    "risk": "MEDIUM",
    "score": 5.2,
    "action": "ALERT_STAFF"
  },
  "metrics": {
    "min_distance": 0.18,
    "motion_score": 0.6,
    "fall_detected": false
  },
  "people": [
    {
      "id": 1,
      "bbox": { "x": 100, "y": 120, "w": 80, "h": 160 },
      "centroid": { "x": 0.32, "y": 0.45 }
    }
  ],
  "debug": {
    "image": "<BASE64_DEBUG_IMAGE>",
    "raw_detections": []
  }
}

---

## 🛠️ Setup

### Clone

git clone https://github.com/your-username/LiftGuardAI.git
cd LiftGuardAI

### Backend

npm install
node src/server.js

### YOLO Service

pip install ultralytics opencv-python fastapi uvicorn
uvicorn yolo_service:app --reload --port 8000

### Test

curl -X POST http://localhost:5500/api/analyze \
-H "Content-Type: application/json" \
-d '{"image":"<BASE64>","fall_detected":false,"motion_score":0.5}'

---

## 🧪 Testing

- Postman
- Curl
- Node script

---

## ⚠️ Challenges

- Mirror reflections
- Low-light noise
- Real-time performance

---

## 🚀 Future

- Live video streaming
- Person tracking
- Dashboard
- IoT integration
- Mobile alerts

----

## 👥 Team

- Backend + YOLO + Risk Engine
- Frontend + MediaPipe