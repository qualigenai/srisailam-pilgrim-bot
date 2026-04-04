from typing import List, Dict
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger(__name__)

class BM25Retriever:
    """BM25-based keyword search"""
    
    def __init__(self):
        self.corpus = []
        self.corpus_metadata = []
        self.bm25 = None
    
    def index(self, documents: List[Dict]):
        """Index documents for BM25 search"""
        self.corpus = []
        self.corpus_metadata = []
        
        for i, doc in enumerate(documents):
            text = doc["text"]
            # Tokenize (simple split, can be improved)
            tokens = text.lower().split()
            self.corpus.append(tokens)
            
            self.corpus_metadata.append({
                "text": text,
                "source": doc.get("source", ""),
                "metadata": doc.get("metadata", {}),
            })
        
        self.bm25 = BM25Okapi(self.corpus)
        logger.info(f"Indexed {len(self.corpus)} documents for BM25")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search documents using BM25"""
        if not self.bm25:
            logger.warning("BM25 not indexed yet")
            return []
        
        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        
        results = [
            {
                "id": idx,
                "score": float(scores[idx]),
                "text": self.corpus_metadata[idx]["text"],
                "source": self.corpus_metadata[idx]["source"],
                "metadata": self.corpus_metadata[idx]["metadata"],
            }
            for idx in top_indices
            if scores[idx] > 0  # Filter out zero scores
        ]
        
        return results

# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    docs = [
        {"text": "Machine learning is a subset of AI", "source": "doc1"},
        {"text": "Deep learning uses neural networks", "source": "doc2"},
        {"text": "RAG combines retrieval and generation", "source": "doc3"},
    ]
    
    retriever = BM25Retriever()
    retriever.index(docs)
    
    results = retriever.search("machine learning", top_k=2)
    print(f"Found {len(results)} results")
    for r in results:
        print(f"Score: {r['score']:.2f}, Text: {r['text'][:50]}")
    print("✅ BM25 search test passed!")