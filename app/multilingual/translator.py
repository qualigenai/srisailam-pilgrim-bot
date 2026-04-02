from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

def translate_to_english(text: str, source_lang: str) -> str:
    try:
        if source_lang == "en":
            return text
        translated = GoogleTranslator(
            source=source_lang,
            target="en"
        ).translate(text)
        logger.info(f"✅ Translated to English: {translated}")
        return translated
    except Exception as e:
        logger.error(f"❌ Translation error: {e}")
        return text

def translate_from_english(text: str, target_lang: str) -> str:
    try:
        if target_lang == "en":
            return text
        translated = GoogleTranslator(
            source="en",
            target=target_lang
        ).translate(text)
        logger.info(f"✅ Translated to {target_lang}: {translated}")
        return translated
    except Exception as e:
        logger.error(f"❌ Translation error: {e}")
        return text