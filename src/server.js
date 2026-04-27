const express = require("express");
const cors = require("cors");

const analyzeRoute = require("./routes/analyze");

const app = express();
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
app.options("*", cors(corsOptions));
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

// Start server
const PORT = Number(process.env.PORT || 5500);
const HOST = process.env.HOST || "0.0.0.0";

app.listen(PORT, HOST, () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
});