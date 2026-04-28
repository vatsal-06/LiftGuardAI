const express = require("express");
const cors = require("cors");

const analyzeRoute = require("./routes/analyze");

const app = express();
const YOLO_SERVICE_URL = process.env.YOLO_SERVICE_URL || "http://localhost:8000/detect";
const MEDIAPIPE_SERVICE_URL =
  process.env.MEDIAPIPE_SERVICE_URL || "http://localhost:8001/mediapipe";
const YOLO_SERVICE_TIMEOUT_MS = Number(process.env.YOLO_SERVICE_TIMEOUT_MS || 60000);
const YOLO_SERVICE_RETRIES = Number(process.env.YOLO_SERVICE_RETRIES || 2);
const MEDIAPIPE_SERVICE_TIMEOUT_MS = Number(
  process.env.MEDIAPIPE_SERVICE_TIMEOUT_MS || 60000
);
const MEDIAPIPE_SERVICE_RETRIES = Number(
  process.env.MEDIAPIPE_SERVICE_RETRIES || 2
);
const ALLOWED_ORIGINS = (process.env.CORS_ORIGIN || "*")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const corsOptions = {
  origin: ALLOWED_ORIGINS.includes("*") ? true : ALLOWED_ORIGINS,
  methods: ["GET", "POST", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
};

// Middleware
app.use(cors(corsOptions));
app.use(express.json({ limit: "10mb" })); // important for base64

app.use((req, res, next) => {
  console.log("Incoming:", req.method, req.url);
  next();
});

// Routes
app.use("/api", analyzeRoute);

// Debug route
app.get("/debug", (req, res) => {
  res.json({ message: "Server is running" });
});

app.get("/debug/config", (req, res) => {
  res.json({
    yolo_service_url: YOLO_SERVICE_URL,
    mediapipe_service_url: MEDIAPIPE_SERVICE_URL,
    yolo_service_timeout_ms: YOLO_SERVICE_TIMEOUT_MS,
    yolo_service_retries: YOLO_SERVICE_RETRIES,
    mediapipe_service_timeout_ms: MEDIAPIPE_SERVICE_TIMEOUT_MS,
    mediapipe_service_retries: MEDIAPIPE_SERVICE_RETRIES,
    cors_origin: process.env.CORS_ORIGIN || "*",
    port: PORT,
  });
});

// Start server
const PORT = Number(process.env.PORT || 5500);
const HOST = process.env.HOST || "0.0.0.0";

app.listen(PORT, HOST, () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
});