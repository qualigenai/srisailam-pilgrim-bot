from groq import Groq
from app.utils.config import GROQ_API_KEY
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

INTENTS = {
    "greeting": "Hello, hi, namaste, jai shiva, jai mallikarjuna, good morning, నమస్కారం, నమస్తే, हेलो or any greeting",
    "closure": "Thank you, thanks, bye, okay done, dhanyavadalu, సరే, ధన్యవాదాలు",
    "journey": "Plan a trip, coming from city with number of days, itinerary request, family of X for X days",
    "ritual": "Which seva, what seva, seva for health/wealth/family, which puja, recommend seva, ఏ సేవ",
    "spiritual": "Mantra meaning, prayer significance, how to prepare, checklist, devotional guidance",
    "temple_info": "Temple timings, directions, how to reach, distance, bus/train, accommodation, prasadam, dress code, facilities, significance, darshan types",
    "booking": "How to book, booking process, online booking, ticket booking, reservation",
    "festival": "Festival dates, Maha Shivaratri, Karthika Masam, Pradosha, Monday special, auspicious days",
    "unknown": "Unrelated to Srisailam temple"
}

# ── Deterministic phrase lists ──────────────────────────────

CLOSURE_PHRASES = [
    "thanks", "thank you", "ok thanks", "okay thanks",
    "bye", "goodbye", "dhanyavadalu", "shukriya",
    "got it", "understood", "noted", "ok bye", "okay bye"
]

GREETING_PHRASES = [
    "hi", "hello", "hey", "namaste",
    "jai mallikarjuna", "jai shiva", "jai shiv",
    "om namah shivaya", "om namaha shivaya",
    "har har mahadev", "har har mahade",
    "హర హర మహాదేవ్", "నమస్కారం", "నమస్తే", "హలో",
    "నమస్కారములు", "శివాయ నమః",
    "नमस्ते", "जय शिव", "हर हर महादेव",
    "jai mallikarjuna swamy", "jai bhramarambika"
]

DIRECTIONS_PHRASES = [
    "how to reach", "how to get to", "how to go to",
    "route to", "directions to", "distance to",
    "distance from",
    "bus from", "bus to", "buses to",
    "train to", "train from", "trains to",
    "nearest railway", "nearest station", "nearest airport",
    "railway station", "bus station", "bus stand",
    "nallamala", "forest road", "nh765",
    "cab from", "taxi from", "drive from",
    "ఎలా చేరుకోవాలి", "ఎలా వెళ్ళాలి", "దూరం ఎంత",
    "కి.మీ", "రైలు", "బస్సు",
    "कैसे पहुंचें", "कैसे जाएं", "दूरी", "रेलवे", "बस"
]

FESTIVAL_PHRASES = [
    "pradosha", "pradosh",
    "is monday", "monday special", "monday at srisailam",
    "shivaratri", "karthika", "brahmotsavam",
    "ugadi", "sankranti", "auspicious day",
    "somavar", "సోమవారం", "ప్రదోష", "కార్తీక",
    "सोमवार", "प्रदोष", "कार्तिक"
]

ACCOMMODATION_PHRASES = [
    "where to stay", "where to sleep",
    "accommodation", "hotel near", "hotels in",
    "lodge near", "nandhiniketan", "rooms at",
    "dharmashalas", "guest house", "staying at",
    "stay near temple", "stay in srisailam",
    "వసతి", "హోటల్", "నందినికేతన్",
    "रुकने", "होटल", "आवास"
]

PREPARATION_PHRASES = [
    "how to prepare", "preparation for",
    "what to bring", "what to carry", "what to wear",
    "checklist for", "ready for", "before visiting",
    "dress code", "what is required for",
    "తయారు", "ఏమి తీసుకెళ్ళాలి",
    "तैयारी", "क्या पहनना", "क्या लाना"
]


def classify_intent(message: str) -> str:
    try:
        text = message.lower().strip()

        # ── 1. CLOSURE (deterministic) ──
        if any(text == p or text.startswith(p) for p in CLOSURE_PHRASES):
            logger.info("🎯 Intent: closure (deterministic)")
            return "closure"

        # ── 2. GREETING (deterministic) ──
        text_words = text.split()
        if any(p == text or p in text_words or text.startswith(p + " ") for p in GREETING_PHRASES):
            if "?" not in message and len(message.split()) <= 5:
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

        # ── 7. LLM CLASSIFICATION ──
        intent_list = "\n".join([f"- {k}: {v}" for k, v in INTENTS.items()])

        prompt = f"""Classify this message for Srisailam temple WhatsApp bot.

Message: "{message}"

Intent options:
{intent_list}

RULES:
1. transport/distance/bus/train/route queries → temple_info
2. which seva / puja for intention → ritual
3. plan trip with days/city/group → journey
4. mantra/prayer meaning → spiritual
5. how to book → booking
6. festival/auspicious day → festival
7. greeting only → greeting
8. thank you/bye → closure

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
            logger.warning(f"Unknown intent: {intent} — defaulting to unknown")
            intent = "unknown"

        logger.info(f"🎯 Intent: {intent}")
        return intent

    except Exception as e:
        logger.error(f"❌ Intent error: {e}")
        return "unknown"