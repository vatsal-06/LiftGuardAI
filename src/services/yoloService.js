const axios = require("axios");

const YOLO_SERVICE_URL =
  process.env.YOLO_SERVICE_URL || "http://localhost:8000/detect";

exports.getDetections = async (base64Image, fallDetected, motionScore) => {
  const res = await axios.post(
    YOLO_SERVICE_URL,
    {
      image: base64Image,
      fall_detected: Boolean(fallDetected),
      motion_score: Number(motionScore || 0),
    },
    { timeout: 3000 }
  );

  // return full payload, not just detections
  return res.data;
};