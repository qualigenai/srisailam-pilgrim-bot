from app.rag.loader import load_documents, chunk_documents
from app.rag.hybrid_retriever import HybridRetriever
from app.utils.config import KNOWLEDGE_BASE_PROCESSED
import os
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("🚀 Starting knowledge base ingestion with Hybrid RAG v1.5...")

    docs = load_documents()
    print(f"📄 Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✂️ Created {len(chunks)} chunks")

    retriever = HybridRetriever()
    retriever.index_documents(chunks)

    print("✅ Hybrid knowledge base ready!")
    print(f"📊 Vector search + BM25 hybrid retrieval active")