#!/bin/bash
# Test script for /process-video endpoint using curl
# Usage: ./test_video_curl.sh [video_file]

set -e

API_URL="http://localhost:8000/process-video"
VIDEO_FILE="${1:-test_videos/fall.mp4}"
OUTPUT_FILE="response.json"
OUTPUT_VIDEO="annotated_video.mp4"

echo "=================================================="
echo "LiftGuardAI Video Processing Test (curl)"
echo "=================================================="
echo ""

# Check if FastAPI is running
echo "📡 Checking if API is running on :8000..."
if ! curl -s -m 2 http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "❌ API is not running on http://localhost:8000"
    echo ""
    echo "Start the server with:"
    echo "  uvicorn yolo_service:app --host 0.0.0.0 --port 8000"
    exit 1
fi
echo "✅ API is running"
echo ""

# Check if video file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "❌ Video file not found: $VIDEO_FILE"
    echo ""
    echo "Available videos:"
    ls -lh test_videos/
    exit 1
fi

# Get file size
FILE_SIZE=$(stat -f%z "$VIDEO_FILE" 2>/dev/null || stat -c%s "$VIDEO_FILE" 2>/dev/null)
FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc)
echo "📹 Video: $VIDEO_FILE"
echo "📊 Size: ${FILE_SIZE_MB}MB"
echo ""

# Encode video to base64
echo "⏳ Encoding video to base64..."
VIDEO_BASE64=$(base64 < "$VIDEO_FILE" | tr -d '\n')
echo "✅ Encoded (${#VIDEO_BASE64} chars)"
echo ""

# Send request
echo "🚀 Sending POST request to /process-video..."
echo "   URL: $API_URL"
echo "   Timeout: 300 seconds (5 min)"
echo ""

START_TIME=$(date +%s)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"video\": \"$VIDEO_BASE64\",
    \"filename\": \"$(basename $VIDEO_FILE)\"
  }" \
  -o "$OUTPUT_FILE" \
  --max-time 300 \
  -w "\n✅ Response Status: %{http_code}\n"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "⏱️  Processing took ${DURATION}s"
echo ""

# Check if response is valid JSON
if ! jq empty "$OUTPUT_FILE" 2>/dev/null; then
    echo "❌ Response is not valid JSON"
    echo ""
    echo "Raw response:"
    cat "$OUTPUT_FILE"
    exit 1
fi

# Print summary
echo "=================================================="
echo "Video Processing Results"
echo "=================================================="
echo ""

STATUS=$(jq -r '.status' "$OUTPUT_FILE")
echo "Status: $STATUS"
echo ""

if [ "$STATUS" = "success" ]; then
    echo "✅ Processing succeeded!"
    echo ""
    
    # Extract and display summary
    SUMMARY=$(jq '.summary' "$OUTPUT_FILE")
    echo "📊 Video Summary:"
    echo "   Total Frames: $(echo $SUMMARY | jq '.total_frames')"
    echo "   Duration: $(echo $SUMMARY | jq '.duration_sec')s"
    echo "   FPS: $(echo $SUMMARY | jq '.fps')"
    echo "   Resolution: $(echo $SUMMARY | jq -r '.video_resolution | "\(.width)x\(.height)"')"
    echo ""
    
    echo "🎯 Detection Results:"
    echo "   Falls Detected: $(echo $SUMMARY | jq '.total_falls_detected')"
    echo "   Fall Frames: $(echo $SUMMARY | jq '.fall_frames')"
    echo "   People in Video: $(echo $SUMMARY | jq '.people_in_video')"
    echo "   Frames with People: $(echo $SUMMARY | jq '.frames_with_people')"
    echo ""
    
    echo "📈 Motion Analysis:"
    echo "   Avg Motion: $(echo $SUMMARY | jq '.avg_motion_score')"
    echo "   Max Motion: $(echo $SUMMARY | jq '.max_motion_score')"
    echo ""
    
    # Extract and save annotated video
    VIDEO_B64=$(jq -r '.video' "$OUTPUT_FILE")
    echo "💾 Saving annotated video..."
    echo "$VIDEO_B64" | base64 -D > "$OUTPUT_VIDEO"
    echo "✅ Saved: $OUTPUT_VIDEO ($(stat -f%z "$OUTPUT_VIDEO" 2>/dev/null || stat -c%s "$OUTPUT_VIDEO" 2>/dev/null | numfmt --to=iec-i --suffix=B 2>/dev/null || stat -c%s "$OUTPUT_VIDEO" 2>/dev/null))"
    echo ""
    
    # Show first few metrics
    echo "📋 Sample Frame Metrics (first 5 frames):"
    jq '.metrics[0:5]' "$OUTPUT_FILE" | head -20
    echo ""
    
else
    echo "❌ Processing failed"
    echo ""
    echo "Error response:"
    jq '.' "$OUTPUT_FILE"
    exit 1
fi

echo "=================================================="
echo "✅ Test Complete!"
echo "   Full response saved to: $OUTPUT_FILE"
echo "   Annotated video saved to: $OUTPUT_VIDEO"
echo "=================================================="
