// src/services/proximityService.js

const FRAME_WIDTH = 640;
const FRAME_HEIGHT = 480;

const normalize = (val, max) => val / max;

const getCentroids = (detections) => {
  return detections.map(d => ({
    x: normalize(d.x + d.w / 2, FRAME_WIDTH),
    y: normalize(d.y + d.h / 2, FRAME_HEIGHT)
  }));
};

exports.computeDistance = (detections) => {
  if (detections.length < 2) return 1;

  const centroids = getCentroids(detections);

  let minDist = Infinity;

  for (let i = 0; i < centroids.length; i++) {
    for (let j = i + 1; j < centroids.length; j++) {
      const dx = centroids[i].x - centroids[j].x;
      const dy = centroids[i].y - centroids[j].y;

      const dist = Math.sqrt(dx * dx + dy * dy);
      minDist = Math.min(minDist, dist);
    }
  }

  return minDist;
};