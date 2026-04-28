const axios = require("axios");

const YOLO_SERVICE_URL =
  process.env.YOLO_SERVICE_URL || "http://localhost:8000/detect";
const YOLO_SERVICE_TIMEOUT_MS = Number(process.env.YOLO_SERVICE_TIMEOUT_MS || 60000);
const YOLO_SERVICE_RETRIES = Number(process.env.YOLO_SERVICE_RETRIES || 2);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const isRetryableError = (err) =>
  err.code === "ECONNABORTED" ||
  err.code === "ETIMEDOUT" ||
  err.code === "ECONNRESET" ||
  !err.response;

exports.getDetections = async (base64Image, fallDetected, motionScore) => {
  let lastError;

  for (let attempt = 0; attempt <= YOLO_SERVICE_RETRIES; attempt += 1) {
    try {
      const res = await axios.post(
        YOLO_SERVICE_URL,
        {
          image: base64Image,
          fall_detected: Boolean(fallDetected),
          motion_score: Number(motionScore || 0),
        },
        { timeout: YOLO_SERVICE_TIMEOUT_MS }
      );

      // return full payload, not just detections
      return res.data;
    } catch (err) {
      lastError = err;

      if (attempt >= YOLO_SERVICE_RETRIES || !isRetryableError(err)) {
        throw err;
      }

      const backoffMs = 500 * Math.pow(2, attempt);
      await sleep(backoffMs);
    }
  }

  throw lastError;
};