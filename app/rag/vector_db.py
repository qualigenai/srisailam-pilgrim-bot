from typing import List, Dict, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class VectorDBManager:
    """Simple in-memory vector database (works with any Python version)"""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.collection_name = "documents"
        self.vectors = {}  # id -> vector
        self.payloads = {}  # id -> payload
        self.next_id = 0

        logger.info("✅ Using in-memory vector store")

    def upsert_documents(self, documents: List[Dict], embeddings: List):
        """Insert or update documents with their embeddings"""
        for doc, embedding in zip(documents, embeddings):
            doc_id = self.next_id

            # Convert embedding to numpy array if needed
            if isinstance(embedding, list):
                embedding = np.array(embedding)

            self.vectors[doc_id] = embedding
            self.payloads[doc_id] = {
                "text": doc.get("text", ""),
                "source": doc.get("source", ""),
                "metadata": doc.get("metadata", {}),
                "chunk_id": doc.get("chunk_id", 0),
            }
            self.next_id += 1

        logger.info(f"Upserted {len(documents)} documents")

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """Search for similar documents using cosine similarity"""
        if not self.vectors:
            logger.warning("No vectors indexed yet")
            return []

        # Convert to numpy array
        query_vec = np.array(query_vector)

        # Calculate similarity scores
        scores = {}
        for doc_id, vector in self.vectors.items():
            # Cosine similarity
            vec = np.array(vector)
            similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-8)
            scores[doc_id] = float(similarity)

        # Sort by score and get top-k
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]

        results = []
        for doc_id in sorted_ids:
            if scores[doc_id] > 0:  # Only include positive scores
                results.append({
                    "id": doc_id,
                    "score": scores[doc_id],
                    "text": self.payloads[doc_id]["text"],
                    "source": self.payloads[doc_id]["source"],
                    "metadata": self.payloads[doc_id]["metadata"],
                })

        logger.info(f"Found {len(results)} results")
        return results

    def delete_documents(self, ids: List[int]):
        """Delete documents by ID"""
        for doc_id in ids:
            if doc_id in self.vectors:
                del self.vectors[doc_id]
                del self.payloads[doc_id]
        logger.info(f"Deleted {len(ids)} documents")

    def get_collection_info(self) -> Dict:
        """Get collection statistics"""
        return {
            "points_count": len(self.vectors),
            "status": "green",
        }


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = VectorDBManager(embedding_dim=384)
    info = manager.get_collection_info()
    print(f"Collection info: {info}")
    print("✅ Vector DB initialized successfully!")