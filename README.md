# 🚨 LiftGuard AI

**AI-powered Emergency Detection & Crisis Coordination for Smart
Elevators**

------------------------------------------------------------------------

## 🧠 Overview

LiftGuard AI is a real-time intelligent safety system designed for
hospitality environments (hotels, malls, offices) to detect emergencies
inside elevators and confined spaces.

It combines: - YOLOv8 (Computer Vision) - MediaPipe (Human Behavior
Analysis) - Node.js Backend

------------------------------------------------------------------------

## ⚙️ System Architecture

Camera Feed\
↓\
MediaPipe → fall_detected, motion_score\
YOLOv8 → detections\
↓\
Node.js Backend → risk scoring\
↓\
API Response

------------------------------------------------------------------------

## 📡 API

### POST /api/analyze

#### Request

{ "image": "`<BASE64_IMAGE>`{=html}", "fall_detected": false,
"motion_score": 0.6 }

#### Response

{ "summary": { "num_people": 2, "risk": "MEDIUM", "score": 5.2,
"action": "ALERT_STAFF" } }

------------------------------------------------------------------------

## 🛠️ Setup

git clone https://github.com/your-username/LiftGuardAI.git \
cd LiftGuardAI\
npm install\
node src/server.js

------------------------------------------------------------------------

## 📜 License

MIT License
