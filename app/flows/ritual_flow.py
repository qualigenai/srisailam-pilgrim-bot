from app.rag.qa_chain import answer_question
from app.utils.session_store import get_ritual_flow, set_ritual_flow, clear_ritual_flow
import logging

logger = logging.getLogger(__name__)

INTENTION_MENU = (
    "What is your prayer intention? 🙏\n\n"
    "🌿 Health\n"
    "💰 Prosperity\n"
    "👨‍👩‍👧 Family\n"
    "📚 Education\n"
    "🌟 General Blessings\n\n"
    "Please type your intention (e.g. 'Health for my mother')"
)

SEVA_MAP = {
    "health":      "Rudrabhishekam",
    "sick":        "Rudrabhishekam",
    "disease":     "Rudrabhishekam",
    "ill":         "Rudrabhishekam",
    "prosperity":  "Lakshmi Puja",
    "wealth":      "Lakshmi Puja",
    "money":       "Lakshmi Puja",
    "business":    "Lakshmi Puja",
    "family":      "Satyanarayana Puja",
    "marriage":    "Satyanarayana Puja",
    "husband":     "Satyanarayana Puja",
    "wife":        "Satyanarayana Puja",
    "children":    "Santana Gopala Puja",
    "child":       "Santana Gopala Puja",
    "baby":        "Santana Gopala Puja",
    "education":   "Saraswathi Homam",
    "studies":     "Saraswathi Homam",
    "exam":        "Saraswathi Homam",
    "study":       "Saraswathi Homam",
    "general":     "Abhishekam",
    "blessings":   "Abhishekam",
    "moksha":      "Rudrabhishekam",
    "peace":       "Abhishekam",
}


def get_seva_for_intention(intention: str) -> str:
    """Map user intention keywords to a specific seva."""
    intention_lower = intention.lower()
    for keyword, seva in SEVA_MAP.items():
        if keyword in intention_lower:
            return seva
    return "Abhishekam"  # default fallback


def handle_ritual_flow(phone: str, message: str) -> str:
    """
    Multi-turn seva recommendation flow.

    Step 1 (start)                → Show intention menu
    Step 2 (awaiting_intention)   → Map intention to seva, fetch RAG details
    Step 3 (awaiting_booking_confirm) → Confirm booking, collect details
    """
    flow = get_ritual_flow(phone)
    step = flow.get("step")

    # ── Step 1: Fresh trigger — show intention menu ────────────────────────────
    if step is None:
        set_ritual_flow(phone, {"step": "awaiting_intention"})
        logger.info(f"🛕 Ritual flow started for {phone}")
        return INTENTION_MENU

    # ── Step 2: User gave intention — recommend seva ───────────────────────────
    if step == "awaiting_intention":
        seva = get_seva_for_intention(message)
        logger.info(f"🙏 Intention: '{message}' → Seva: {seva}")

        # RAG called now with a specific, answerable query
        rag_answer = answer_question(
            f"How to book and prepare for {seva} at Srisailam temple?"
        )

        set_ritual_flow(phone, {
            "step": "awaiting_booking_confirm",
            "seva": seva,
            "intention": message,
        })

        return (
            f"For your intention, *{seva}* is the most powerful seva. 🙏\n\n"
            f"{rag_answer}\n\n"
            f"Would you like to book this seva?\n"
            f"Reply *Yes* to proceed or *No* to choose a different intention."
        )

    # ── Step 3: Booking confirmation ───────────────────────────────────────────
    if step == "awaiting_booking_confirm":
        seva = flow.get("seva", "seva")
        msg_lower = message.lower()

        if "yes" in msg_lower:
            clear_ritual_flow(phone)
            logger.info(f"✅ Booking confirmed for {phone}: {seva}")
            return (
                f"🎉 Wonderful! To complete your *{seva}* booking, please share:\n\n"
                f"📛 Full Name\n"
                f"📅 Preferred Date\n"
                f"📿 Gotram (if known)\n"
                f"📞 Contact Number\n\n"
                f"Our team at Srisailam will confirm your booking shortly. 🕉️"
            )

        elif "no" in msg_lower:
            set_ritual_flow(phone, {"step": "awaiting_intention"})
            logger.info(f"🔄 Ritual flow restarted for {phone}")
            return "No problem! 🙏 Let's choose again.\n\n" + INTENTION_MENU

        else:
            # Unclear response — re-prompt without resetting
            return (
                f"Please reply *Yes* to book *{seva}* or "
                f"*No* to choose a different seva. 🙏"
            )

    # ── Safety fallback — reset flow ───────────────────────────────────────────
    clear_ritual_flow(phone)
    return INTENTION_MENU