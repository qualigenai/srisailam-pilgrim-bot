import chromadb
from app.utils.config import KNOWLEDGE_BASE_PROCESSED
from app.rag.embedder import embed_texts
import logging

logger = logging.getLogger(__name__)

COLLECTION_NAME = "srisailam_knowledge"

def get_chroma_client():
    client = chromadb.PersistentClient(path=KNOWLEDGE_BASE_PROCESSED)
    return client

def build_vectorstore(chunks: list[dict]):
    client = get_chroma_client()

    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("🗑️ Deleted existing collection")
    except:
        pass

    collection = client.create_collection(COLLECTION_NAME)

    texts = [c["text"] for c in chunks]
    sources = [c["source"] for c in chunks]
    embeddings = embed_texts(texts)

    collection.add(
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[{"source": s} for s in sources],
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )
    logger.info(f"✅ Vectorstore built with {len(chunks)} chunks")
    return collection

def get_vectorstore():
    client = get_chroma_client()
    collection = client.get_collection(COLLECTION_NAME)
    return collection

def search_vectorstore(query: str, top_k: int = 3):
    collection = get_vectorstore()
    query_embedding = embed_texts([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
    return results["documents"][0]