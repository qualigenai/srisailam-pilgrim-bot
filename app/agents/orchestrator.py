from app.agents.intent_classifier import classify_intent
from app.agents.greeting_agent import handle_greeting
from app.agents.booking_agent import handle_booking
from app.rag.qa_chain import answer_question
from app.multilingual.detector import detect_language
from app.multilingual.translator import translate_to_english, translate_from_english
from app.agents.spiritual_agent import process_spiritual_message
from app.agents.journey_planner_agent import create_itinerary, needs_more_info
from app.utils.session_store import (
    get_user_language, set_user_language,
    add_to_history, get_history,
    set_user_name, get_user_name
)
from app.agents.memory_agent import (
    build_context_prompt,
    extract_name_from_message,
    is_follow_up
)
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

        # Step 2 — Translate to English
        english_message = translate_to_english(message, detected_lang)
        logger.info(f"🔤 English: {english_message}")

        # Step 3 — Extract name if introduced
        if not get_user_name(phone):
            name = extract_name_from_message(english_message)
            if name:
                set_user_name(phone, name)
                logger.info(f"👤 Name detected: {name}")

        # Step 4 — Check if follow-up question
        history = get_history(phone)
        history_text = "\n".join([
            f"{'Pilgrim' if h['role'] == 'user' else 'Bot'}: {h['message']}"
            for h in history
        ])

        if is_follow_up(english_message, history_text):
            logger.info("🔄 Follow-up question detected — adding context")
            english_message = build_context_prompt(phone, english_message)

        # Step 5 — Classify intent
        intent = classify_intent(english_message)
        logger.info(f"🎯 Intent: {intent}")

        # Step 6 — Store user message in history
        add_to_history(phone, "user", message)

        # Step 7 — Route to correct agent
        if intent == "greeting":
            name = get_user_name(phone)
            if name and len(history) > 0:
                response = f"🙏 Welcome back {name}! How can I help you today?\n\nAsk me anything about Srisailam temple — timings, sevas, directions or rituals. 🕉️"
            else:
                response = handle_greeting()

        elif intent == "booking":
            response = handle_booking()
            if detected_lang != "en":
                response = translate_from_english(response, detected_lang)

        elif intent == "journey":
            if needs_more_info(english_message):
                response = """🙏 I'd love to plan your Srisailam pilgrimage!

        Please share:
        - Which city are you travelling from?
        - How many days do you have?
        - How many people in your group?
        - Any special needs (elderly, children)?

        I'll create a personalized itinerary for you! 🛕"""
            else:
                response = create_itinerary(english_message, phone)
            if detected_lang != "en":
                response = translate_from_english(response, detected_lang)

        elif intent == "spiritual":
            response = process_spiritual_message(
                english_message, phone, detected_lang
            )
            if detected_lang != "en" and not any(
                    c for c in response if '\u0c00' <= c <= '\u0c7f'
            ):
                response = translate_from_english(response, detected_lang)

        elif intent in ["temple_info", "ritual", "festival"]:
            response = answer_question(english_message)
            disclaimer = get_disclaimer(detected_lang)
            if detected_lang != "en":
                response = translate_from_english(response, detected_lang)
            response = response + disclaimer

        else:
            response = get_unknown_message(detected_lang)

        # Step 8 — Store bot response in history
        add_to_history(phone, "bot", response)

        return response

    except Exception as e:
        logger.error(f"❌ Orchestrator error: {e}")
        return get_fallback_message(detected_lang)