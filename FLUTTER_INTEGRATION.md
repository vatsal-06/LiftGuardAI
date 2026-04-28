# Flutter Integration Guide - LiftGuardAI

## Overview

This guide explains how to integrate the LiftGuardAI backend services into a Flutter mobile application. The system provides real-time fall detection and motion analysis using:

- **Live camera frames** - Single-frame analysis for real-time detection
- **Video files** - Complete video processing with frame-by-frame metrics

**Services:**

- **Python FastAPI** (Port 8000): Handles YOLO detection, MediaPipe pose analysis, and **video processing**
- **Node.js Express** (Port 5500): Orchestrates requests and provides unified API

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup](#setup)
3. [API Endpoints](#api-endpoints)
4. [Flutter Implementation](#flutter-implementation)
5. [Example Code](#example-code)
   - [Single Image Analysis](#quick-start-single-image-analysis)
   - [Video File Processing](#video-file-processing-with-live-metrics)
6. [Error Handling](#error-handling)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- Flutter 3.0+
- Dart 2.19+
- Android SDK 21+ or iOS 11+

### Required Flutter Packages

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0 # HTTP client
  image_picker: ^1.0.0 # Camera/gallery access
  camera: ^0.10.0 # Direct camera access
  image: ^4.0.0 # Image processing
  path_provider: ^2.0.0 # File storage
  intl: ^0.19.0 # Formatting
  permission_handler: ^11.4.0 # Runtime permissions
```

---

## Setup

### 1. Create Flutter Project

```bash
flutter create liftguard_ai
cd liftguard_ai
```

### 2. Update `pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  image_picker: ^1.0.0
  camera: ^0.10.0
  image: ^4.0.0
  path_provider: ^2.0.0
  permission_handler: ^11.4.0

dev_dependencies:
  flutter_test:
    sdk: flutter
```

### 3. Configure Platform-Specific Permissions

#### Android (`android/app/src/main/AndroidManifest.xml`)

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

#### iOS (`ios/Runner/Info.plist`)

```xml
<key>NSCameraUsageDescription</key>
<string>We need camera access to detect falls and monitor motion</string>
<key>NSLocalNetworkUsageDescription</key>
<string>We need local network access to communicate with LiftGuardAI</string>
<key>NSBonjourServiceTypes</key>
<array>
  <string>_liftguard._tcp</string>
</array>
```

### 4. Run Flutter Setup

```bash
flutter pub get
flutter pub run build_runner build  # If using code generation
```

---

## API Endpoints

### Endpoint 1: Health Check (Python)

**Purpose:** Verify Python service is running

```
GET /healthz
Host: localhost:8000  (Production: render_backend_url:8000)

Response (200 OK):
{
  "ok": true
}
```

### Endpoint 2: Health Check (Node)

**Purpose:** Verify Node orchestration service is running

```
GET /debug
Host: localhost:5500  (Production: render_backend_url:5500)

Response (200 OK):
{
  "message": "Server is running"
}
```

### Endpoint 3: YOLO Person Detection

**Purpose:** Detect people in frame and draw bounding boxes

```
POST /detect
Host: localhost:8000

Request Body:
{
  "image": "base64_encoded_image_string",
  "fall_detected": false,
  "motion_score": 0.0
}

Response (200 OK):
{
  "detections": [
    {
      "x": 100,
      "y": 50,
      "w": 200,
      "h": 400
    },
    ...
  ],
  "fall_detected": false,
  "motion_score": 0.25,
  "image": "base64_encoded_annotated_image"
}
```

**Response Fields:**

- `detections`: Array of bounding boxes [x, y, w, h] for each detected person
- `fall_detected`: Boolean indicating if a fall was detected
- `motion_score`: Float [0.0-1.0] indicating motion level
- `image`: Base64 annotated image with bounding boxes drawn

### Endpoint 4: MediaPipe Pose Analysis

**Purpose:** Analyze pose landmarks and detect falls/motion

```
POST /mediapipe
Host: localhost:8000

Request Body:
{
  "image": "base64_encoded_image_string"
}

Response (200 OK):
{
  "fall_detected": false,
  "motion_score": 0.15
}
```

**Response Fields:**

- `fall_detected`: Boolean [true if motion_score > 0.35]
- `motion_score`: Float [0.0-1.0] normalized motion score across 10-frame window

### Endpoint 5: Unified Analysis (Recommended for Flutter)

**Purpose:** Complete analysis with YOLO detection + MediaPipe + risk scoring

```
POST /api/analyze
Host: localhost:5500

Request Body:
{
  "image": "base64_encoded_image_string"
}

Response (200 OK):
{
  "summary": {
    "num_people": 1,
    "risk": "CRITICAL",
    "score": 85,
    "action": "ALERT"
  },
  "metrics": {
    "min_distance": 2.5,
    "motion_score": 0.65,
    "fall_detected": true
  },
  "people": [
    {
      "x": 100,
      "y": 50,
      "w": 200,
      "h": 400
    }
  ],
  "debug": {
    "image": "base64_encoded_annotated_image",
    "raw_detections": [...]
  }
}
```

**Response Fields:**

- `summary.num_people`: Count of detected people
- `summary.risk`: Risk level [LOW, MEDIUM, HIGH, CRITICAL]
- `summary.score`: Risk score 0-100
- `summary.action`: Recommended action [MONITOR, ALERT, EMERGENCY]
- `metrics.min_distance`: Minimum distance between people (0=too close)
- `metrics.motion_score`: Overall motion intensity [0.0-1.0]
- `metrics.fall_detected`: Whether a fall was detected
- `people`: Array of bounding boxes for detected people
- `debug.image`: Annotated image for visualization
- `debug.raw_detections`: YOLO raw detection data

### Endpoint 6: Video Processing (Live Metrics)

**Purpose:** Process entire video file and return annotated video with frame-by-frame metrics

```
POST /process-video
Host: localhost:8000
Content-Type: application/json

Request Body:
{
  "video": "base64_encoded_video_string",
  "filename": "fall_demo.mp4"
}

Response (200 OK):
{
  "status": "success",
  "video": "base64_encoded_annotated_video_mp4",
  "metrics": [
    {
      "frame": 0,
      "timestamp_sec": 0.0,
      "num_people": 1,
      "motion_score": 0.15,
      "fall_detected": false,
      "detections": [
        {"x": 100, "y": 50, "w": 200, "h": 400}
      ]
    },
    {
      "frame": 1,
      "timestamp_sec": 0.033,
      "num_people": 1,
      "motion_score": 0.42,
      "fall_detected": true,
      "detections": [
        {"x": 105, "y": 60, "w": 200, "h": 380}
      ]
    },
    ...
  ],
  "summary": {
    "total_frames": 150,
    "duration_sec": 5.0,
    "fps": 30,
    "video_resolution": {"width": 1280, "height": 720},
    "total_falls_detected": 2,
    "avg_motion_score": 0.28,
    "max_motion_score": 0.85,
    "frames_with_people": 145,
    "fall_frames": 8,
    "people_in_video": 1
  }
}
```

**Response Fields:**

- `status`: "success" if processing completed
- `video`: Base64 encoded annotated MP4 video with overlaid metrics
- `metrics`: Array of frame-by-frame detection data:
  - `frame`: Frame number (0-indexed)
  - `timestamp_sec`: Time in video (seconds)
  - `num_people`: People count in frame
  - `motion_score`: Motion intensity [0.0-1.0]
  - `fall_detected`: Boolean fall indicator
  - `detections`: Array of bounding boxes
- `summary`: Overall statistics:
  - `total_frames`: Total video frames
  - `duration_sec`: Video duration in seconds
  - `fps`: Frames per second
  - `video_resolution`: Video dimensions
  - `total_falls_detected`: Total fall events
  - `avg_motion_score`: Average motion across video
  - `max_motion_score`: Peak motion score
  - `frames_with_people`: Count of frames with detected people
  - `fall_frames`: Count of frames with fall detected
  - `people_in_video`: Number of unique people

  **Flutter upload note:** encode the selected video file to base64 before sending it to `/process-video`.

**Supported Video Formats:**

- MP4, AVI, MOV, MKV, WebM

**Processing Notes:**

- Processing time depends on video length and resolution
- Output video includes real-time metrics overlay:
  - Frame counter
  - People count
  - Motion score (0.0-1.0)
  - Fall detection status
- Metrics are frame-accurate for timeline analysis
- Output video uses H.264 codec (MP4 format)

---

## Flutter Implementation

### 1. Create API Service Class

Create `lib/services/liftguard_api_service.dart`:

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:typed_data';

class LiftGuardApiService {
  final String baseUrl;
  final Duration timeout;

  LiftGuardApiService({
    this.baseUrl = 'http://localhost:5500',  // Change for production
    this.timeout = const Duration(seconds: 30),
  });

  /// Check if Node API is running
  Future<bool> isNodeHealthy() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/debug'),
      ).timeout(timeout);
      return response.statusCode == 200;
    } catch (e) {
      print('Node health check failed: $e');
      return false;
    }
  }

  /// Check if Python API is running
  Future<bool> isPythonHealthy() async {
    try {
      final pythonUrl = baseUrl.replaceAll(':5500', ':8000');
      final response = await http.get(
        Uri.parse('$pythonUrl/healthz'),
      ).timeout(timeout);
      return response.statusCode == 200;
    } catch (e) {
      print('Python health check failed: $e');
      return false;
    }
  }

  /// Analyze image for falls and motion
  /// Returns risk assessment with detections
  Future<AnalysisResult> analyzeImage(Uint8List imageBytes) async {
    try {
      // Convert image to base64
      String base64Image = base64Encode(imageBytes);

      final response = await http.post(
        Uri.parse('$baseUrl/api/analyze'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'image': base64Image,
        }),
      ).timeout(timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return AnalysisResult.fromJson(data);
      } else {
        throw Exception('Server error: ${response.statusCode}');
      }
    } catch (e) {
      print('Analysis failed: $e');
      rethrow;
    }
  }

  /// Direct YOLO detection (optional)
  Future<YoloDetectionResult> detectPeople(Uint8List imageBytes) async {
    try {
      String base64Image = base64Encode(imageBytes);
      final pythonUrl = baseUrl.replaceAll(':5500', ':8000');

      final response = await http.post(
        Uri.parse('$pythonUrl/detect'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'image': base64Image,
          'fall_detected': false,
          'motion_score': 0.0,
        }),
      ).timeout(timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return YoloDetectionResult.fromJson(data);
      } else {
        throw Exception('YOLO error: ${response.statusCode}');
      }
    } catch (e) {
      print('YOLO detection failed: $e');
      rethrow;
    }
  }

  /// Direct MediaPipe analysis (optional)
  Future<MediaPipeResult> analyzeMediaPipe(Uint8List imageBytes) async {
    try {
      String base64Image = base64Encode(imageBytes);
      final pythonUrl = baseUrl.replaceAll(':5500', ':8000');

      final response = await http.post(
        Uri.parse('$pythonUrl/mediapipe'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'image': base64Image,
        }),
      ).timeout(timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return MediaPipeResult.fromJson(data);
      } else {
        throw Exception('MediaPipe error: ${response.statusCode}');
      }
    } catch (e) {
      print('MediaPipe analysis failed: $e');
      rethrow;
    }
  }

  /// Process video file and get frame-by-frame metrics
  /// Returns annotated video + live metrics for each frame
  Future<VideoProcessingResult> processVideoFile(Uint8List videoBytes, String filename) async {
    try {
      final pythonUrl = baseUrl.replaceAll(':5500', ':8000');
      final response = await http.post(
        Uri.parse('$pythonUrl/process-video'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'video': base64Encode(videoBytes),
          'filename': filename,
        }),
      ).timeout(const Duration(seconds: 300)); // 5 min timeout for large videos

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return VideoProcessingResult.fromJson(data);
      } else {
        throw Exception('Video processing error: ${response.statusCode}');
      }
    } catch (e) {
      print('Video processing failed: $e');
      rethrow;
    }
  }
}

// Data Models

class VideoProcessingResult {
  final String status;
  final String video;  // Base64 encoded MP4
  final List<FrameMetrics> metrics;
  final VideoSummary summary;

  VideoProcessingResult({
    required this.status,
    required this.video,
    required this.metrics,
    required this.summary,
  });

  factory VideoProcessingResult.fromJson(Map<String, dynamic> json) {
    return VideoProcessingResult(
      status: json['status'] ?? 'unknown',
      video: json['video'] ?? '',
      metrics: (json['metrics'] as List?)
          ?.map((m) => FrameMetrics.fromJson(m))
          .toList() ?? [],
      summary: VideoSummary.fromJson(json['summary'] ?? {}),
    );
  }

  bool get hasErrors => metrics.isEmpty;
  int get totalFalls => summary.totalFallsDetected;
  double get avgMotion => summary.avgMotionScore;
}

class FrameMetrics {
  final int frame;
  final double timestampSec;
  final int numPeople;
  final double motionScore;
  final bool fallDetected;
  final List<Detection> detections;

  FrameMetrics({
    required this.frame,
    required this.timestampSec,
    required this.numPeople,
    required this.motionScore,
    required this.fallDetected,
    required this.detections,
  });

  factory FrameMetrics.fromJson(Map<String, dynamic> json) {
    return FrameMetrics(
      frame: json['frame'] ?? 0,
      timestampSec: (json['timestamp_sec'] ?? 0.0).toDouble(),
      numPeople: json['num_people'] ?? 0,
      motionScore: (json['motion_score'] ?? 0.0).toDouble(),
      fallDetected: json['fall_detected'] ?? false,
      detections: (json['detections'] as List?)
          ?.map((d) => Detection.fromJson(d))
          .toList() ?? [],
    );
  }

  String get timeString {
    final minutes = (timestampSec ~/ 60).toString().padLeft(2, '0');
    final seconds = (timestampSec % 60).toStringAsFixed(2).padLeft(5, '0');
    return '$minutes:$seconds';
  }
}

class VideoSummary {
  final int totalFrames;
  final double durationSec;
  final double fps;
  final Map<String, int> videoResolution;
  final int totalFallsDetected;
  final double avgMotionScore;
  final double maxMotionScore;
  final int framesWithPeople;
  final int fallFrames;
  final int peopleInVideo;

  VideoSummary({
    required this.totalFrames,
    required this.durationSec,
    required this.fps,
    required this.videoResolution,
    required this.totalFallsDetected,
    required this.avgMotionScore,
    required this.maxMotionScore,
    required this.framesWithPeople,
    required this.fallFrames,
    required this.peopleInVideo,
  });

  factory VideoSummary.fromJson(Map<String, dynamic> json) {
    final resolution = json['video_resolution'] as Map?;
    return VideoSummary(
      totalFrames: json['total_frames'] ?? 0,
      durationSec: (json['duration_sec'] ?? 0.0).toDouble(),
      fps: (json['fps'] ?? 30.0).toDouble(),
      videoResolution: {
        'width': resolution?['width'] ?? 1920,
        'height': resolution?['height'] ?? 1080,
      },
      totalFallsDetected: json['total_falls_detected'] ?? 0,
      avgMotionScore: (json['avg_motion_score'] ?? 0.0).toDouble(),
      maxMotionScore: (json['max_motion_score'] ?? 0.0).toDouble(),
      framesWithPeople: json['frames_with_people'] ?? 0,
      fallFrames: json['fall_frames'] ?? 0,
      peopleInVideo: json['people_in_video'] ?? 0,
    );
  }

  String get durationString {
    final minutes = (durationSec ~/ 60).toString().padLeft(2, '0');
    final seconds = (durationSec % 60).toStringAsFixed(2).padLeft(5, '0');
    return '$minutes:$seconds';
  }

  double get detectionAccuracy => framesWithPeople > 0
      ? (framesWithPeople / totalFrames) * 100
      : 0.0;
}

class AnalysisResult {
  final Summary summary;
  final Metrics metrics;
  final List<Detection> people;
  final DebugInfo? debug;

  AnalysisResult({
    required this.summary,
    required this.metrics,
    required this.people,
    this.debug,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      summary: Summary.fromJson(json['summary']),
      metrics: Metrics.fromJson(json['metrics']),
      people: (json['people'] as List)
          .map((p) => Detection.fromJson(p))
          .toList(),
      debug: json['debug'] != null
          ? DebugInfo.fromJson(json['debug'])
          : null,
    );
  }

  bool get isCritical => summary.risk == 'CRITICAL';
  bool get isHigh => summary.risk == 'HIGH';
  bool get isFallDetected => metrics.fallDetected;
  bool get hasHighMotion => metrics.motionScore > 0.5;
}

class Summary {
  final int numPeople;
  final String risk;  // LOW, MEDIUM, HIGH, CRITICAL
  final int score;    // 0-100
  final String action; // MONITOR, ALERT, EMERGENCY

  Summary({
    required this.numPeople,
    required this.risk,
    required this.score,
    required this.action,
  });

  factory Summary.fromJson(Map<String, dynamic> json) {
    return Summary(
      numPeople: json['num_people'] ?? 0,
      risk: json['risk'] ?? 'LOW',
      score: json['score'] ?? 0,
      action: json['action'] ?? 'MONITOR',
    );
  }

  bool get shouldAlert => risk == 'CRITICAL' || risk == 'HIGH';
}

class Metrics {
  final double minDistance;
  final double motionScore;
  final bool fallDetected;

  Metrics({
    required this.minDistance,
    required this.motionScore,
    required this.fallDetected,
  });

  factory Metrics.fromJson(Map<String, dynamic> json) {
    return Metrics(
      minDistance: (json['min_distance'] ?? 0).toDouble(),
      motionScore: (json['motion_score'] ?? 0.0).toDouble(),
      fallDetected: json['fall_detected'] ?? false,
    );
  }
}

class Detection {
  final int x;
  final int y;
  final int width;
  final int height;

  Detection({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
  });

  factory Detection.fromJson(Map<String, dynamic> json) {
    return Detection(
      x: json['x'] ?? 0,
      y: json['y'] ?? 0,
      width: json['w'] ?? 0,
      height: json['h'] ?? 0,
    );
  }

  Rect toRect() => Rect.fromLTWH(
    x.toDouble(),
    y.toDouble(),
    width.toDouble(),
    height.toDouble(),
  );
}

class DebugInfo {
  final String? image;
  final List<dynamic>? rawDetections;

  DebugInfo({
    this.image,
    this.rawDetections,
  });

  factory DebugInfo.fromJson(Map<String, dynamic> json) {
    return DebugInfo(
      image: json['image'],
      rawDetections: json['raw_detections'],
    );
  }
}

class YoloDetectionResult {
  final List<Detection> detections;
  final bool fallDetected;
  final double motionScore;
  final String? image;

  YoloDetectionResult({
    required this.detections,
    required this.fallDetected,
    required this.motionScore,
    this.image,
  });

  factory YoloDetectionResult.fromJson(Map<String, dynamic> json) {
    return YoloDetectionResult(
      detections: (json['detections'] as List)
          .map((d) => Detection.fromJson(d))
          .toList(),
      fallDetected: json['fall_detected'] ?? false,
      motionScore: (json['motion_score'] ?? 0.0).toDouble(),
      image: json['image'],
    );
  }
}

class MediaPipeResult {
  final bool fallDetected;
  final double motionScore;

  MediaPipeResult({
    required this.fallDetected,
    required this.motionScore,
  });

  factory MediaPipeResult.fromJson(Map<String, dynamic> json) {
    return MediaPipeResult(
      fallDetected: json['fall_detected'] ?? false,
      motionScore: (json['motion_score'] ?? 0.0).toDouble(),
    );
  }
}

import 'dart:ui' as ui show Rect;
typedef Rect = ui.Rect;
```

### 2. Create Camera Manager

Create `lib/services/camera_manager.dart`:

```dart
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:typed_data';

class CameraManager {
  CameraController? _controller;
  final ImagePicker _picker = ImagePicker();

  Future<void> initializeCamera(CameraDescription camera) async {
    _controller = CameraController(
      camera,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    try {
      await _controller?.initialize();
    } catch (e) {
      print('Camera initialization error: $e');
      rethrow;
    }
  }

  CameraController? get controller => _controller;

  Future<Uint8List?> captureFrame() async {
    try {
      final image = await _controller?.takePicture();
      if (image != null) {
        return await image.readAsBytes();
      }
    } catch (e) {
      print('Capture error: $e');
    }
    return null;
  }

  Future<Uint8List?> pickImageFromGallery() async {
    try {
      final image = await _picker.pickImage(source: ImageSource.gallery);
      if (image != null) {
        return await image.readAsBytes();
      }
    } catch (e) {
      print('Gallery pick error: $e');
    }
    return null;
  }

  void dispose() {
    _controller?.dispose();
    _controller = null;
  }
}
```

### 3. Create Main Analysis Screen

Create `lib/screens/analysis_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../services/liftguard_api_service.dart';
import '../services/camera_manager.dart';

class AnalysisScreen extends StatefulWidget {
  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  late LiftGuardApiService _apiService;
  late CameraManager _cameraManager;

  AnalysisResult? _lastResult;
  bool _isAnalyzing = false;
  bool _isServiceHealthy = false;
  String _statusMessage = 'Initializing...';

  @override
  void initState() {
    super.initState();
    _apiService = LiftGuardApiService(
      baseUrl: 'http://localhost:5500',  // Change to production URL
    );
    _cameraManager = CameraManager();
    _checkServiceHealth();
    _initializeCamera();
  }

  Future<void> _checkServiceHealth() async {
    final nodeHealthy = await _apiService.isNodeHealthy();
    final pythonHealthy = await _apiService.isPythonHealthy();

    setState(() {
      _isServiceHealthy = nodeHealthy && pythonHealthy;
      _statusMessage = _isServiceHealthy
          ? 'Services Connected ✓'
          : 'Connection Failed ✗';
    });
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      final frontCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      await _cameraManager.initializeCamera(frontCamera);
      setState(() {});
    } catch (e) {
      print('Camera init failed: $e');
    }
  }

  Future<void> _analyzeCurrentFrame() async {
    if (_isAnalyzing || _cameraManager.controller == null) return;

    setState(() => _isAnalyzing = true);

    try {
      final imageBytes = await _cameraManager.captureFrame();
      if (imageBytes != null) {
        final result = await _apiService.analyzeImage(imageBytes);
        setState(() {
          _lastResult = result;
          _statusMessage = result.summary.action;
        });

        // Show alert if critical
        if (result.isCritical) {
          _showAlert(result);
        }
      }
    } catch (e) {
      setState(() => _statusMessage = 'Analysis failed: $e');
    } finally {
      setState(() => _isAnalyzing = false);
    }
  }

  void _showAlert(AnalysisResult result) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('⚠️ Alert'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Risk Level: ${result.summary.risk}'),
            Text('Risk Score: ${result.summary.score}/100'),
            if (result.metrics.fallDetected)
              Text('Fall Detected!', style: TextStyle(color: Colors.red)),
            Text('Action: ${result.summary.action}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('LiftGuardAI Analysis'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _checkServiceHealth,
          ),
        ],
      ),
      body: Column(
        children: [
          // Camera Preview
          if (_cameraManager.controller?.value.isInitialized ?? false)
            Expanded(
              flex: 3,
              child: CameraPreview(_cameraManager.controller!),
            )
          else
            Expanded(
              flex: 3,
              child: Center(child: CircularProgressIndicator()),
            ),

          // Status Panel
          Container(
            padding: EdgeInsets.all(16),
            color: _isServiceHealthy ? Colors.green[100] : Colors.red[100],
            child: Column(
              children: [
                Text(
                  _statusMessage,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (_lastResult != null) ...[
                  SizedBox(height: 8),
                  Text('People: ${_lastResult!.summary.numPeople}'),
                  Text('Risk: ${_lastResult!.summary.risk}'),
                  Text('Motion: ${(_lastResult!.metrics.motionScore * 100).toStringAsFixed(1)}%'),
                ],
              ],
            ),
          ),

          // Action Buttons
          Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _isAnalyzing ? null : _analyzeCurrentFrame,
                  icon: Icon(Icons.camera),
                  label: Text('Analyze'),
                ),
                ElevatedButton.icon(
                  onPressed: () async {
                    // Implement gallery pick
                  },
                  icon: Icon(Icons.photo_library),
                  label: Text('Gallery'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _cameraManager.dispose();
    super.dispose();
  }
}
```

---

## Example Code

### Quick Start: Single Image Analysis

```dart
// main.dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'services/liftguard_api_service.dart';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: SimpleAnalysisPage(),
    );
  }
}

class SimpleAnalysisPage extends StatefulWidget {
  @override
  State<SimpleAnalysisPage> createState() => _SimpleAnalysisPageState();
}

class _SimpleAnalysisPageState extends State<SimpleAnalysisPage> {
  final _apiService = LiftGuardApiService(
    baseUrl: 'http://localhost:5500',
  );
  final _picker = ImagePicker();

  AnalysisResult? _result;
  bool _isLoading = false;

  Future<void> _pickAndAnalyze() async {
    final image = await _picker.pickImage(source: ImageSource.gallery);
    if (image == null) return;

    setState(() => _isLoading = true);

    try {
      final bytes = await image.readAsBytes();
      final result = await _apiService.analyzeImage(bytes);
      setState(() => _result = result);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Fall Detection')),
      body: Center(
        child: _isLoading
            ? CircularProgressIndicator()
            : _result == null
                ? ElevatedButton(
                    onPressed: _pickAndAnalyze,
                    child: Text('Pick Image & Analyze'),
                  )
                : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('Risk: ${_result!.summary.risk}'),
                      Text('Score: ${_result!.summary.score}/100'),
                      Text('Fall Detected: ${_result!.metrics.fallDetected}'),
                      Text('Motion: ${(_result!.metrics.motionScore * 100).toStringAsFixed(1)}%'),
                      ElevatedButton(
                        onPressed: _pickAndAnalyze,
                        child: Text('Analyze Another'),
                      ),
                    ],
                  ),
      ),
    );
  }
}
```

### Video File Processing with Live Metrics

```dart
// video_analysis_page.dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'services/liftguard_api_service.dart';
import 'dart:convert';

class VideoAnalysisPage extends StatefulWidget {
  @override
  State<VideoAnalysisPage> createState() => _VideoAnalysisPageState();
}

class _VideoAnalysisPageState extends State<VideoAnalysisPage> {
  final _apiService = LiftGuardApiService(
    baseUrl: 'http://localhost:5500',
  );
  final _picker = ImagePicker();

  VideoProcessingResult? _result;
  bool _isProcessing = false;
  String _statusMessage = '';

  Future<void> _pickAndProcessVideo() async {
    final video = await _picker.pickVideo(source: ImageSource.gallery);
    if (video == null) return;

    setState(() {
      _isProcessing = true;
      _statusMessage = 'Processing video...';
    });

    try {
      final bytes = await video.readAsBytes();
      final result = await _apiService.processVideoFile(
        bytes,
        video.name,
      );

      setState(() {
        _result = result;
        _statusMessage = 'Processing complete!';
      });
    } catch (e) {
      setState(() => _statusMessage = 'Error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Video Analysis')),
      body: _isProcessing
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text(_statusMessage),
                ],
              ),
            )
          : _result == null
              ? Center(
                  child: ElevatedButton.icon(
                    onPressed: _pickAndProcessVideo,
                    icon: Icon(Icons.videocam),
                    label: Text('Pick & Process Video'),
                  ),
                )
              : SingleChildScrollView(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Video Summary Section
                        Card(
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Video Summary',
                                  style: Theme.of(context).textTheme.headlineSmall,
                                ),
                                SizedBox(height: 12),
                                _summaryRow('Duration', _result!.summary.durationString),
                                _summaryRow('Total Frames', '${_result!.summary.totalFrames}'),
                                _summaryRow('FPS', '${_result!.summary.fps.toStringAsFixed(1)}'),
                                _summaryRow(
                                  'Resolution',
                                  '${_result!.summary.videoResolution['width']}x${_result!.summary.videoResolution['height']}',
                                ),
                              ],
                            ),
                          ),
                        ),
                        SizedBox(height: 16),

                        // Detection Statistics
                        Card(
                          color: _result!.totalFalls > 0 ? Colors.red[100] : Colors.green[100],
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Detection Statistics',
                                  style: Theme.of(context).textTheme.headlineSmall,
                                ),
                                SizedBox(height: 12),
                                _summaryRow(
                                  'Falls Detected',
                                  '${_result!.summary.totalFallsDetected}',
                                  highlight: _result!.totalFalls > 0,
                                ),
                                _summaryRow('Fall Frames', '${_result!.summary.fallFrames}'),
                                _summaryRow('People in Video', '${_result!.summary.peopleInVideo}'),
                                _summaryRow('Frames with People', '${_result!.summary.framesWithPeople}'),
                                _summaryRow(
                                  'Detection Accuracy',
                                  '${_result!.summary.detectionAccuracy.toStringAsFixed(1)}%',
                                ),
                              ],
                            ),
                          ),
                        ),
                        SizedBox(height: 16),

                        // Motion Analysis
                        Card(
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Motion Analysis',
                                  style: Theme.of(context).textTheme.headlineSmall,
                                ),
                                SizedBox(height: 12),
                                _summaryRow(
                                  'Avg Motion Score',
                                  '${_result!.summary.avgMotionScore.toStringAsFixed(4)}',
                                ),
                                _summaryRow(
                                  'Max Motion Score',
                                  '${_result!.summary.maxMotionScore.toStringAsFixed(4)}',
                                ),
                              ],
                            ),
                          ),
                        ),
                        SizedBox(height: 16),

                        // Frame-by-frame Metrics
                        Text(
                          'Frame-by-Frame Metrics',
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        SizedBox(height: 8),
                        SizedBox(
                          height: 200,
                          child: ListView.builder(
                            itemCount: _result!.metrics.length,
                            itemBuilder: (context, index) {
                              final metric = _result!.metrics[index];
                              return ListTile(
                                title: Text('Frame ${metric.frame}'),
                                subtitle: Text(
                                  'Time: ${metric.timeString} | People: ${metric.numPeople} | Motion: ${(metric.motionScore * 100).toStringAsFixed(1)}%',
                                ),
                                trailing: metric.fallDetected
                                    ? Icon(Icons.warning, color: Colors.red)
                                    : null,
                              );
                            },
                          ),
                        ),
                        SizedBox(height: 16),

                        // Action Buttons
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            ElevatedButton.icon(
                              onPressed: () {
                                // Save annotated video
                                _saveVideo(_result!.video);
                              },
                              icon: Icon(Icons.download),
                              label: Text('Save Video'),
                            ),
                            ElevatedButton.icon(
                              onPressed: _pickAndProcessVideo,
                              icon: Icon(Icons.videocam),
                              label: Text('Process Another'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _summaryRow(String label, String value, {bool highlight = false}) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 16)),
          Text(
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: highlight ? Colors.red : null,
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _saveVideo(String base64Video) async {
    try {
      // Decode base64 to bytes
      final bytes = base64Decode(base64Video);

      // Save to app documents directory
      // Implement using path_provider package
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Video saved successfully!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error saving video: $e')),
      );
    }
  }
}
```

---

## Error Handling

### Network Timeouts

```dart
Future<void> _analyzeWithTimeout() async {
  try {
    final result = await _apiService.analyzeImage(imageBytes).timeout(
      Duration(seconds: 30),
      onTimeout: () {
        throw TimeoutException('Analysis took too long');
      },
    );
  } on TimeoutException {
    showError('Request timed out. Check server connection.');
  }
}
```

### Connection Errors

```dart
Future<void> _handleConnectionError(dynamic error) async {
  if (error is SocketException) {
    showError('Cannot connect to server. Check URL and network.');
  } else if (error is TimeoutException) {
    showError('Server not responding. Try again later.');
  } else if (error is FormatException) {
    showError('Invalid response format from server.');
  } else {
    showError('Error: ${error.toString()}');
  }
}
```

### Retry Logic

```dart
Future<AnalysisResult> _analyzeWithRetry(
  Uint8List imageBytes, {
  int maxRetries = 3,
}) async {
  int attempts = 0;

  while (attempts < maxRetries) {
    try {
      return await _apiService.analyzeImage(imageBytes);
    } catch (e) {
      attempts++;
      if (attempts >= maxRetries) rethrow;
      await Future.delayed(Duration(seconds: 2 * attempts));
    }
  }
  throw Exception('Max retries exceeded');
}
```

---

## Deployment

### Local Development

```yaml
# Configuration for localhost
baseUrl: "http://localhost:5500"
pythonBaseUrl: "http://localhost:8000"
```

### Production on Render

1. **Update Backend URLs:**

```dart
final apiService = LiftGuardApiService(
  baseUrl: 'https://your-app.onrender.com:5500',
);
```

2. **Enable HTTPS:**

- Update service configuration to use HTTPS
- Ensure SSL certificates are valid
- Update CORS settings for production domain

3. **Configure Timeouts:**

```dart
final apiService = LiftGuardApiService(
  baseUrl: 'https://your-app.onrender.com:5500',
  timeout: Duration(seconds: 60),  // Increase for slower networks
);
```

4. **Build APK/iOS:**

```bash
# Android
flutter build apk --release

# iOS
flutter build ios --release
```

---

## Troubleshooting

### Issue: Connection Refused

**Cause:** Services not running or wrong URL
**Solution:**

```bash
# Check Python service
curl http://localhost:8000/healthz

# Check Node service
curl http://localhost:5500/debug

# Verify firewall allows connections
```

### Issue: "Cannot connect to server"

**Causes:**

- Wrong IP address (localhost works only on device, use local IP on phone)
- Firewall blocking ports
- Services not responding

**Solution:**

```dart
// For testing on physical device, use local network IP
baseUrl: 'http://192.168.1.100:5500'  // Replace with your machine IP
```

### Issue: Timeout Errors

**Cause:** Analysis taking too long (first run downloads models)
**Solution:**

```dart
// Increase timeout for first request
final apiService = LiftGuardApiService(
  timeout: Duration(seconds: 120),
);

// Send a warm-up request first
await apiService.analyzeImage(testImageBytes);
```

### Issue: "Invalid response format"

**Cause:** Backend version mismatch or JSON parsing error
**Solution:**

- Verify backend is latest version
- Check response data in debug logs
- Print raw response: `print(response.body);`

### Issue: High CPU Usage or Battery Drain

**Solutions:**

- Reduce camera frame rate
- Analyze only key frames (every 5th frame)
- Lower image resolution

```dart
ResolutionPreset.low  // Instead of ResolutionPreset.medium
```

---

## Video Detection Testing

### Testing the `/process-video` Endpoint

Before deploying video processing in your Flutter app, validate the endpoint with test videos.

#### Prerequisites

- Python FastAPI running on port 8000
- Sample test videos (MP4, AVI, MOV, MKV, or WebM)
- `curl` or a Python test script

#### Quick Test (curl)

```bash
# 1. Encode video to base64
VIDEO_BASE64=$(base64 -i test_videos/fall.mp4 | tr -d '\n')

# 2. Send to /process-video
curl -X POST http://localhost:8000/process-video \
  -H "Content-Type: application/json" \
  -d "{
    \"video\": \"$VIDEO_BASE64\",
    \"filename\": \"fall.mp4\"
  }" \
  -o response.json

# 3. Check response
jq '.summary' response.json
```

#### Full Python Test

```python
import requests
import base64
import json
from pathlib import Path

def test_video_processing():
    # Configuration
    API_URL = "http://localhost:8000/process-video"
    VIDEO_FILE = Path("test_videos/fall.mp4")

    if not VIDEO_FILE.exists():
        print(f"❌ Video file not found: {VIDEO_FILE}")
        return False

    try:
        print(f"📹 Loading video: {VIDEO_FILE.name}")
        with open(VIDEO_FILE, 'rb') as f:
            video_bytes = f.read()

        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        print(f"   Size: {len(video_base64) / 1024 / 1024:.2f} MB (encoded)")

        payload = {
            "video": video_base64,
            "filename": VIDEO_FILE.name
        }

        print("⏳ Processing video (this may take a minute)...")
        response = requests.post(API_URL, json=payload, timeout=300)

        print(f"\n📊 Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Error: {response.json()}")
            return False

        result = response.json()

        # Print summary
        summary = result.get('summary', {})
        print(f"\n✅ Video Processing Complete:")
        print(f"   Total Frames: {summary.get('total_frames', 0)}")
        print(f"   Duration: {summary.get('duration_sec', 0):.2f}s")
        print(f"   FPS: {summary.get('fps', 0):.1f}")
        print(f"   Resolution: {summary.get('video_resolution', {})}")
        print(f"   Falls Detected: {summary.get('total_falls_detected', 0)}")
        print(f"   Avg Motion: {summary.get('avg_motion_score', 0):.4f}")
        print(f"   Max Motion: {summary.get('max_motion_score', 0):.4f}")
        print(f"   People in Video: {summary.get('people_in_video', 0)}")

        # Save annotated video
        if 'video' in result:
            video_out = result['video']
            annotated_path = Path("annotated_video.mp4")
            with open(annotated_path, 'wb') as out:
                out.write(base64.b64decode(video_out))
            print(f"\n💾 Annotated video saved: {annotated_path}")

        return True

    except requests.exceptions.Timeout:
        print("❌ Request timeout. Video may be too large or server is slow.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_video_processing()
    exit(0 if success else 1)
```

#### Expected Behavior

**Success Response (200 OK):**

- `status`: "success"
- `video`: Base64-encoded annotated MP4
- `metrics`: Array of frame-level detections
- `summary`: Video statistics

**Input Validation Errors (400):**

- Missing `video` field → `{"error": "No video data provided"}`
- Invalid filename extension → `{"error": "Invalid video format..."}`
- Corrupted video file → `{"error": "Failed to open video file"}`

**Processing Errors (500):**

- YOLO inference failure → `{"error": "Failed to process frame X"}`
- Output encoding failure → `{"error": "Failed to encode output video"}`

#### Performance Guidelines

| Video Duration | Resolution | Est. Time | Memory |
| -------------- | ---------- | --------- | ------ |
| 5s @ 30fps     | 1280x720   | 30-60s    | 500MB  |
| 10s @ 30fps    | 1920x1080  | 90-120s   | 1GB    |
| 30s @ 30fps    | 1920x1080  | 5-10min   | 2GB    |

**Optimization Tips:**

- Use MP4 format (best codec support)
- Keep videos under 30 seconds for mobile
- Resize to 720p for faster processing
- Use lower FPS if available (15 fps is sufficient for fall detection)

### Integration in Flutter

#### Video Processing with Progress Tracking

```dart
Future<void> _processVideoWithProgress() async {
  final video = await _picker.pickVideo(source: ImageSource.gallery);
  if (video == null) return;

  setState(() {
    _isProcessing = true;
    _statusMessage = 'Reading video file...';
  });

  try {
    final bytes = await video.readAsBytes();
    final sizeMB = bytes.length / (1024 * 1024);

    if (sizeMB > 100) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Video too large (${sizeMB.toStringAsFixed(1)}MB). Max 100MB.'))
      );
      return;
    }

    setState(() => _statusMessage = 'Encoding video...');

    final result = await _apiService.processVideoFile(bytes, video.name);

    setState(() {
      _result = result;
      _statusMessage = 'Processing complete!';
    });
  } catch (e) {
    setState(() => _statusMessage = 'Error: $e');
  } finally {
    setState(() => _isProcessing = false);
  }
}
```

#### Handling Large Videos

```dart
// For videos >50MB, show size warning
if (bytes.length > 50 * 1024 * 1024) {
  final confirm = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Large Video'),
      content: Text(
        'This video is large and may take several minutes to process. Continue?'
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: Text('Cancel'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, true),
          child: Text('Process'),
        ),
      ],
    ),
  );

  if (confirm != true) return;
}
```

#### Extracting Frame-Level Fall Detection

```dart
// Get frames with falls
List<FrameMetrics> getFallFrames() {
  return _result!.metrics
      .where((m) => m.fallDetected)
      .toList();
}

// Get peak motion frames
List<FrameMetrics> getPeakMotionFrames({threshold = 0.7}) {
  return _result!.metrics
      .where((m) => m.motionScore > threshold)
      .toList();
}

// Timeline visualization example
ListView.builder(
  itemCount: _result!.metrics.length,
  itemBuilder: (context, index) {
    final metric = _result!.metrics[index];
    final isFall = metric.fallDetected;
    final isHighMotion = metric.motionScore > 0.5;

    return Container(
      color: isFall ? Colors.red[100] : isHighMotion ? Colors.yellow[100] : null,
      child: ListTile(
        title: Text('${metric.timeString}'),
        subtitle: Text(
          'People: ${metric.numPeople} | Motion: ${(metric.motionScore * 100).toStringAsFixed(0)}%'
        ),
        trailing: isFall ? Icon(Icons.warning, color: Colors.red) : null,
      ),
    );
  },
)
```

### Common Issues & Solutions

#### Issue: "Failed to open video file"

**Causes:**

- Corrupted video file
- Unsupported codec
- Missing audio stream (rare)

**Solutions:**

```bash
# Verify video integrity
ffprobe test_videos/fall.mp4

# Re-encode to standard MP4
ffmpeg -i input.mov -c:v libx264 -preset fast -c:a aac output.mp4
```

#### Issue: Processing timeout (>5 min)

**Causes:**

- Video too large
- Server CPU throttled
- Network instability

**Solutions:**

- Reduce video length (< 30 seconds)
- Lower resolution (720p)
- Increase Flutter timeout to 600 seconds

```dart
final apiService = LiftGuardApiService(
  timeout: Duration(seconds: 600),  // 10 minutes
);
```

#### Issue: Memory error during encoding

**Causes:**

- Video resolution too high
- Server RAM exhausted
- Multiple concurrent requests

**Solutions:**

- Process one video at a time
- Reduce resolution on server:

```python
# In yolo_service.py process_video endpoint
scale_factor = 0.5  # 50% resolution
frame_resized = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor)
```

#### Issue: No falls detected in known fall video

**Causes:**

- Fall too fast (motion blur)
- Poor lighting
- Person partially out of frame
- Model sensitivity too high

**Solutions:**

- Check motion scores (should be > 0.3 during fall)
- Verify person detected in frames
- Lower motion threshold in config

---

## Monitoring & Logging

### Add Logging Service

```dart
class LoggingService {
  static final List<String> _logs = [];

  static void log(String message) {
    final timestamp = DateTime.now().toIso8601String();
    final logEntry = '[$timestamp] $message';
    _logs.add(logEntry);
    print(logEntry);
  }

  static List<String> getLogs() => List.from(_logs);

  static void clearLogs() => _logs.clear();
}
```

### Performance Metrics

```dart
class PerformanceMetrics {
  DateTime? _startTime;

  void startAnalysis() => _startTime = DateTime.now();

  double getAnalysisTime() {
    if (_startTime == null) return 0;
    return DateTime.now().difference(_startTime!).inMilliseconds.toDouble();
  }
}
```

---

## Support & Documentation

- **Backend API Docs:** See [API Endpoints](#api-endpoints) section
- **Flutter Documentation:** https://flutter.dev/docs
- **Camera Package:** https://pub.dev/packages/camera
- **HTTP Package:** https://pub.dev/packages/http

---

**Last Updated:** April 2026
**Backend Version:** 1.0.0
**Flutter SDK Required:** 3.0+
