import os
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "srisailam_bot_2024")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_BASE_RAW = os.path.join(BASE_DIR, "knowledge_base", "raw")
KNOWLEDGE_BASE_PROCESSED = os.path.join(BASE_DIR, "knowledge_base", "processed")

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama-3.1-8b-instant"
MAX_TOKENS = 512
TEMPERATURE = 0.3
TOP_K_RESULTS = 3