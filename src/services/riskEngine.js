// src/services/riskEngine.js

/**
 * Maintains short history of scores to smooth fluctuations
 */
let history = [];

/**
 * Smooths score over last N frames
 */
const smoothScore = (newScore) => {
  history.push(newScore);

  // Keep last 5 frames
  if (history.length > 5) {
    history.shift();
  }

  const avg =
    history.reduce((sum, val) => sum + val, 0) / history.length;

  return avg;
};

/**
 * Main risk computation function
 */
exports.computeRisk = ({
  fall_detected = false,
  motion_score = 0,
  num_people = 0,
  distance = 1,
}) => {
  let score = 0;

// 🧍 Medical emergency
if (num_people === 1 && fall_detected) {
  score += 6;
}

// ⚠️ Two-person close proximity
if (num_people === 2 && distance < 0.2) {
  score += 3;
}

// 👥 Crowding scenario (NEW)
if (num_people >= 3) {
  score += 2;

  if (distance < 0.25) {
    score += 2; // tighter crowd = more risk
  }
}

if (num_people >= 4) {
  score += 3; // overcrowding alert
}

// 🧠 Motion anomaly
if (motion_score > 0.7) {
  score += 2;
}

// 🚨 Combined suspicious behavior
if (num_people === 2 && distance < 0.15 && motion_score > 0.6) {
  score += 2;
}

  // Apply smoothing
  score = smoothScore(score);

  // 🎯 Convert score → risk level
  let risk = "LOW";
  let action = "MONITOR";

  if (score >= 7) {
    risk = "HIGH";
    action = "STOP_LIFT";
  } else if (score >= 4) {
    risk = "MEDIUM";
    action = "ALERT_STAFF";
  }

  return {
    risk,
    action,
    score: Number(score.toFixed(2)), // cleaner output
  };
};