from groq import Groq
from app.utils.config import GROQ_API_KEY
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

INTENTS = {
    "greeting": "User is saying hello, hi, namaste, jai shiva, jai mallikarjuna, om namah shivaya, నమస్కారం, నమస్తే, హలో, శివాయ నమః, नमस्ते, जय शिव, हेलो or any greeting in any language",
    "temple_info": "User is asking about temple timings, location, directions, history, significance, dress code, facilities",
    "booking": "User is asking about booking darshan, seva, tickets, accommodation, online booking",
    "ritual": "User is asking about sevas, pujas, rituals, abhishekam, significance of rituals",
    "festival": "User is asking about festivals, special days, Maha Shivaratri, Karthika Masam",
    "unknown": "Message is unrelated to Srisailam temple or cannot be classified"
}

def classify_intent(message: str) -> str:
    try:
        intent_descriptions = "\n".join([f"- {k}: {v}" for k, v in INTENTS.items()])

        prompt = f"""Classify the following message into exactly one of these intents:
{intent_descriptions}

Message: "{message}"

Reply with ONLY the intent name, nothing else. No explanation.
Example replies: greeting, temple_info, booking, ritual, festival, unknown"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )

        intent = response.choices[0].message.content.strip().lower()

        if intent not in INTENTS:
            intent = "unknown"

        logger.info(f"🎯 Intent classified: {intent}")
        return intent

    except Exception as e:
        logger.error(f"❌ Intent classification error: {e}")
        return "unknown"