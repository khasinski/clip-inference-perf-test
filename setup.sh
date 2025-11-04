#!/bin/bash

set -e

echo "⚡ Fast-CLIP Setup Script"
echo "========================"
echo ""

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"
echo "🖥️  Detected: $OS $ARCH"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Mac-specific setup
if [[ "$OS" == "Darwin" ]]; then
    echo "✓ macOS detected"

    # Check for Homebrew (optional but recommended)
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew not found. Install from https://brew.sh for easier dependency management"
    fi
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Convert model
echo ""
echo "🔄 Converting model to ONNX (this may take a few minutes)..."
python3 convert_to_onnx.py

echo ""
echo "✅ Setup complete!"
echo ""

# Mac-specific recommendations
if [[ "$OS" == "Darwin" ]]; then
    echo "🍎 macOS Tips:"
    if [[ "$ARCH" == "arm64" ]]; then
        echo "  • You're on Apple Silicon! For even better performance:"
        echo "    pip3 install onnxruntime-coreml"
    fi
    echo "  • See MACOS.md for detailed Mac instructions"
    echo ""
fi

echo "🚀 To start the server:"
echo ""
echo "  Basic:                    python3 fast_onnx_server.py"
echo "  High concurrency:         python3 fast_onnx_server.py --limit-concurrency 200"
echo "  With script:              ./start_server.sh"
echo ""
echo "📊 To benchmark:            python3 benchmark.py"
echo "🧪 To test:                 python3 client.py"
echo ""
