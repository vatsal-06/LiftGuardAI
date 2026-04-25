exports.computeRisk = ({
    fall_detected = false,
    motion_score = 0,
    num_people = 0,
    distance = 1,
}) => {
    let score = 0;

    if (fall_detected) score += 6;

    if (num_people >= 2 && distance < 0.2) score += 3;

    if (motion_score > 0.7) score += 2;

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
        score,
        action,
    };
};
