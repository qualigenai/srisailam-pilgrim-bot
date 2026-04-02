from app.agents.intent_classifier import classify_intent
from app.agents.greeting_agent import handle_greeting
from app.agents.booking_agent import handle_booking
from app.rag.qa_chain import answer_question
from app.multilingual.detector import detect_language
from app.multilingual.translator import translate_to_english, translate_from_english
from app.utils.session_store import get_user_language, set_user_language
from app.utils.error_handler import get_fallback_message, get_unknown_message
from app.utils.message_templates import get_disclaimer
import logging

logger = logging.getLogger(__name__)

def process_message(message: str, phone: str = "unknown") -> str:
    detected_lang = "en"
    try:
        logger.info(f"💬 Processing: {message} from {phone}")

        # Step 1 — Detect language
        detected_lang = detect_language(message)
        set_user_language(phone, detected_lang)
        logger.info(f"🌐 Language: {detected_lang}")

        # Step 2 — Translate to English
        english_message = translate_to_english(message, detected_lang)
        logger.info(f"🔤 English: {english_message}")

        # Step 3 — Classify intent
        intent = classify_intent(english_message)
        logger.info(f"🎯 Intent: {intent}")

        # Step 4 — Route to correct agent
        if intent == "greeting":
            return handle_greeting()

        elif intent == "booking":
            response = handle_booking()
            if detected_lang != "en":
                response = translate_from_english(response, detected_lang)
            return response

        elif intent in ["temple_info", "ritual", "festival"]:
            response = answer_question(english_message)
            disclaimer = get_disclaimer(detected_lang)
            if detected_lang != "en":
                response = translate_from_english(response, detected_lang)
            return response + disclaimer

        else:
            return get_unknown_message(detected_lang)

    except Exception as e:
        logger.error(f"❌ Orchestrator error: {e}")
        return get_fallback_message(detected_lang)