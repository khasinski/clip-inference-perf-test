"""
Ultra-fast ONNX-based inference server
Uses ONNX Runtime with all optimizations enabled
"""
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
from contextlib import asynccontextmanager
import transformers
from pathlib import Path

# Global cache
model_cache = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ONNX model on startup"""
    print("Loading ONNX model...")

    model_dir = Path("./model")
    model_path = model_dir / "model_quantized.onnx"

    if not model_path.exists():
        print("❌ Model not found! Run convert_to_onnx.py first")
        raise RuntimeError("Model not found")

    # ONNX Runtime with maximum optimizations
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    # Optimize thread count based on CPU
    import os
    num_threads = max(1, os.cpu_count() // 2)
    sess_options.intra_op_num_threads = num_threads
    sess_options.inter_op_num_threads = num_threads

    # Enable memory optimization
    sess_options.enable_mem_pattern = True
    sess_options.enable_cpu_mem_arena = True

    # Use optimized CPU execution
    # CPU with quantized ONNX model is very fast on modern hardware
    print("⚡ Using optimized CPU execution")
    providers = ['CPUExecutionProvider']

    session = ort.InferenceSession(
        str(model_path),
        sess_options=sess_options,
        providers=providers
    )

    # Load tokenizer - try multiple methods for compatibility
    try:
        # First try: Load from model name if available
        import json
        model_info_path = model_dir / "model_info.json"
        if model_info_path.exists():
            with open(model_info_path) as f:
                info = json.load(f)
                tokenizer = transformers.AutoTokenizer.from_pretrained(info["model_name"])
                print("✓ Tokenizer loaded from HuggingFace")
        else:
            raise FileNotFoundError("model_info.json not found")
    except Exception as e:
        # Fallback: Try loading from local files
        print(f"⚠️  Loading from HuggingFace failed ({e}), trying local files...")
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            str(model_dir),
            use_fast=True,
            local_files_only=False
        )

    model_cache["session"] = session
    model_cache["tokenizer"] = tokenizer
    model_cache["provider"] = session.get_providers()[0]

    print(f"✓ Model loaded with {model_cache['provider']}")
    yield

    model_cache.clear()

app = FastAPI(lifespan=lifespan, title="Ultra-Fast M-CLIP ONNX Inference")

class TextRequest(BaseModel):
    texts: List[str]
    normalize: bool = True

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    shape: List[int]

@app.post("/encode", response_model=EmbeddingResponse)
async def encode_texts(request: TextRequest):
    """
    Blazing fast text encoding with ONNX Runtime

    Optimizations:
    - Quantized INT8 model
    - ONNX Runtime graph optimizations
    - Batch processing
    - Async execution (non-blocking for high concurrency)
    - Thread pool for CPU-bound work
    """
    try:
        session = model_cache["session"]
        tokenizer = model_cache["tokenizer"]

        # Run CPU-bound work in thread pool to avoid blocking event loop
        # This allows handling many concurrent requests
        import asyncio
        loop = asyncio.get_event_loop()

        def inference():
            """CPU-bound inference work"""
            # Tokenize
            inputs = tokenizer(
                request.texts,
                padding=True,
                truncation=True,
                return_tensors="np"  # Return numpy directly for ONNX
            )

            # Run inference
            ort_inputs = {
                'input_ids': inputs['input_ids'].astype(np.int64),
                'attention_mask': inputs['attention_mask'].astype(np.int64)
            }

            embeddings = session.run(None, ort_inputs)[0]

            # Normalize if requested
            if request.normalize:
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

            return embeddings

        # Run in thread pool to allow other requests to be processed concurrently
        embeddings = await loop.run_in_executor(None, inference)

        return EmbeddingResponse(
            embeddings=embeddings.tolist(),
            shape=list(embeddings.shape)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Check if model is loaded"""
    if "session" in model_cache:
        return {
            "status": "ready",
            "provider": model_cache["provider"]
        }
    return {"status": "loading"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Fast M-CLIP ONNX Inference Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--workers', type=int, default=1,
                        help='Number of worker processes (each loads model separately)')
    parser.add_argument('--limit-concurrency', type=int, default=100,
                        help='Maximum concurrent connections')
    parser.add_argument('--backlog', type=int, default=2048,
                        help='Maximum queued connections')
    parser.add_argument('--timeout-keep-alive', type=int, default=5,
                        help='Keep-alive timeout in seconds')

    args = parser.parse_args()

    print(f"🚀 Starting Fast-CLIP server with:")
    print(f"   Workers: {args.workers}")
    print(f"   Max concurrent connections: {args.limit_concurrency}")
    print(f"   Connection backlog: {args.backlog}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        limit_concurrency=args.limit_concurrency,
        backlog=args.backlog,
        timeout_keep_alive=args.timeout_keep_alive,
        log_level="info"
    )
