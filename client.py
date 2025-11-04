"""
Simple client for the fast inference server
"""
import requests
import numpy as np
from typing import List, Union

class FastClipClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self._check_health()

    def _check_health(self):
        """Check if server is ready"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            data = response.json()
            print(f"✓ Server ready ({data.get('provider', 'unknown')})")
        except Exception as e:
            print(f"⚠️  Server not reachable: {e}")

    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Encode text(s) to embeddings

        Args:
            texts: Single text or list of texts
            normalize: L2 normalize embeddings (required for similarity)

        Returns:
            numpy array of shape (num_texts, 768)
        """
        if isinstance(texts, str):
            texts = [texts]

        response = requests.post(
            f"{self.base_url}/encode",
            json={"texts": texts, "normalize": normalize},
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        return np.array(data["embeddings"])

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        return float(np.dot(emb1[0], emb2[0]))

# Usage examples
if __name__ == "__main__":
    client = FastClipClient()

    # Single text
    print("\n1. Single text encoding:")
    emb = client.encode("Hello world")
    print(f"   Shape: {emb.shape}")
    print(f"   First 5 values: {emb[0][:5]}")

    # Batch (MUCH faster!)
    print("\n2. Batch encoding:")
    texts = [
        "A cat sitting on a mat",
        "A dog playing in the park",
        "Machine learning is fascinating",
        "Deep neural networks",
    ]
    embeddings = client.encode(texts)
    print(f"   Shape: {embeddings.shape}")

    # Similarity
    print("\n3. Text similarity:")
    sim1 = client.similarity("cat on mat", "feline on carpet")
    sim2 = client.similarity("cat on mat", "machine learning")
    print(f"   'cat on mat' vs 'feline on carpet': {sim1:.4f}")
    print(f"   'cat on mat' vs 'machine learning': {sim2:.4f}")

    # Multilingual (M-CLIP supports 48 languages!)
    print("\n4. Multilingual:")
    multilingual = [
        "Hello world",      # English
        "Bonjour le monde", # French
        "Hola mundo",       # Spanish
        "你好世界",          # Chinese
        "こんにちは世界",     # Japanese
    ]
    multi_emb = client.encode(multilingual)
    print(f"   Shape: {multi_emb.shape}")

    # Check similarity between English and other languages
    en_emb = multi_emb[0]
    for i, text in enumerate(multilingual[1:], 1):
        sim = np.dot(en_emb, multi_emb[i])
        print(f"   EN-{text[:10]}: {sim:.4f}")
