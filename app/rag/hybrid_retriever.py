from typing import List, Dict
import logging
import pickle
import os
from app.rag.embedder import EmbeddingManager
from app.rag.vector_db import VectorDBManager
from app.rag.bm25_search import BM25Retriever
from app.utils.config import KNOWLEDGE_BASE_PROCESSED

logger = logging.getLogger(__name__)

RETRIEVER_CACHE = os.path.join(KNOWLEDGE_BASE_PROCESSED, "retriever.pkl")

class HybridRetriever:
    def __init__(self, embedding_dim: int = 384):
        self.embedder = EmbeddingManager()
        self.vector_db = VectorDBManager(embedding_dim=embedding_dim)
        self.bm25 = BM25Retriever()
        self.documents = []

    def index_documents(self, documents: List[Dict]):
        self.documents = documents
        texts = [doc["text"] for doc in documents]

        logger.info("🔢 Generating embeddings...")
        embeddings = self.embedder.embed_batch(texts)

        logger.info("💾 Storing in vector DB...")
        self.vector_db.upsert_documents(documents, embeddings)

        logger.info("📝 Indexing BM25...")
        self.bm25.index(documents)

        logger.info(f"✅ Indexed {len(documents)} documents")

        # Save to disk
        self._save()

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        # Vector search
        query_embedding = self.embedder.embed_text(query).tolist()
        vector_results = self.vector_db.search(query_embedding, top_k=top_k)

        # BM25 search
        bm25_results = self.bm25.search(query, top_k=top_k)

        # Combine with weights
        combined = {}

        for result in vector_results:
            doc_id = result["id"]
            combined[doc_id] = {
                **result,
                "score": result["score"] * 0.7
            }

        for result in bm25_results:
            doc_id = result["id"]
            norm_score = (result["score"] / 10) * 0.3
            if doc_id not in combined:
                combined[doc_id] = {**result, "score": 0}
            combined[doc_id]["score"] += norm_score

        # Sort and return texts
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:top_k]

        texts = [r["text"] for r in sorted_results]
        logger.info(f"✅ Retrieved {len(texts)} chunks for: {query}")
        return texts

    def _save(self):
        os.makedirs(KNOWLEDGE_BASE_PROCESSED, exist_ok=True)
        with open(RETRIEVER_CACHE, "wb") as f:
            pickle.dump({
                "vector_db": self.vector_db,
                "bm25": self.bm25,
                "documents": self.documents
            }, f)
        logger.info("💾 Retriever saved to disk")

    def _load(self):
        if os.path.exists(RETRIEVER_CACHE):
            with open(RETRIEVER_CACHE, "rb") as f:
                data = pickle.load(f)
            self.vector_db = data["vector_db"]
            self.bm25 = data["bm25"]
            self.documents = data["documents"]
            logger.info("✅ Retriever loaded from disk")
            return True
        return False


# Singleton — loaded once
_retriever_instance = None

def get_retriever() -> HybridRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
        _retriever_instance._load()
    return _retriever_instance

def search_hybrid(query: str, top_k: int = 3) -> List[str]:
    retriever = get_retriever()
    return retriever.retrieve(query, top_k=top_k)