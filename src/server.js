const express = require("express");
const cors = require("cors");

const analyzeRoute = require("./routes/analyze");

const app = express();

// Middleware
app.use(cors());
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
const PORT = 5500;

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});