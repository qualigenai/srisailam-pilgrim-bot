from groq import Groq
from app.utils.config import GROQ_API_KEY
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

INTENTS = {
    "greeting": "User is saying hello, hi, namaste, jai shiva, jai mallikarjuna, om namah shivaya, నమస్కారం, నమస్తే, హలో, शिवाय नमः, नमस्ते, जय शिव or any greeting in any language",
    "journey": "User wants to PLAN A TRIP or VISIT to Srisailam. Keywords: plan, visit, coming, travel, itinerary, days, trip, tour, how many days, family trip, వెళ్ళాలి, వెళ్ళాలనుకుంటున్నాను, రోజులు, యాత్ర, जाना, दिन, यात्रा. User mentions number of days OR starting city OR group size in context of visiting",
    "temple_info": "User is asking about temple timings, location, history, significance, dress code, facilities, darshan types",
    "booking": "User is asking specifically about HOW TO BOOK darshan tickets, seva tickets, accommodation — booking process only",
    "ritual": "User is asking about sevas, pujas, rituals, abhishekam, significance of specific rituals",
    "festival": "User is asking about festivals, special days, Maha Shivaratri, Karthika Masam, celebrations",
    "unknown": "Message is completely unrelated to Srisailam temple"
}

def classify_intent(message: str) -> str:
    try:
        intent_descriptions = "\n".join([f"- {k}: {v}" for k, v in INTENTS.items()])

        prompt = f"""You are classifying pilgrim messages for Srisailam temple chatbot.

CRITICAL RULES:
1. If message mentions planning a visit, number of days, coming from a city, or trip planning → ALWAYS classify as "journey"
2. If message mentions booking process or how to book → classify as "booking"  
3. If message is a greeting → classify as "greeting"
4. Telugu: వెళ్ళాలి/వెళ్ళాలనుకుంటున్నాను/రోజులు/యాత్ర = journey intent
5. Hindi: जाना/दिन/यात्रा/योजना = journey intent

Intent definitions:
{intent_descriptions}

Message to classify: "{message}"

Examples:
"I want to plan a visit" → journey
"Coming from Hyderabad, 2 days" → journey  
"శ్రీశైలం వెళ్ళాలనుకుంటున్నాను 2 రోజులు" → journey
"What time does temple open?" → temple_info
"How to book darshan?" → booking
"Tell me about Rudrabhishekam" → ritual
"Hi" → greeting

Reply with ONLY the intent name. No explanation. No punctuation."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )

        intent = response.choices[0].message.content.strip().lower()

        # Clean up response
        intent = intent.replace(".", "").replace(",", "").strip()

        if intent not in INTENTS:
            logger.warning(f"Unknown intent returned: {intent} — defaulting to unknown")
            intent = "unknown"

        logger.info(f"🎯 Intent classified: {intent}")
        return intent

    except Exception as e:
        logger.error(f"❌ Intent classification error: {e}")
        return "unknown"