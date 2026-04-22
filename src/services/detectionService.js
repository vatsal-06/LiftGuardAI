const FRAME_WIDTH = 640; // adjust if needed

const isMirrorPair = (d1, d2) => {
  // similar size
  const sizeSimilar =
    Math.abs(d1.w - d2.w) < 40 &&
    Math.abs(d1.h - d2.h) < 60;

  // roughly same vertical alignment
  const yAligned =
    Math.abs(d1.y - d2.y) < 80;

  // symmetric across center (mirror effect)
  const center1 = d1.x + d1.w / 2;
  const center2 = d2.x + d2.w / 2;

  const symmetric =
    Math.abs(center1 + center2 - FRAME_WIDTH) < 100;

  return sizeSimilar && yAligned && symmetric;
};

exports.cleanDetections = (detections) => {
  if (!detections || detections.length === 0) return [];

  // remove tiny noise
  let filtered = detections.filter(d => d.w > 40 && d.h > 80);

  const result = [];
  const used = new Set();

  for (let i = 0; i < filtered.length; i++) {
    if (used.has(i)) continue;

    let isReflection = false;

    for (let j = i + 1; j < filtered.length; j++) {
      if (used.has(j)) continue;

      if (isMirrorPair(filtered[i], filtered[j])) {
        // keep only one (arbitrary: keep left one)
        const keep =
          filtered[i].x < filtered[j].x ? i : j;

        const drop =
          keep === i ? j : i;

        used.add(drop);
        isReflection = true;
      }
    }

    if (!used.has(i)) {
      result.push(filtered[i]);
    }
  }

  // limit to realistic lift capacity
  return result.slice(0, 4);
};