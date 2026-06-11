import numpy as np
from typing import List, Optional


class SemanticEmbedder:
    """
    Uses sentence-transformers for high-quality semantic embeddings.
    Specifically tuned for F1 domain knowledge.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            print(f"✅ Loaded embedding model: {model_name}")
        except ImportError:
            print("❌ sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model = None

    def embed_text(self, text: str) -> Optional[List[float]]:
        """Embed a single text string into a dense vector."""
        if not self.model:
            return None
        return self.model.encode(text, convert_to_tensor=False).tolist()

    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Embed multiple texts at once."""
        if not self.model:
            return None
        return self.model.encode(texts, convert_to_tensor=False).tolist()

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not embedding1 or not embedding2:
            return 0.0
        arr1 = np.array(embedding1)
        arr2 = np.array(embedding2)
        return float(np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2) + 1e-8))


def embed_text(text: str):
    """Return embedding vector for `text`."""
    embedder = SemanticEmbedder()
    return embedder.embed_text(text)
