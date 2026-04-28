#!/usr/bin/env python3
"""
Test all endpoints for LiftGuardAI services
"""

import requests
import json
import base64
import cv2
import numpy as np
from pathlib import Path

# Configuration
PYTHON_BASE_URL = "http://localhost:8000"
NODE_BASE_URL = "http://localhost:5500"


def create_test_image():
    """Create a simple test image"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add some features to make YOLO detection possible
    cv2.circle(img, (320, 240), 100, (0, 255, 0), -1)
    cv2.rectangle(img, (200, 150), (450, 350), (255, 0, 0), 2)

    # Convert to base64
    _, buffer = cv2.imencode(".jpg", img)
    img_base64 = base64.b64encode(buffer).decode("utf-8")
    return img_base64


def test_python_health():
    """Test GET /healthz"""
    print("\n🔍 Testing Python Health Endpoint: GET /healthz")
    try:
        response = requests.get(f"{PYTHON_BASE_URL}/healthz", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_python_detect():
    """Test POST /detect"""
    print("\n🔍 Testing Python YOLO Detect: POST /detect")
    try:
        img_base64 = create_test_image()
        payload = {"image": img_base64, "fall_detected": False, "motion_score": 0.0}
        response = requests.post(f"{PYTHON_BASE_URL}/detect", json=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response keys: {list(result.keys())}")
        print(f"   Detections: {result.get('detections', [])}")
        print(f"   Fall detected: {result.get('fall_detected')}")
        print(f"   Motion score: {result.get('motion_score')}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_python_mediapipe():
    """Test POST /mediapipe"""
    print("\n🔍 Testing Python MediaPipe: POST /mediapipe")
    try:
        img_base64 = create_test_image()
        payload = {"image": img_base64}
        response = requests.post(
            f"{PYTHON_BASE_URL}/mediapipe", json=payload, timeout=15
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response keys: {list(result.keys())}")
        print(f"   Fall detected: {result.get('fall_detected')}")
        print(f"   Motion score: {result.get('motion_score')}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_node_health():
    """Test GET /debug"""
    print("\n🔍 Testing Node Health Endpoint: GET /debug")
    try:
        response = requests.get(f"{NODE_BASE_URL}/debug", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_node_analyze():
    """Test POST /api/analyze"""
    print("\n🔍 Testing Node Analyze: POST /api/analyze")
    try:
        img_base64 = create_test_image()
        payload = {"image": img_base64}
        response = requests.post(
            f"{NODE_BASE_URL}/api/analyze", json=payload, timeout=20
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response keys: {list(result.keys())}")
        if "summary" in result:
            print(f"   Summary: {result['summary']}")
        if "metrics" in result:
            print(f"   Metrics: {result['metrics']}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_python_process_video():
    """Test POST /process-video with a sample file from test_videos"""
    print("\n🔍 Testing Python Process Video: POST /process-video")
    try:
        sample_dir = Path(__file__).parent / "test_videos"
        video_file = sample_dir / "fall.mp4"
        if not video_file.exists():
            print(f"   ❌ Sample video not found: {video_file}")
            return False

        with open(video_file, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {"video": video_b64, "filename": video_file.name}
        response = requests.post(
            f"{PYTHON_BASE_URL}/process-video", json=payload, timeout=120
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if response.status_code != 200:
            print(f"   Error response: {result}")
            return False

        if "video" in result:
            out_b64 = result["video"]
            out_path = Path("./annotated_video_result.mp4")
            with open(out_path, "wb") as out:
                out.write(base64.b64decode(out_b64))
            print(f"   Saved annotated video to: {out_path}")
        else:
            print("   No video returned in response")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("LiftGuardAI Endpoint Test Suite")
    print("=" * 60)

    results = {}

    # Test Python FastAPI
    print("\n" + "=" * 60)
    print("PYTHON FASTAPI SERVICE (port 8000)")
    print("=" * 60)
    results["python_health"] = test_python_health()
    results["python_detect"] = test_python_detect()
    results["python_mediapipe"] = test_python_mediapipe()
    results["python_process_video"] = test_python_process_video()

    # Test Node.js
    print("\n" + "=" * 60)
    print("NODE.JS EXPRESS SERVICE (port 5500)")
    print("=" * 60)
    results["node_health"] = test_node_health()
    results["node_analyze"] = test_node_analyze()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All endpoints are working!")
    else:
        print("❌ Some endpoints failed. Check the errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
