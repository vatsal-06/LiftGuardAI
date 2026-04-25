const axios = require("axios");

exports.getDetections = async (base64Image, fallDetected, motionScore) => {
  const res = await axios.post(
    "http://localhost:8000/detect",
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