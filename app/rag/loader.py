import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.config import KNOWLEDGE_BASE_RAW
import logging

logger = logging.getLogger(__name__)

def load_documents():
    docs = []
    for filename in os.listdir(KNOWLEDGE_BASE_RAW):
        if filename.endswith(".txt"):
            filepath = os.path.join(KNOWLEDGE_BASE_RAW, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            docs.append({"content": content, "source": filename})
            logger.info(f"✅ Loaded: {filename}")
    return docs

def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\nQ:", "\n\n", "\n", " "]
    )
    chunks = []
    for doc in docs:
        splits = splitter.split_text(doc["content"])
        for split in splits:
            chunks.append({
                "text": split,
                "source": doc["source"]
            })
    logger.info(f"✅ Total chunks created: {len(chunks)}")
    return chunks