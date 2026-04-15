from groq import Groq
from app.utils.config import GROQ_API_KEY
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

INTENTS = {
    "greeting": "Hello, hi, namaste, jai shiva, jai mallikarjuna, good morning, నమస్కారం, नमस्ते",
    "closure": "Thank you, thanks, bye, okay done, dhanyavadalu, సరే, ధన్యవాదాలు",
    "journey": "Plan a trip, visit Srisailam, coming from city, number of days, itinerary, వెళ్ళాలి, రోజులు, యాత్ర",
    "ritual": "Which seva, what seva, seva for health/wealth/family, which puja, recommend seva, ఏ సేవ",
    "spiritual": "Mantra meaning, prayer significance, spiritual guidance, devotional, మంత్రం అర్థం",
    "temple_info": "Temple timings, opening time, closing time, how to reach, directions, darshan types, dress code, facilities, prasadam, annadanam, accommodation, what to bring, entry rules",
    "booking": "How to book, booking process, online booking, ticket booking, reservation",
    "festival": "Festival dates, Maha Shivaratri, Karthika Masam, when is festival",
    "unknown": "Unrelated to Srisailam temple"
}


def classify_intent(message: str) -> str:
    try:
        # DETERMINISTIC: Closure check (saves Groq call)
        text = message.lower().strip()
        closure_phrases = [
            "thanks", "thank you", "ok thanks", "okay thanks",
            "bye", "goodbye", "dhanyavadalu", "shukriya",
            "got it", "understood", "noted"
        ]
        if any(phrase == text or text.startswith(phrase) for phrase in closure_phrases):
            logger.info("🎯 Intent: closure (deterministic)")
            return "closure"

        # DETERMINISTIC: Simple greeting check
        greeting_words = ["hi", "hello", "hey", "namaste", "jai", "om"]
        if text in greeting_words or text.split()[0] in greeting_words:
            # But not if it has a question — "Hi what time does temple open"
            if "?" not in message and len(message.split()) <= 4:
                logger.info("🎯 Intent: greeting (deterministic)")
                return "greeting"
                # DETERMINISTIC: Directions → temple_info
            directions_phrases = [
                "how to reach", "how to get to", "how to go to",
                "route to", "directions to", "distance to",
                "nearest railway", "nearest airport", "nearest bus",
                "ఎలా చేరుకోవాలి", "ఎలా వెళ్ళాలి",
                "कैसे पहुंचें", "कैसे जाएं"
            ]
            if any(phrase in text for phrase in directions_phrases):
                logger.info("🎯 Intent: temple_info (deterministic - directions)")
                return "temple_info"


        # LLM CLASSIFICATION
        intent_list = "\n".join([f"- {k}: {v}" for k, v in INTENTS.items()])

        prompt = f"""Classify this message for Srisailam temple WhatsApp bot.

Message: "{message}"

Intent options:
{intent_list}

RULES:
1. "temple timings", "opening time", "how to reach" → temple_info
2. "which seva", "seva for health" → ritual
3. "plan visit", "coming from", "days trip" → journey
4. "mantra meaning", "significance" → spiritual
5. "how to book" → booking
6. "festival date" → festival
7. greeting words only → greeting
8. thank you / bye → closure

Reply with ONLY the intent name."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )

        intent = response.choices[0].message.content.strip().lower()
        intent = intent.replace(".", "").replace(",", "").strip()

        if intent not in INTENTS:
            logger.warning(f"Unknown intent: {intent} — using unknown")
            intent = "unknown"

        logger.info(f"🎯 Intent: {intent}")
        return intent

    except Exception as e:
        logger.error(f"❌ Intent error: {e}")
        return "unknown"