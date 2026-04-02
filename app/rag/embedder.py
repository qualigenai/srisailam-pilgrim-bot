from sentence_transformers import SentenceTransformer
from app.utils.config import EMBEDDING_MODEL
import logging

logger = logging.getLogger(__name__)

model = SentenceTransformer(EMBEDDING_MODEL)

def embed_texts(texts: list[str]):
    logger.info(f"🔢 Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)
    logger.info("✅ Embedding complete")
    return embeddings