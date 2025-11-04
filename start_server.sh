#!/bin/bash
#
# Start Fast-CLIP server with optimized settings
#

# Default configuration - optimized for M1 Mac
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"  # 1 worker recommended (each loads model into memory)
CONCURRENCY="${CONCURRENCY:-200}"  # Max concurrent connections
BACKLOG="${BACKLOG:-2048}"  # Connection queue size

echo "🚀 Starting Fast-CLIP Server"
echo "================================"
echo "Host:              $HOST"
echo "Port:              $PORT"
echo "Workers:           $WORKERS"
echo "Max Concurrency:   $CONCURRENCY"
echo "Backlog:           $BACKLOG"
echo "================================"
echo ""
echo "💡 Tip: Each worker loads the model (~2GB RAM)"
echo "   Single worker with high concurrency is usually best"
echo ""

python3 fast_onnx_server.py \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --limit-concurrency "$CONCURRENCY" \
    --backlog "$BACKLOG"
