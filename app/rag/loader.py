import os
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.config import KNOWLEDGE_BASE_RAW

logger = logging.getLogger(__name__)

def load_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def load_pdf(filepath):
    from pypdf import PdfReader
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def load_docx(filepath):
    from docx import Document
    doc = Document(filepath)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def load_documents():
    docs = []
    supported = {
        ".txt": load_txt,
        ".pdf": load_pdf,
        ".docx": load_docx
    }
    for filename in os.listdir(KNOWLEDGE_BASE_RAW):
        ext = os.path.splitext(filename)[1].lower()
        if ext in supported:
            filepath = os.path.join(KNOWLEDGE_BASE_RAW, filename)
            try:
                content = supported[ext](filepath)
                docs.append({
                    "content": content,
                    "source": filename
                })
                logger.info(f"✅ Loaded: {filename}")
            except Exception as e:
                logger.error(f"❌ Failed to load {filename}: {e}")
    return docs

def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=[
            "\n\nQ:", "\n\n", "\n-", "\n",
            ". ", "! ", "? ", " ", ""
        ]
    )
    chunks = []
    for doc in docs:
        splits = splitter.split_text(doc["content"])
        for split in splits:
            if len(split.strip()) > 50:
                chunks.append({
                    "text": split.strip(),
                    "source": doc["source"]
                })
    logger.info(f"✅ Total chunks: {len(chunks)}")
    return chunks