from groq import Groq
from app.utils.config import GROQ_API_KEY
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

INTENTS = {
    "greeting": "User is saying hello, hi, namaste, jai shiva, jai mallikarjuna, om namah shivaya, నమస్కారం, నమస్తే, हेलो or any greeting in any language",
    "journey": "User wants to PLAN A TRIP or VISIT to Srisailam. Mentions days, travel, coming from a city, itinerary, trip planning, family trip, వెళ్ళాలి, వెళ్ళాలనుకుంటున్నాను, రోజులు, యాత్ర, जाना, दिन, यात्रा",
    "spiritual": "User asks about mantra meanings, spiritual significance, what a prayer means, pilgrimage spiritual benefits, devotional guidance — NOT about which seva to perform or booking. Examples: 'meaning of Om Namah Shivaya', 'benefits of visiting Srisailam', 'what is the spiritual significance', మంత్రం అర్థం, ఆధ్యాత్మిక",
    "temple_info": "User asks about temple timings, location, history, significance, dress code, entry rules, facilities, prasadam, annadanam, what is available at temple",
    "booking": "User asks specifically about HOW TO BOOK darshan tickets, seva tickets, accommodation — booking process only",
    "ritual": "User wants to perform a seva or puja, asks which seva to do, seva for health/wealth/family/education, wants to book a seva, preparation for a seva or darshan. Examples: 'I want to do a seva', 'which seva for health', 'seva for my mother', 'how to prepare for Sparsha Darshan', 'what seva should I do', ఏ సేవ చేయాలి, సేవ చేయాలి, పూజ చేయాలి, कौन सी सेवा, सेवा करना",
    "festival": "User asks about festivals, special days, Maha Shivaratri, Karthika Masam, celebrations",
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
4. If message mentions doing a seva, which seva to perform, seva for health/family/wealth, or preparation for darshan/seva → ALWAYS classify as "ritual"
5. If message asks how to PREPARE FOR darshan or what to BRING to temple → classify as "temple_info", NOT ritual
6. If message asks about mantra meaning or spiritual significance only (no seva) → classify as "spiritual"
7. If message asks about prasadam, annadanam, timings, facilities → classify as "temple_info"
8. Telugu: వెళ్ళాలి/వెళ్ళాలనుకుంటున్నాను/రోజులు/యాత్ర = journey
9. Telugu: ఏ సేవ/సేవ చేయాలి/పూజ చేయాలి = ritual

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
"I want to do a seva" → ritual
"Which seva should I do?" → ritual
"Seva for my mother health" → ritual
"ఏ సేవ చేయాలి అమ్మ ఆరోగ్యం కోసం?" → ritual
"How to prepare for Sparsha Darshan?" → temple_info
"What is the meaning of Om Namah Shivaya?" → spiritual
"What prasadam is available?" → temple_info
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