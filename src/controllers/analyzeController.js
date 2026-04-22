const { getDetections } = require("../services/yoloService");
const { computeDistance } = require("../services/proximityService");
const { computeRisk } = require("../services/riskEngine");
const { cleanDetections } = require("../services/detectionService");

const FRAME_WIDTH = 640;
const FRAME_HEIGHT = 480;

const normalize = (val, max) => val / max;

exports.analyze = async (req, res) => {
  try {
    const { image, fall_detected, motion_score } = req.body;

    const yoloRes = await getDetections(image);

    let detections = cleanDetections(yoloRes.detections || []);

    // build people array
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