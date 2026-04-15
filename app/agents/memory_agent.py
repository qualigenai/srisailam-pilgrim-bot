from groq import Groq
from app.utils.config import GROQ_API_KEY
from app.utils.session_store import get_history_as_text, get_user_name
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

# Words that indicate a NEW direct question — never a follow-up
DIRECT_QUESTION_STARTERS = [
    "what", "when", "where", "how", "which", "who", "why",
    "tell me", "explain", "describe", "is there", "are there",
    "can i", "do you", "does the",
    "temple", "darshan", "seva", "puja", "reach", "go to",
    "timings", "timing", "time", "open", "close",
    # Telugu
    "సమయాలు", "ఎలా", "ఏమిటి", "ఎంత", "ఎప్పుడు", "ఎక్కడ",
    "గుడి", "దర్శనం", "సేవ",
    # Hindi
    "समय", "कैसे", "क्या", "कब", "कहाँ", "कितना",
    "मंदिर", "दर्शन", "सेवा"
]

# Only these short phrases are genuine follow-ups
GENUINE_FOLLOWUP_PHRASES = [
    "tell me more", "more details", "explain more",
    "and then", "what else", "anything else",
    "how about that", "what about that",
    "can she attend", "can he attend", "can they attend",
    "is it safe", "is it free", "is it available",
    "అది ఎంత", "ఇంకా చెప్పు", "మరింత వివరాలు",
    "वह कितना", "और बताओ", "क्या यह"
]

def is_follow_up(message: str, history: str) -> bool:
    """
    Only returns True for genuinely ambiguous short follow-up messages.
    NEVER for direct complete questions.
    """
    if not history:
        return False

    message_lower = message.lower().strip()

    # Rule 1 — Long messages are always new questions
    if len(message.split()) > 5:
        return False

    # Rule 2 — If starts with a direct question word → NOT follow-up
    for starter in DIRECT_QUESTION_STARTERS:
        if message_lower.startswith(starter) or message_lower == starter:
            return False

    # Rule 3 — If contains direct question words anywhere → NOT follow-up
    direct_words = [
        "timings", "timing", "time", "temple", "darshan",
        "seva", "reach", "open", "close", "book", "booking",
        "cost", "price", "fee", "distance", "km", "hours",
        "సమయాలు", "గుడి", "दर्शन", "मंदिर"
    ]
    if any(word in message_lower for word in direct_words):
        return False

    # Rule 4 — Only these are genuine follow-ups
    for phrase in GENUINE_FOLLOWUP_PHRASES:
        if phrase in message_lower:
            return True

    # Rule 5 — Very short single pronouns might be follow-ups
    single_followup_words = ["it", "that", "this", "those", "అది", "ఇది", "वह", "यह"]
    if message_lower.strip() in single_followup_words:
        return True

    return False


def build_context_prompt(phone: str, current_message: str) -> str:
    history = get_history_as_text(phone)
    name = get_user_name(phone)

    context_parts = []
    if name:
        context_parts.append(f"Pilgrim's name: {name}")
    if history:
        # Only last 2 exchanges for context
        lines = history.strip().split("\n")
        recent = "\n".join(lines[-4:]) if len(lines) > 4 else history
        context_parts.append(f"Recent conversation:\n{recent}")

    if context_parts:
        context = "\n".join(context_parts)
        return f"""{context}

Current message: {current_message}

Based on the conversation history, answer the current message."""
    return current_message


def extract_name_from_message(message: str) -> str:
    try:
        # Quick check — only call Groq if "name" or "I am" is in message
        message_lower = message.lower()
        name_triggers = [
            "my name is", "i am", "i'm", "call me",
            "నా పేరు", "నేను", "मेरा नाम", "मैं"
        ]
        if not any(trigger in message_lower for trigger in name_triggers):
            return None

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Does this message introduce a person's name?
Message: "{message}"
If yes, reply with ONLY the name (1-2 words max).
If no, reply with: NONE"""
            }],
            max_tokens=10,
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        if result and result.upper() != "NONE" and len(result) < 30:
            return result
        return None
    except Exception as e:
        logger.error(f"Name extraction error: {e}")
        return None