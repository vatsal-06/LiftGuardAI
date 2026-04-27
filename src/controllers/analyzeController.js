const axios = require("axios");
const { getDetections } = require("../services/yoloService");
const { computeDistance } = require("../services/proximityService");
const { computeRisk } = require("../services/riskEngine");
const { cleanDetections } = require("../services/detectionService");

const FRAME_WIDTH = 640;
const FRAME_HEIGHT = 480;
const MEDIAPIPE_SERVICE_URL =
  process.env.MEDIAPIPE_SERVICE_URL || "http://localhost:8001/mediapipe";

const normalize = (val, max) => val / max;
const parseNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};
const parseBoolean = (value) => {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes", "y"].includes(normalized)) return true;
    if (["false", "0", "no", "n", ""].includes(normalized)) return false;
  }
  return Boolean(value);
};

exports.analyze = async (req, res) => {
  try {
    const { image } = req.body;

    if (!image) {
      return res.status(400).json({ error: "image is required" });
    }

    const yoloRes = await getDetections(image);
    const yoloDetections = yoloRes?.detections || [];

    console.log("YOLO count:", yoloDetections.length);

    const detections = cleanDetections(yoloDetections);

    let fall_detected = false;
    let motion_score = 0;

    if (detections.length > 0) {
      try {
        const mpRes = await axios.post(
          MEDIAPIPE_SERVICE_URL,
          { image },
          { timeout: 5000 }
        );

        console.log("MediaPipe:", mpRes.data);

        fall_detected = parseBoolean(mpRes?.data?.fall_detected);
        motion_score = parseNumber(mpRes?.data?.motion_score, 0);
      } catch (mpErr) {
        console.log("MediaPipe:", {
          fall_detected: false,
          motion_score: 0,
          error: mpErr.message,
        });
        fall_detected = false;
        motion_score = 0;
      }
    } else {
      console.log("MediaPipe:", { fall_detected: false, motion_score: 0, skipped: true });
    }

    const people = detections.map((d, idx) => {
      const cx = d.x + d.w / 2;
      const cy = d.y + d.h / 2;

      return {
        id: idx + 1,
        bbox: {
          x: Math.round(d.x),
          y: Math.round(d.y),
          w: Math.round(d.w),
          h: Math.round(d.h),
        },
        centroid: {
          x: Number(normalize(cx, FRAME_WIDTH).toFixed(2)),
          y: Number(normalize(cy, FRAME_HEIGHT).toFixed(2)),
        },
      };
    });

    const distance = computeDistance(detections);

    const riskData = computeRisk({
      fall_detected,
      motion_score,
      num_people: detections.length,
      distance,
    });

    res.json({
      summary: {
        num_people: detections.length,
        risk: riskData.risk,
        score: riskData.score,
        action: riskData.action,
      },
      metrics: {
        min_distance: Number(distance.toFixed(3)),
        motion_score,
        fall_detected,
      },
      people,
      debug: {
        image: yoloRes.image || null,
        raw_detections: detections,
      },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};