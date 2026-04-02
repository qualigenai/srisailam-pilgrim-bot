from app.rag.loader import load_documents, chunk_documents
from app.rag.vectorstore import build_vectorstore
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("🚀 Starting knowledge base ingestion...")
    docs = load_documents()
    print(f"📄 Loaded {len(docs)} documents")
    chunks = chunk_documents(docs)
    print(f"✂️ Created {len(chunks)} chunks")
    build_vectorstore(chunks)
    print("✅ Knowledge base ready!")