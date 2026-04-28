#!/bin/bash

VIDEO=${1:-test_videos/fall.mp4}
API_URL="http://localhost:8000/process-video"

echo "Encoding video..."

BASE64=$(base64 "$VIDEO")

echo "Creating JSON payload..."

echo "{\"video\":\"$BASE64\"}" > payload.json

echo "Sending request..."

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  --data-binary @payload.json \
  -o response.json

echo "Done."