import logging
from app.agents.intent_classifier import classify_intent
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from app.agents.greeting_agent import handle_greeting
from app.agents.booking_agent import handle_booking
from app.rag.qa_chain import answer_question
from app.multilingual.detector import detect_language
from app.multilingual.translator import translate_to_english
from app.agents.spiritual_agent import process_spiritual_message
from app.agents.journey_planner_agent import create_itinerary, needs_more_info
from app.utils.session_store import (
    set_user_language, add_to_history, get_history,
    set_user_name, get_user_name, get_ritual_flow
)
from app.agents.memory_agent import (
    build_context_prompt, extract_name_from_message, is_follow_up
)
from app.utils.error_handler import get_fallback_message, get_unknown_message
from app.flows.ritual_flow import handle_ritual_flow
from app.utils.awp_logger import AWPAuditor
from app.utils.awp_helpers import finalize_awp_artifact

logger = logging.getLogger(__name__)


def analyze_message_combined(message: str, phone: str) -> dict:
    """
    Single Groq call that combines name extraction + intent.
    Saves 1 Groq call per message = 25% reduction in API usage.
    """
    from groq import Groq
    from app.utils.config import GROQ_API_KEY
    client = Groq(api_key=GROQ_API_KEY)

    history = get_history(phone)
    history_text = "\n".join([
        f"{h['role']}: {h['message']}"
        for h in history[-4:]
    ]) if history else "none"

    # Deterministic closure check — no Groq needed
    text = message.lower().strip()
    closure_phrases = [
        "thanks", "thank you", "ok", "okay", "bye",
        "dhanyavadalu", "shukriya", "👍"
    ]
    if any(phrase in text for phrase in closure_phrases):
        return {
            "INTENT": "closure",
            "NAME": "NONE",
            "IS_FOLLOWUP": "NO"
        }

    try:
        prompt = f"""Analyze this message for Srisailam temple WhatsApp bot.

Message: "{message}"
Recent chat: {history_text}

Reply in EXACTLY this format:
INTENT: <greeting|journey|spiritual|ritual|temple_info|booking|festival|closure|unknown>
NAME: <person name if introduced, else NONE>
IS_FOLLOWUP: <YES if refers to previous conversation, else NO>

Rules:
- journey = planning a trip, days, coming from city
- ritual = which seva to do, seva for health/wealth/family
- spiritual = mantra meaning, prayer significance
- temple_info = timings, facilities, dress code, prasadam
- closure = thanks, bye, okay, done"""

        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30,
            temperature=0
        )
        raw = response.choices[0].message.content.strip()
        result = {}
        for line in raw.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                result[key.strip()] = val.strip()

        if "INTENT" not in result:
            result["INTENT"] = "unknown"
        if "NAME" not in result:
            result["NAME"] = "NONE"
        if "IS_FOLLOWUP" not in result:
            result["IS_FOLLOWUP"] = "NO"

        return result

    except Exception as e:
        logger.error(f"Combined analysis error: {e}")
        return {"INTENT": "unknown", "NAME": "NONE", "IS_FOLLOWUP": "NO"}


def process_message(message: str, phone: str = "unknown") -> str:
    """
    AWP v2 Orchestrator — optimized for Render free tier.
    Reduced from 3-4 Groq calls to 2 Groq calls per message.
    """
    auditor = AWPAuditor(phone)
    detected_lang = "en"

    try:
        logger.info(f"💬 AWP Workflow Started for: {phone}")

        # --- ROLE: LinguisticExpert ---
        detected_lang = detect_language(message)
        set_user_language(phone, detected_lang)
        english_message = translate_to_english(message, detected_lang)
        auditor.log_step(
            "LinguisticExpert", "detector_v1",
            "Translation to EN", english_message
        )

        # --- DETERMINISTIC CHECK: Ritual Flow (no Groq needed) ---
        ritual_state = get_ritual_flow(phone)
        if ritual_state.get("step"):
            add_to_history(phone, "user", message)
            response = handle_ritual_flow(phone, english_message)
            auditor.log_step(
                "RitualSpecialist", "ritual_flow_v1",
                "Flow Continuation", response
            )
            final_artifact = finalize_awp_artifact(
                response, detected_lang, phone
            )
            auditor.save_audit_log()
            return final_artifact

        # --- COMBINED ANALYSIS (1 Groq call instead of 2) ---
        analysis = analyze_message_combined(english_message, phone)
        intent = analysis.get("INTENT", "unknown")
        detected_name = analysis.get("NAME", "NONE")
        is_followup = analysis.get("IS_FOLLOWUP", "NO") == "YES"

        auditor.log_step(
            "AnalysisAgent", "combined_v2",
            "Intent + Name Detection", f"intent={intent} name={detected_name}"
        )

        # --- ROLE: MemoryAnalyst ---
        if detected_name != "NONE" and not get_user_name(phone):
            set_user_name(phone, detected_name)
            auditor.log_step(
                "MemoryAnalyst", "extractor_v1",
                "Name Detection", detected_name
            )

        # --- CONTEXT BUILDING ---
        if is_followup:
            # Only add context for short ambiguous messages
            # Never for complete direct questions (len > 6 words)
            word_count = len(english_message.split())
            if word_count <= 6:
                english_message = build_context_prompt(phone, english_message)
                auditor.log_step(
                    "MemoryAnalyst", "context_v1",
                    "Context Enrichment", english_message[:100]
                )

        add_to_history(phone, "user", message)

        # --- CLOSURE: Early exit (no Groq needed) ---
        if intent == "closure":
            name = get_user_name(phone)
            response = f"🙏 You're welcome{f' {name}' if name else ''}! May Lord Mallikarjuna and Goddess Bhramarambika bless you always. Om Namah Shivaya! 🕉️"
            auditor.log_step(
                "System", "termination_v1",
                "Workflow Closed", response
            )
            final_output = finalize_awp_artifact(
                response, detected_lang, phone
            )
            auditor.save_audit_log()
            return final_output

        # --- EXECUTION: Specialist Agent Routing ---
        if intent == "greeting":
            name = get_user_name(phone)
            history = get_history(phone)
            if name and len(history) > 2:
                response = f"🙏 Welcome back {name}! How can I help you today?\n\nAsk me anything about Srisailam — timings, sevas, trip planning or rituals. 🕉️"
            else:
                response = handle_greeting()
            role = "GreetingAgent"

        elif intent == "booking":
            response = handle_booking()
            role = "BookingCoordinator"

        elif intent == "journey":
            if needs_more_info(english_message):
                response = """🙏 I'd love to plan your Srisailam pilgrimage!

Please share:
- Which city are you travelling from?
- How many days do you have?
- How many people in your group?
- Any special needs (elderly, children)?

I'll create a personalized itinerary! 🛕"""
            else:
                response = create_itinerary(english_message, phone)
            role = "JourneyPlanner"

        elif intent == "ritual":
            response = process_spiritual_message(
                english_message, phone, detected_lang
            )
            role = "RitualSpecialist"

        elif intent == "spiritual":
            response = process_spiritual_message(
                english_message, phone, detected_lang
            )
            role = "SpiritualGuide"

        elif intent in ["temple_info", "festival"]:
            response = answer_question(english_message)
            role = "InfoAnalyst"

        else:
            response = get_unknown_message(detected_lang)
            role = "System"

        # --- LOG + FINALIZE ---
        auditor.log_step(
            role, f"{intent}_agent_v2",
            "Response Generation", response[:100]
        )
        final_output = finalize_awp_artifact(
            response, detected_lang, phone
        )
        auditor.save_audit_log()
        return final_output

    except Exception as e:
        logger.error(f"❌ AWP Workflow Error: {e}")
        auditor.log_step(
            "System", "error_handler",
            "Exception Occurred", str(e)
        )
        auditor.save_audit_log()
        return get_fallback_message(detected_lang)