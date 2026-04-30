import logging
from app.agents.intent_classifier import classify_intent
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


class AnalysisError(Exception):
    """Raised when analyze_message_combined() fails to call or parse the Groq API."""


# ── Shared deterministic phrase lists ───────────────────────

CLOSURE_PHRASES = [
    "thanks", "thank you", "ok thanks", "okay thanks",
    "bye", "goodbye", "dhanyavadalu", "shukriya",
    "got it", "understood", "noted"
]

GREETING_PHRASES = [
    "jai mallikarjuna", "jai shiva",
    "om namah shivaya", "har har mahadev",
    "హర హర మహాదేవ్", "నమస్కారం", "నమస్తే",
    "नमस्ते", "जय शिव", "हर हर महादेव"
]

GREETING_SINGLE_WORDS = ["hi", "hello", "hey", "namaste"]

DIRECTIONS_PHRASES = [
    "how to reach", "how to get to", "route to",
    "directions to", "distance to", "distance from",
    "bus from", "bus to", "train to", "train from",
    "nearest railway", "nearest station", "nearest airport",
    "railway station", "bus station", "nallamala", "forest road",
    "ఎలా చేరుకోవాలి", "ఎలా వెళ్ళాలి", "రైలు", "బస్సు",
    "कैसे पहुंचें", "कैसे जाएं", "रेलवे", "बस"
]

ACCOMMODATION_PHRASES = [
    "where to stay", "accommodation", "hotel near",
    "lodge near", "nandhiniketan", "rooms at",
    "dharmashalas", "guest house", "stay near",
    "stay in srisailam", "వసతి", "హోటల్",
    "रुकने", "होटल", "आवास"
]

FESTIVAL_PHRASES = [
    "pradosha", "pradosh",
    "is monday", "monday special",
    "shivaratri", "karthika",
    "సోమవారం", "ప్రదోష",
    "सोमवार", "प्रदोष"
]

PREPARATION_PHRASES = [
    "how to prepare", "preparation for",
    "what to bring", "what to carry",
    "checklist for", "dress code",
    "తయారు", "ఏమి తీసుకెళ్ళాలి",
    "तैयारी", "क्या पहनना"
]

TEMPLE_KEYWORDS = [
    "timings", "timing", "temple time", "open time",
    "darshan time", "puja time", "temple hours",
    "prasadam", "annadanam", "facilities",
    "entry fee", "ticket", "queue", "crowd",
    "significance", "history", "about temple",
    "dress code", "what to wear",
    "సమయాలు", "సమయం", "దర్శనం సమయం",
    "समय", "दर्शन समय", "मंदिर"
]


def analyze_message_combined(message: str, phone: str) -> dict:
    """
    Single Groq call combining intent + name + follow-up detection.
    Deterministic checks run first to save API calls.
    """
    from groq import Groq
    from app.utils.config import GROQ_API_KEY
    client = Groq(api_key=GROQ_API_KEY)

    text = message.lower().strip()
    text_words = text.split()

    # Get history for context
    history = get_history(phone)
    history_text = "\n".join([
        f"{h['role']}: {h['message']}"
        for h in history[-4:]
    ]) if history else "none"

    # ── 1. CLOSURE (deterministic) ──
    if any(text == p or text.startswith(p) for p in CLOSURE_PHRASES):
        return {"INTENT": "closure", "NAME": "NONE", "IS_FOLLOWUP": "NO"}

    # ── 2. GREETING (deterministic) ──
    if any(p in text for p in GREETING_PHRASES):
        if "?" not in message and len(message.split()) <= 5:
            return {"INTENT": "greeting", "NAME": "NONE", "IS_FOLLOWUP": "NO"}
    if text_words and text_words[0] in GREETING_SINGLE_WORDS:
        if "?" not in message and len(message.split()) <= 4:
            return {"INTENT": "greeting", "NAME": "NONE", "IS_FOLLOWUP": "NO"}

    # ── 3. DIRECTIONS → temple_info (deterministic) ──
    if any(p in text for p in DIRECTIONS_PHRASES):
        return {"INTENT": "temple_info", "NAME": "NONE", "IS_FOLLOWUP": "NO"}

    # ── 4. ACCOMMODATION → temple_info (deterministic) ──
    if any(p in text for p in ACCOMMODATION_PHRASES):
        return {"INTENT": "temple_info", "NAME": "NONE", "IS_FOLLOWUP": "NO"}

    # ── 5. FESTIVAL (deterministic) ──
    if any(p in text for p in FESTIVAL_PHRASES):
        return {"INTENT": "festival", "NAME": "NONE", "IS_FOLLOWUP": "NO"}

    # ── 6. PREPARATION → spiritual (deterministic) ──
    if any(p in text for p in PREPARATION_PHRASES):
        return {"INTENT": "spiritual", "NAME": "NONE", "IS_FOLLOWUP": "NO"}

    # ── 7. TEMPLE KEYWORDS → temple_info (deterministic) ──
    if any(p in text for p in TEMPLE_KEYWORDS):
        return {"INTENT": "temple_info", "NAME": "NONE", "IS_FOLLOWUP": "NO"}

    # ── 8. LLM combined analysis ──
    try:
        system_prompt = (
            "You are an intent classification assistant for a WhatsApp pilgrim guide bot serving the\n"
            "Srisailam Mallikarjuna Jyotirlinga temple in Andhra Pradesh, India. Your only job is to\n"
            "analyze an incoming pilgrim message and output three classification fields.\n\n"
            "Pilgrims may write in Telugu, Hindi, or English. Classify by meaning, not by language —\n"
            "treat Telugu and Hindi temple vocabulary as equivalent to their English counterparts.\n\n"
            "Respond in EXACTLY this format — three lines, no extra text, no explanation:\n"
            "INTENT: <greeting|journey|spiritual|ritual|temple_info|booking|festival|closure|unknown>\n"
            "NAME: <person name if the sender explicitly introduces themselves in the current message, else NONE>\n"
            "IS_FOLLOWUP: <YES if the current message is incomplete without the preceding conversation context, else NO>\n\n"
            "RULES:\n"
            "1. ANY short temple query (1–5 words about the temple) → temple_info\n"
            "2. transport / distance / bus / train / route / directions → temple_info\n"
            "3. plan a trip with a stated origin city and number of days → journey\n"
            "4. which seva / which puja / specific ritual inquiry → ritual\n"
            "5. mantra / preparation checklist / what to bring → spiritual\n"
            "6. timings / facilities / darshan info / dress code → temple_info\n"
            "7. booking inquiry / how to book → booking\n"
            "8. festival / auspicious day / pradosha / shivaratri → festival\n"
            "9. NEVER return unknown for any temple-related query — default to temple_info\n\n"
            "EDGE CASES:\n"
            "- Short messages (1–5 words) that are temple-related must resolve to temple_info, not unknown.\n"
            "- NAME must only reflect a name the sender explicitly states in the current message.\n"
            "  Do not infer or carry forward names seen in the conversation history.\n"
            "- IS_FOLLOWUP is YES only when the current message cannot stand alone without prior context\n"
            "  (e.g., \"what time?\" following a timings question, or \"tell me more\" with no new subject).\n"
            "- When a message contains both a greeting and a question, classify by the question's topic."
        )

        user_prompt = (
            f"<current_message>\n{message}\n</current_message>\n\n"
            f"<conversation_history>\n{history_text}\n</conversation_history>\n\n"
            "Classify the CURRENT MESSAGE shown above.\n"
            "The NAME and IS_FOLLOWUP fields refer strictly to the current message — do not extract\n"
            "names from the conversation history or treat history topics as the subject of the current message."
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
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
            result["INTENT"] = "temple_info"
        if "NAME" not in result:
            result["NAME"] = "NONE"
        if "IS_FOLLOWUP" not in result:
            result["IS_FOLLOWUP"] = "NO"

        # Safety net — never return unknown for short messages
        if result["INTENT"] == "unknown" and len(message.split()) <= 5:
            result["INTENT"] = "temple_info"

        return result

    except Exception as e:
        logger.error(f"Combined analysis error: {e}")
        raise AnalysisError(str(e)) from e


def process_message(message: str, phone: str = "unknown") -> str:
    """
    AWP v2 Orchestrator — optimized multi-agent workflow.
    Max 2 Groq calls per message.
    """
    auditor = AWPAuditor(phone)
    detected_lang = "en"

    try:
        logger.info(f"💬 AWP Workflow Started for: {phone}")

        # ── ROLE: LinguisticExpert ──
        detected_lang = detect_language(message)
        set_user_language(phone, detected_lang)
        english_message = translate_to_english(message, detected_lang)
        auditor.log_step(
            "LinguisticExpert", "detector_v1",
            "Translation to EN", english_message
        )

        # ── DETERMINISTIC: Ritual Flow continuation ──
        ritual_state = get_ritual_flow(phone)
        if ritual_state.get("step"):
            add_to_history(phone, "user", message)
            response = handle_ritual_flow(phone, english_message)
            auditor.log_step(
                "RitualSpecialist", "ritual_flow_v1",
                "Flow Continuation", response
            )
            final_artifact = finalize_awp_artifact(response, detected_lang, phone)
            auditor.save_audit_log()
            return final_artifact

        # ── COMBINED ANALYSIS (1 Groq call) ──
        analysis = analyze_message_combined(english_message, phone)
        intent = analysis.get("INTENT", "temple_info")
        detected_name = analysis.get("NAME", "NONE")
        is_followup = analysis.get("IS_FOLLOWUP", "NO") == "YES"

        auditor.log_step(
            "AnalysisAgent", "combined_v2",
            "Intent + Name", f"intent={intent} name={detected_name}"
        )

        # ── ROLE: MemoryAnalyst ──
        if detected_name != "NONE" and not get_user_name(phone):
            set_user_name(phone, detected_name)
            auditor.log_step(
                "MemoryAnalyst", "extractor_v1",
                "Name Saved", detected_name
            )

        # ── CONTEXT BUILDING ──
        if is_followup and len(english_message.split()) <= 5:
            english_message = build_context_prompt(phone, english_message)
            auditor.log_step(
                "MemoryAnalyst", "context_v1",
                "Context Enrichment", english_message[:100]
            )

        add_to_history(phone, "user", message)

        # ── CLOSURE: Early exit ──
        if intent == "closure":
            name = get_user_name(phone)
            response = (
                f"🙏 You're welcome{f' {name}' if name else ''}! "
                f"May Lord Mallikarjuna and Goddess Bhramarambika "
                f"bless you always. Om Namah Shivaya! 🕉️"
            )
            auditor.log_step("System", "termination_v1", "Workflow Closed", response)
            final_output = finalize_awp_artifact(response, detected_lang, phone)
            auditor.save_audit_log()
            return final_output

        # ── SPECIALIST AGENT ROUTING ──
        if intent == "greeting":
            name = get_user_name(phone)
            history = get_history(phone)
            if name and len(history) > 2:
                response = (
                    f"🙏 Welcome back {name}! How can I help you today?\n\n"
                    f"Ask me anything about Srisailam — timings, sevas, "
                    f"trip planning or rituals. 🕉️"
                )
            else:
                response = handle_greeting()
            role = "GreetingAgent"

        elif intent == "booking":
            response = handle_booking()
            role = "BookingCoordinator"

        elif intent == "journey":
            if needs_more_info(english_message):
                response = (
                    "🙏 I'd love to plan your Srisailam pilgrimage!\n\n"
                    "Please share:\n"
                    "• Which city are you travelling from?\n"
                    "• How many days do you have?\n"
                    "• How many people in your group?\n"
                    "• Any special needs (elderly, children)?\n\n"
                    "I'll create a personalized itinerary! 🛕"
                )
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
            # Safety net — unknown falls back to RAG
            logger.warning(f"⚠️ Unknown intent for: {english_message} — using RAG")
            response = answer_question(english_message)
            role = "InfoAnalyst"

        # ── LOG + FINALIZE ──
        auditor.log_step(
            role, f"{intent}_agent_v2",
            "Response Generation", response[:100]
        )
        final_output = finalize_awp_artifact(response, detected_lang, phone)
        auditor.save_audit_log()
        return final_output

    except AnalysisError as e:
        logger.error(f"Analysis agent failed — degrading gracefully: {e}")
        auditor.log_step("AnalysisAgent", "combined_v2", "Analysis Failed", str(e))
        auditor.save_audit_log()
        return get_fallback_message(detected_lang)
    except Exception as e:
        logger.error(f"❌ AWP Workflow Error: {e}")
        auditor.log_step("System", "error_handler", "Exception", str(e))
        auditor.save_audit_log()
        return get_fallback_message(detected_lang)