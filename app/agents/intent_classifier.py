from groq import Groq
from app.utils.config import GROQ_API_KEY
import logging
from app.utils.phrase_lists import (
    CLOSURE_PHRASES, GREETING_PHRASES, GREETING_SINGLE_WORDS,
    DIRECTIONS_PHRASES, ACCOMMODATION_PHRASES, FESTIVAL_PHRASES,
    PREPARATION_PHRASES, TEMPLE_KEYWORDS,
)

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)


class IntentClassificationError(Exception):
    """Raised when classify_intent() fails to call or parse the Groq API."""

INTENTS = {
    "greeting": "Hello, hi, namaste, jai shiva, jai mallikarjuna, good morning, నమస్కారం, నమస్తే, हेलो or any greeting",
    "closure": "Thank you, thanks, bye, okay done, dhanyavadalu, సరే, ధన్యవాదాలు",
    "journey": "Plan a trip, coming from city with number of days, itinerary request, family of X for X days",
    "ritual": "Which seva, what seva, seva for health/wealth/family, which puja, recommend seva, ఏ సేవ",
    "spiritual": "Mantra meaning, prayer significance, how to prepare, checklist, devotional guidance",
    "temple_info": "Temple timings, directions, how to reach, distance, bus/train, accommodation, prasadam, dress code, facilities, significance, darshan types, entry fee, queue",
    "booking": "How to book, booking process, online booking, ticket booking, reservation",
    "festival": "Festival dates, Maha Shivaratri, Karthika Masam, Pradosha, Monday special, auspicious days",
    "unknown": "Unrelated to Srisailam temple"
}


def classify_intent(message: str) -> str:
    try:
        text = message.lower().strip()

        # ── 1. CLOSURE (deterministic) ──
        if any(text == p or text.startswith(p) for p in CLOSURE_PHRASES):
            logger.info("🎯 Intent: closure (deterministic)")
            return "closure"

        # ── 2. GREETING (deterministic) ──
        text_words = text.split()
        if any(p in text for p in GREETING_PHRASES):
            if "?" not in message and len(message.split()) <= 5:
                logger.info("🎯 Intent: greeting (deterministic)")
                return "greeting"
        if text_words and text_words[0] in GREETING_SINGLE_WORDS:
            if "?" not in message and len(message.split()) <= 4:
                logger.info("🎯 Intent: greeting (deterministic)")
                return "greeting"

        # ── 3. DIRECTIONS → temple_info (deterministic) ──
        if any(p in text for p in DIRECTIONS_PHRASES):
            logger.info("🎯 Intent: temple_info (deterministic - directions)")
            return "temple_info"

        # ── 4. ACCOMMODATION → temple_info (deterministic) ──
        if any(p in text for p in ACCOMMODATION_PHRASES):
            logger.info("🎯 Intent: temple_info (deterministic - accommodation)")
            return "temple_info"

        # ── 5. FESTIVAL (deterministic) ──
        if any(p in text for p in FESTIVAL_PHRASES):
            logger.info("🎯 Intent: festival (deterministic)")
            return "festival"

        # ── 6. PREPARATION → spiritual (deterministic) ──
        if any(p in text for p in PREPARATION_PHRASES):
            logger.info("🎯 Intent: spiritual (deterministic - preparation)")
            return "spiritual"

        # ── 7. TEMPLE KEYWORDS → temple_info (deterministic) ──
        if any(p in text for p in TEMPLE_KEYWORDS):
            logger.info("🎯 Intent: temple_info (deterministic - temple keyword)")
            return "temple_info"

        # ── 8. LLM CLASSIFICATION ──
        intent_list = "\n".join([f"- {k}: {v}" for k, v in INTENTS.items()])

        prompt = f"""Classify this message for Srisailam temple WhatsApp bot.

Message: "{message}"

Intent options:
{intent_list}

RULES:
1. ANY short query about temple, timings, darshan → temple_info
2. transport/distance/bus/train/route queries → temple_info
3. which seva / puja for intention → ritual
4. plan trip with days/city/group → journey
5. mantra/prayer meaning → spiritual
6. how to book → booking
7. festival/auspicious day → festival
8. greeting words only → greeting
9. thank you/bye → closure
10. NEVER return unknown for temple-related queries

Reply with ONLY the intent name. No explanation."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )

        intent = response.choices[0].message.content.strip().lower()
        intent = intent.replace(".", "").replace(",", "").strip()

        if intent not in INTENTS:
            logger.warning(f"Unknown intent: {intent} — defaulting to temple_info")
            intent = "temple_info"

        logger.info(f"🎯 Intent: {intent}")
        return intent

    except Exception as e:
        logger.error(f"❌ Intent error: {e}")
        raise IntentClassificationError(str(e)) from e