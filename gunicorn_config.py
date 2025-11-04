"""
Gunicorn configuration for production deployment
Alternative to uvicorn for better process management

Usage:
    gunicorn -c gunicorn_config.py fast_onnx_server:app
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKERS", "1"))  # Each worker loads model (~2GB RAM)
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000  # Restart workers after N requests (helps with memory leaks)
max_requests_jitter = 1000
timeout = 120  # Timeout for long requests
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Performance
preload_app = False  # Can't preload with lifespan events
worker_tmp_dir = "/dev/shm"  # Use RAM for worker heartbeat (faster than disk)

# Process naming
proc_name = "fast-clip-server"

def on_starting(server):
    print("🚀 Starting Fast-CLIP Server with Gunicorn")
    print(f"   Workers: {workers}")
    print(f"   Connections per worker: {worker_connections}")
    print(f"   Total capacity: {workers * worker_connections} concurrent requests")

def worker_int(worker):
    print(f"⚠️  Worker {worker.pid} received interrupt signal")

def worker_abort(worker):
    print(f"❌ Worker {worker.pid} aborted")
