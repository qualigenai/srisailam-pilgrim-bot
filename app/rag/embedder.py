import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, model_name: str = None):
        self.model = None
        self._load_model(model_name)

    def _load_model(self, model_name=None):
        try:
            from sentence_transformers import SentenceTransformer
            name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
            self.model = SentenceTransformer(name, device="cpu")
            logger.info(f"✅ Model loaded: {name}")
        except ImportError:
            logger.warning("⚠️ sentence-transformers not installed — embedding disabled")
            self.model = None

    def embed_text(self, text: str) -> np.ndarray:
        if self.model is None:
            return np.random.rand(384)
        if not text or not text.strip():
            return np.zeros(384)
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts, batch_size=32):
        if self.model is None:
            return np.random.rand(len(texts), 384)
        texts = [t for t in texts if t and t.strip()]
        if not texts:
            return np.array([])
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )

    def get_embedding_dimension(self):
        return 384