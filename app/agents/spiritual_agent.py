from groq import Groq
from app.utils.config import GROQ_API_KEY
from app.rag.hybrid_retriever import search_hybrid
from app.utils.session_store import get_user_name, get_history_as_text
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

SPIRITUAL_SYSTEM_PROMPT = """You are a knowledgeable and compassionate spiritual guide 
for Srisailam temple — one of the twelve Jyotirlingas of Lord Shiva.

You help pilgrims with:
- Choosing the right seva based on their prayer intention
- Understanding mantras and their meanings
- Preparing for specific sevas and darshan
- Understanding prasadam and its significance
- Spiritual guidance rooted in tradition

Always respond with warmth, devotion and respect.
Start responses with 🙏
Keep responses concise for WhatsApp — under 1200 characters.
Use Telugu, Hindi or English based on the pilgrim's language.
For bookings always direct to srisailadevasthanam.org or Mana Mitra 9552300009."""

SEVA_INTENTIONS = {
    "health": ["rudrabhishekam", "mahamrityunjaya", "kumkumarchana"],
    "prosperity": ["sahasranamarchana", "bilva archana", "abhishekam"],
    "family": ["kalyanotsavam", "kumkumarchana", "panchamruta abhishekam"],
    "education": ["sahasranamarchana", "ashtottara", "vidyarambham"],
    "moksha": ["sparsha darshan", "ekadasa rudrabhishekam", "pradosha"],
    "obstacles": ["rudrabhishekam", "bilva archana", "ekanta seva"]
}

FOLLOW_UP_QUESTION = {
    "en": """🙏 I'll help you choose the perfect seva!

What is your prayer intention?

1️⃣ Health & healing
2️⃣ Prosperity & wealth  
3️⃣ Family harmony & marriage
4️⃣ Children & education
5️⃣ Spiritual liberation
6️⃣ Removing obstacles

Please reply with the number or describe your intention.""",

    "te": """🙏 మీకు సరైన సేవను సూచించడానికి సహాయం చేస్తాను!

మీ ప్రార్థన ఉద్దేశ్యం ఏమిటి?

1️⃣ ఆరోగ్యం & నయం
2️⃣ సంపద & శ్రేయస్సు
3️⃣ కుటుంబ సామరస్యం & వివాహం
4️⃣ పిల్లలు & విద్య
5️⃣ ఆధ్యాత్మిక విముక్తి
6️⃣ అడ్డంకులు తొలగించడం

దయచేసి సంఖ్య లేదా మీ ఉద్దేశ్యాన్ని వివరించండి.""",

    "hi": """🙏 मैं आपको सही सेवा चुनने में मदद करूंगा!

आपकी प्रार्थना का उद्देश्य क्या है?

1️⃣ स्वास्थ्य और उपचार
2️⃣ समृद्धि और धन
3️⃣ पारिवारिक सद्भाव और विवाह
4️⃣ बच्चे और शिक्षा
5️⃣ आध्यात्मिक मोक्ष
6️⃣ बाधाओं को दूर करना

कृपया नंबर या अपना उद्देश्य बताएं।"""
}

def detect_intention(message: str) -> str:
    try:
        system_prompt = (
            "Identify the prayer intention from this message.\n\n"
            "Choose ONE from: health, prosperity, family, education, moksha, obstacles, general\n"
            "Reply with ONLY the single word."
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": message},
            ],
            max_tokens=10,
            temperature=0
        )
        intention = response.choices[0].message.content.strip().lower()
        if intention not in SEVA_INTENTIONS and intention != "general":
            return "general"
        return intention
    except Exception as e:
        logger.error(f"Intention detection error: {e}")
        return "general"

def is_seva_recommendation_request(message: str) -> bool:
    keywords = [
        "which seva", "what seva", "seva recommend", "suggest seva",
        "which puja", "what puja", "help me choose", "which ritual",
        "want to do seva", "want to perform", "which abhishekam",
        "ఏ సేవ", "సేవ సూచించండి", "ఏ పూజ",
        "कौन सी सेवा", "सेवा सुझाव", "कौन सी पूजा"
    ]
    message_lower = message.lower()
    return any(kw in message_lower for kw in keywords)

def is_mantra_request(message: str) -> bool:
    keywords = [
        "mantra", "prayer", "stotra", "sloka", "chant",
        "om namah shivaya", "mahamrityunjaya", "bilvashtakam",
        "మంత్రం", "స్తోత్రం", "ప్రార్థన",
        "मंत्र", "स्तोत्र", "प्रार्थना"
    ]
    message_lower = message.lower()
    return any(kw in message_lower for kw in keywords)

def is_preparation_request(message: str) -> bool:
    keywords = [
        "prepare", "preparation", "checklist", "what to bring",
        "what to carry", "dress code", "before visiting",
        "తయారు", "ఏమి తీసుకెళ్ళాలి", "ఏమి ధరించాలి",
        "तैयारी", "क्या लाना", "क्या पहनना"
    ]
    message_lower = message.lower()
    return any(kw in message_lower for kw in keywords)

def is_prasadam_request(message: str) -> bool:
    keywords = [
        "prasadam", "prasad", "food", "annadanam", "meal",
        "eat", "restaurant", "lunch", "breakfast",
        "ప్రసాదం", "అన్నదానం", "భోజనం",
        "प्रसाद", "अन्नदानम", "भोजन", "खाना"
    ]
    message_lower = message.lower()
    return any(kw in message_lower for kw in keywords)

def handle_seva_recommendation(message: str, phone: str, lang: str) -> str:
    try:
        intention = detect_intention(message)
        logger.info(f"🎯 Prayer intention: {intention}")

        if intention == "general":
            return FOLLOW_UP_QUESTION.get(lang, FOLLOW_UP_QUESTION["en"])

        # Get RAG context for this intention
        rag_query = f"seva for {intention} at Srisailam"
        rag_context = search_hybrid(rag_query, top_k=3)
        context = "\n\n".join(rag_context)

        name = get_user_name(phone)
        greeting = f"Dear {name}" if name else "Dear Devotee"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SPIRITUAL_SYSTEM_PROMPT},
                {"role": "user", "content": f"""Recommend the best seva for {intention} at Srisailam.
Greeting: {greeting}
Prayer intention: {intention}
Temple info: {context}

Provide:
1. Best recommended seva with reason
2. How to book it
3. One relevant mantra or prayer tip
Keep under 1000 characters. Use {lang} language."""}
            ],
            max_tokens=350,
            temperature=0.3
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Seva recommendation error: {e}")
        return FOLLOW_UP_QUESTION.get(lang, FOLLOW_UP_QUESTION["en"])

def handle_spiritual_query(message: str, phone: str, lang: str) -> str:
    try:
        # Get relevant spiritual knowledge
        rag_context = search_hybrid(message, top_k=3)
        context = "\n\n".join(rag_context)

        name = get_user_name(phone)
        greeting = f"Dear {name}" if name else "Dear Devotee"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SPIRITUAL_SYSTEM_PROMPT},
                {"role": "user", "content": f"""Answer this spiritual query about Srisailam temple.
Greeting: {greeting}
Question: {message}
Context: {context}

Keep under 1000 characters. Use {lang} language."""}
            ],
            max_tokens=350,
            temperature=0.3
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Spiritual query error: {e}")
        return "🙏 Sorry, I couldn't process your spiritual query. Please visit srisailadevasthanam.org or call 08524-288888."

def process_spiritual_message(message: str, phone: str, lang: str = "en") -> str:
    logger.info(f"🕉️ Processing spiritual message: {message[:50]}")

    if is_seva_recommendation_request(message):
        logger.info("→ Seva recommendation flow")
        return handle_seva_recommendation(message, phone, lang)

    elif is_mantra_request(message):
        logger.info("→ Mantra guide flow")
        return handle_spiritual_query(message, phone, lang)

    elif is_preparation_request(message):
        logger.info("→ Preparation checklist flow")
        return handle_spiritual_query(message, phone, lang)

    elif is_prasadam_request(message):
        logger.info("→ Prasadam guide flow")
        return handle_spiritual_query(message, phone, lang)

    else:
        logger.info("→ General spiritual query flow")
        return handle_spiritual_query(message, phone, lang)