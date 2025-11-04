"""
Download M-CLIP model and convert to optimized ONNX format
"""
import torch
import torch.nn as nn
import transformers
from multilingual_clip import pt_multilingual_clip
from pathlib import Path
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType
import onnxruntime as ort

class TextEncoderWrapper(nn.Module):
    """Wrapper that takes tokenized inputs directly, not raw text"""
    def __init__(self, text_model):
        super().__init__()
        self.transformer = text_model.transformer
        self.LinearTransformation = text_model.LinearTransformation

    def forward(self, input_ids, attention_mask):
        embs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)[0]
        embs = (embs * attention_mask.unsqueeze(2)).sum(dim=1) / attention_mask.sum(dim=1)[:, None]
        return self.LinearTransformation(embs)

def download_and_convert():
    """Download model and convert to ONNX with optimizations"""

    model_name = 'M-CLIP/XLM-Roberta-Large-Vit-B-32'
    output_dir = Path("./model")
    output_dir.mkdir(exist_ok=True)

    print("📦 Downloading M-CLIP model...")
    mclip_model = pt_multilingual_clip.MultilingualCLIP.from_pretrained(model_name)
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)

    # Wrap the model to accept tokenized inputs
    model = TextEncoderWrapper(mclip_model)
    model.eval()
    torch.set_grad_enabled(False)

    # Save tokenizer (use legacy=True for better compatibility)
    tokenizer.save_pretrained(str(output_dir), legacy_format=True)
    print("✓ Tokenizer saved")

    # Also save the model name for easy reloading
    import json
    with open(output_dir / "model_info.json", "w") as f:
        json.dump({"model_name": model_name}, f)
    print("✓ Model info saved")

    # Create dummy input for ONNX export
    dummy_text = "Hello world"
    inputs = tokenizer(dummy_text, return_tensors="pt", padding=True, truncation=True)

    print("🔄 Converting to ONNX...")
    onnx_path = output_dir / "model.onnx"

    torch.onnx.export(
        model,
        (inputs['input_ids'], inputs['attention_mask']),
        str(onnx_path),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input_ids', 'attention_mask'],
        output_names=['embeddings'],
        dynamic_axes={
            'input_ids': {0: 'batch_size', 1: 'sequence'},
            'attention_mask': {0: 'batch_size', 1: 'sequence'},
            'embeddings': {0: 'batch_size'}
        }
    )
    print(f"✓ ONNX model saved to {onnx_path}")

    # Validate ONNX model (skip full load since model is >2GB)
    print("🔍 Validating ONNX model...")
    try:
        onnx.checker.check_model(str(onnx_path))
        print("✓ ONNX model is valid")
    except ValueError as e:
        if "too large" in str(e):
            print("✓ ONNX model created (too large for full validation, but this is OK)")
        else:
            raise

    # Quantize for faster inference (INT8)
    print("⚡ Quantizing model for faster inference...")
    quantized_path = output_dir / "model_quantized.onnx"
    quantize_dynamic(
        str(onnx_path),
        str(quantized_path),
        weight_type=QuantType.QInt8
    )
    print(f"✓ Quantized model saved to {quantized_path}")

    # Test inference speed
    print("\n📊 Testing inference speed...")

    # Test original ONNX
    session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])
    test_inputs = {
        'input_ids': inputs['input_ids'].numpy(),
        'attention_mask': inputs['attention_mask'].numpy()
    }

    import time
    start = time.perf_counter()
    for _ in range(100):
        session.run(None, test_inputs)
    elapsed = time.perf_counter() - start
    print(f"Original ONNX: {elapsed/100*1000:.2f}ms per inference")

    # Test quantized
    session_quant = ort.InferenceSession(str(quantized_path), providers=['CPUExecutionProvider'])
    start = time.perf_counter()
    for _ in range(100):
        session_quant.run(None, test_inputs)
    elapsed = time.perf_counter() - start
    print(f"Quantized ONNX: {elapsed/100*1000:.2f}ms per inference")

    print("\n✅ Done! Use 'model_quantized.onnx' for fastest inference")

    # Print model info
    print(f"\nModel files:")
    for file in output_dir.iterdir():
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  {file.name}: {size_mb:.1f} MB")

if __name__ == "__main__":
    download_and_convert()
