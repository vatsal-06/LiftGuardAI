const express = require("express");
const router = express.Router();

const { analyze } = require("../controllers/analyzeController");

router.post("/analyze", analyze);

module.exports = router;