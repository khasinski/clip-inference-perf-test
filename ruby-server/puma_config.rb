# Puma configuration optimized for CPU-bound ONNX inference
# Multi-process to bypass GIL, moderate threads per worker

# Single process mode (multi-worker had port binding issues)
# Testing with high thread count for better concurrency
workers 0

# Increased threads to handle more concurrent requests
# Even with GIL, helps with I/O overhead (HTTP, JSON parsing)
threads 8, 32

# Port and binding
bind 'tcp://0.0.0.0:8003'

# Worker timeout (in seconds)
worker_timeout 60

# Restart workers after this many requests (to prevent memory leaks)
worker_boot_timeout 60

on_worker_boot do
  puts "⚡ Puma worker #{Process.pid} started (multi-process mode)"
end
