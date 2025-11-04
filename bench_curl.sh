#!/bin/bash
#
# Simple curl-based benchmark for fast-clip
# Quick and dirty performance test without external dependencies
#

URL="${1:-http://localhost:8000/encode}"
ITERATIONS="${2:-100}"

echo "=================================="
echo "CURL Benchmark"
echo "=================================="
echo "URL:        $URL"
echo "Iterations: $ITERATIONS"
echo "=================================="
echo ""

# Create test payload
PAYLOAD='{"texts":["Hello world","Machine learning","Natural language processing","Computer vision"],"normalize":true}'

# Warmup
echo "Warming up..."
for i in {1..5}; do
    curl -s -X POST "$URL" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" > /dev/null
done

echo "Running benchmark..."

# Run benchmark
TIMES_FILE=$(mktemp)

for i in $(seq 1 $ITERATIONS); do
    # Use curl's time_total output
    TIME=$(curl -s -X POST "$URL" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        -w "%{time_total}\n" \
        -o /dev/null)

    echo "$TIME" >> "$TIMES_FILE"

    # Progress
    if [ $((i % 10)) -eq 0 ]; then
        echo "Progress: $i/$ITERATIONS" >&2
    fi
done

echo "" >&2
echo "Calculating statistics..." >&2

# Calculate statistics using Python (more portable than awk on macOS)
python3 - "$TIMES_FILE" << 'PYEOF'
import sys
import statistics

with open(sys.argv[1]) as f:
    times = [float(line.strip()) for line in f if line.strip()]

if not times:
    print("No data collected!")
    sys.exit(1)

times_sorted = sorted(times)
count = len(times)
mean = statistics.mean(times)
median = statistics.median(times)
stdev = statistics.stdev(times) if count > 1 else 0

def percentile(data, p):
    index = int(len(data) * p)
    return data[min(index, len(data)-1)]

print("==================================")
print("RESULTS")
print("==================================")
print(f"Requests:     {count}")
print(f"Mean:         {mean*1000:.2f}ms")
print(f"Median:       {median*1000:.2f}ms")
print(f"Min:          {min(times)*1000:.2f}ms")
print(f"Max:          {max(times)*1000:.2f}ms")
print(f"Std Dev:      {stdev*1000:.2f}ms")
print(f"p95:          {percentile(times_sorted, 0.95)*1000:.2f}ms")
print(f"p99:          {percentile(times_sorted, 0.99)*1000:.2f}ms")
print(f"Throughput:   {1/mean:.2f} req/s")
print("==================================")
PYEOF

# Cleanup
rm -f "$TIMES_FILE"
