import logging
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0
logger = logging.getLogger(__name__)

# Telugu/Sanskrit/Hindi words commonly misidentified
TELUGU_KEYWORDS = [
    "suprabatham", "suprabhata", "darshan", "seva", "puja",
    "prasadam", "abhishekam", "mallikarjuna", "bhramarambika",
    "srisailam", "swamy", "amma", "garu", "mandir",
    "నమస్కారం", "ధన్యవాదాలు", "సేవ", "దర్శనం", "గుడి",
    "శివాయ", "మల్లికార్జున", "శ్రీశైలం", "స్వామి"
]

HINDI_KEYWORDS = [
    "namaste", "dhanyawad", "mandir", "pooja", "darshan",
    "namaskar", "swagat", "सेवा", "दर्शन", "मंदिर",
    "प्रसाद", "अभिषेक", "नमस्ते", "धन्यवाद"
]

SUPPORTED_LANGUAGES = {"en", "te", "hi"}


def detect_language(text: str) -> str:
    try:
        if not text or len(text.strip()) < 2:
            return "en"

        text_lower = text.lower().strip()

        # ── 1. Telugu script detection ──
        telugu_chars = sum(1 for c in text if '\u0c00' <= c <= '\u0c7f')
        if telugu_chars > 0:
            logger.info("🌐 Detected language: te (Telugu script)")
            return "te"

        # ── 2. Hindi/Devanagari script detection ──
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097f')
        if hindi_chars > 0:
            logger.info("🌐 Detected language: hi (Devanagari script)")
            return "hi"

        # ── 3. Telugu/Sanskrit keyword detection ──
        if any(kw in text_lower for kw in TELUGU_KEYWORDS):
            logger.info("🌐 Detected language: te (Telugu keyword match)")
            return "te"

        # ── 4. Hindi keyword detection ──
        if any(kw in text_lower for kw in HINDI_KEYWORDS):
            logger.info("🌐 Detected language: hi (Hindi keyword match)")
            return "hi"

        # ── 5. langdetect for everything else ──
        detected = detect(text)

        # Map unsupported languages to English
        # Indonesian (id), Malay (ms) often misidentify Telugu/Sanskrit
        MISIDENTIFICATION_MAP = {
            "id": "te",   # Indonesian ← often Telugu/Sanskrit
            "ms": "te",   # Malay ← often Telugu/Sanskrit
            "tl": "en",   # Filipino → English
            "af": "en",   # Afrikaans → English
            "nl": "en",   # Dutch → English
        }

        if detected in MISIDENTIFICATION_MAP:
            mapped = MISIDENTIFICATION_MAP[detected]
            logger.info(
                f"🌐 Remapped {detected} → {mapped} "
                f"(common misidentification)"
            )
            return mapped

        if detected not in SUPPORTED_LANGUAGES:
            logger.info(f"🌐 Unsupported language {detected} → defaulting to en")
            return "en"

        logger.info(f"🌐 Detected language: {detected}")
        return detected

    except LangDetectException:
        logger.warning("⚠️ Language detection failed — defaulting to en")
        return "en"
    except Exception as e:
        logger.error(f"❌ Language detector error: {e}")
        return "en"