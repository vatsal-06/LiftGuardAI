const axios = require("axios");

exports.getDetections = async (base64Image) => {
  const res = await axios.post(
    "http://localhost:8000/detect",
    { image: base64Image },
    { timeout: 3000 }
  );

  // return full payload, not just detections
  return res.data; 
};