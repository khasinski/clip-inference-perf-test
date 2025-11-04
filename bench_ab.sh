#!/bin/bash
#
# Apache Benchmark (ab) script for fast-clip inference
# Note: ab has limitations with POST data, so this is a simplified version
#

set -e

URL="${1:-http://localhost:8000/encode}"
REQUESTS="${2:-100}"
CONCURRENCY="${3:-10}"

# Create test payload
PAYLOAD='{"texts":["Hello world","Machine learning","Natural language processing","Computer vision"],"normalize":true}'

# Save payload to temp file
TEMP_FILE=$(mktemp)
echo "$PAYLOAD" > "$TEMP_FILE"

echo "=================================="
echo "Apache Benchmark Test"
echo "=================================="
echo "URL:         $URL"
echo "Requests:    $REQUESTS"
echo "Concurrency: $CONCURRENCY"
echo "Payload:     $PAYLOAD"
echo "=================================="
echo ""

# Run Apache Benchmark
ab \
  -n "$REQUESTS" \
  -c "$CONCURRENCY" \
  -p "$TEMP_FILE" \
  -T "application/json" \
  -H "Content-Type: application/json" \
  "$URL"

# Cleanup
rm -f "$TEMP_FILE"

echo ""
echo "=================================="
echo "Test complete!"
echo "=================================="
