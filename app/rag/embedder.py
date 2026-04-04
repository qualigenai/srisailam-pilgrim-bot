import os
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Inline settings instead of src.core.config
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CACHE_DIR = "embeddings_cache"

class EmbeddingManager:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self.cache_dir = EMBEDDING_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(
            self.model_name,
            cache_folder=self.cache_dir,
            device="cpu"
        )
        logger.info(f"Model loaded. Dim: {self.model.get_sentence_embedding_dimension()}")

    def embed_text(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return np.zeros(self.model.get_sentence_embedding_dimension())
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        texts = [t for t in texts if t and t.strip()]
        if not texts:
            return np.array([])
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )

    def get_embedding_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()