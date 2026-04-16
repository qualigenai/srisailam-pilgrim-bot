import logging
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0
logger = logging.getLogger(__name__)

# ONLY pure Telugu words — NOT English proper nouns
TELUGU_WORDS = [
    "నమస్కారం", "ధన్యవాదాలు", "సేవ", "దర్శనం", "గుడి",
    "శివాయ", "మల్లికార్జున", "శ్రీశైలం", "స్వామి",
    "ఆలయం", "పూజ", "ప్రసాదం", "అభిషేకం", "యాత్ర",
    "వసతి", "హోటల్", "రోజులు", "వెళ్ళాలి", "చేరుకోవాలి",
    "సమయాలు", "సమయం", "ఎలా", "ఏమిటి", "ఎంత"
]

# ONLY pure Hindi words — NOT English proper nouns
HINDI_WORDS = [
    "नमस्ते", "धन्यवाद", "मंदिर", "सेवा", "दर्शन",
    "प्रसाद", "अभिषेक", "यात्रा", "समय", "कैसे",
    "क्या", "कब", "कहाँ", "जाना", "रुकना",
    "होटल", "बस", "रेलवे", "दिन", "परिवार"
]

SUPPORTED_LANGUAGES = {"en", "te", "hi"}

# Languages that commonly misidentify Telugu/Sanskrit in Latin script
MISIDENTIFICATION_MAP = {
    "id": "en",  # Indonesian ← misidentifies Sanskrit/Telugu words
    "ms": "en",  # Malay ← same issue
    "tl": "en",  # Filipino
    "af": "en",  # Afrikaans
    "nl": "en",  # Dutch
    "sw": "en",  # Swahili
    "so": "en",  # Somali
}


def is_latin_script(text: str) -> bool:
    """Check if text is predominantly Latin script."""
    latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total_chars = sum(1 for c in text if c.isalpha())
    if total_chars == 0:
        return True
    return (latin_chars / total_chars) >= 0.8


def detect_language(text: str) -> str:
    try:
        if not text or len(text.strip()) < 2:
            return "en"

        # ── 1. Telugu script detection (Unicode range) ──
        telugu_chars = sum(1 for c in text if '\u0c00' <= c <= '\u0c7f')
        if telugu_chars > 0:
            logger.info("🌐 Detected language: te (Telugu script)")
            return "te"

        # ── 2. Hindi/Devanagari script detection ──
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097f')
        if hindi_chars > 0:
            logger.info("🌐 Detected language: hi (Devanagari script)")
            return "hi"

        # ── 3. If Latin script → check for pure Telugu/Hindi words only ──
        if is_latin_script(text):
            # Only match pure Telugu/Hindi words in Latin transliteration
            # NOT domain proper nouns like Srisailam, Darshan, Seva
            text_lower = text.lower().strip()

            # Pure Telugu transliterated words (not temple proper nouns)
            telugu_latin = [
                "meeru", "mee", "nenu", "mana", "ikkade",
                "akkade", "ela", "emiti", "evaru", "enduku"
            ]
            if any(w in text_lower for w in telugu_latin):
                logger.info("🌐 Detected language: te (Telugu transliteration)")
                return "te"

            # Pure Hindi transliterated words (not temple proper nouns)
            hindi_latin = [
                "aap", "hum", "yahan", "wahan", "kaise",
                "kya", "kab", "kahan", "jana", "chahiye"
            ]
            if any(w in text_lower for w in hindi_latin):
                logger.info("🌐 Detected language: hi (Hindi transliteration)")
                return "hi"

            # Latin script with no Telugu/Hindi markers → English
            logger.info("🌐 Detected language: en (Latin script)")
            return "en"

        # ── 4. Pure Telugu/Hindi Unicode words in non-Latin text ──
        if any(w in text for w in TELUGU_WORDS):
            logger.info("🌐 Detected language: te (Telugu word match)")
            return "te"

        if any(w in text for w in HINDI_WORDS):
            logger.info("🌐 Detected language: hi (Hindi word match)")
            return "hi"

        # ── 5. langdetect fallback ──
        detected = detect(text)

        if detected in MISIDENTIFICATION_MAP:
            mapped = MISIDENTIFICATION_MAP[detected]
            logger.info(f"🌐 Remapped {detected} → {mapped}")
            return mapped

        if detected not in SUPPORTED_LANGUAGES:
            logger.info(f"🌐 Unsupported {detected} → en")
            return "en"

        logger.info(f"🌐 Detected language: {detected}")
        return detected

    except LangDetectException:
        logger.warning("⚠️ Language detection failed → en")
        return "en"
    except Exception as e:
        logger.error(f"❌ Detector error: {e}")
        return "en"