from groq import Groq
from app.utils.config import GROQ_API_KEY
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

INTENTS = {
    "greeting": "User is saying hello, hi, namaste, jai shiva, jai mallikarjuna, om namah shivaya, నమస్కారం, నమస్తే, हेलो or any greeting in any language",
    "closure": "User is saying thank you, thanks, bye, okay, dhanyavadalu, or ending the conversation",
    "journey": "User wants to PLAN A TRIP or VISIT to Srisailam. Mentions days, travel, coming from a city, itinerary, trip planning, family trip, వెళ్ళాలి, వెళ్ళాలనుకుంటున్నాను, రోజులు, యాత్ర, जाना, दिन, यात्रा",
    "spiritual": "User asks about mantra meanings, spiritual significance, what a prayer means, pilgrimage spiritual benefits, devotional guidance — NOT about which seva to perform or booking.",
    "temple_info": "User asks about temple timings, location, history, significance, dress code, entry rules, facilities, prasadam, annadanam, what is available at temple",
    "booking": "User asks specifically about HOW TO BOOK darshan tickets, seva tickets, accommodation — booking process only",
    "ritual": "User wants to perform a seva or puja, asks which seva to do, seva for health/wealth/family/education, wants to book a seva, preparation for a seva or darshan.",
    "festival": "User asks about festivals, special days, Maha Shivaratri, Karthika Masam, celebrations",
    "unknown": "Message is completely unrelated to Srisailam temple"
}

def classify_intent(message: str) -> str:
    try:
        # 1. DETERMINISTIC CHECK (Saves Cost/Time)
        text = message.lower().strip()
        closure_phrases = ["thanks", "thank you", "ok", "okay", "bye", "dhanyavadalu", "shukriya"]
        if any(phrase in text for phrase in closure_phrases):
            logger.info("🎯 Intent classified: closure (Deterministic)")
            return "closure"

        # 2. LLM CLASSIFICATION (For complex queries)
        intent_descriptions = "\n".join([f"- {k}: {v}" for k, v in INTENTS.items()])

        prompt = f"""You are classifying pilgrim messages for Srisailam temple chatbot.

CRITICAL RULES:
1. If message mentions planning a visit, number of days, or trip planning → "journey"
2. If message is a greeting → "greeting"
3. If message says thank you or goodbye → "closure"
4. If message mentions doing a seva or which seva to perform → "ritual"
5. If message asks about timings, facilities, or what to bring → "temple_info"

Intent definitions:
{intent_descriptions}

Message to classify: "{message}"

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
            intent = "unknown"

        logger.info(f"🎯 Intent classified: {intent}")
        return intent

    except Exception as e:
        logger.error(f"❌ Intent classification error: {e}")
        return "unknown"