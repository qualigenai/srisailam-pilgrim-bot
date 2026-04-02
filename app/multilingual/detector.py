from langdetect import detect
import logging

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "te": "Telugu",
    "hi": "Hindi",
    "kn": "kannada",
    "ta": "tamil",
    "en": "English"
}

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        logger.info(f"🌐 Detected language: {lang}")
        if lang in SUPPORTED_LANGUAGES:
            return lang
        return "en"
    except Exception as e:
        logger.error(f"❌ Language detection error: {e}")
        return "en"