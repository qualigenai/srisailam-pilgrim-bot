from groq import Groq
from app.utils.config import GROQ_API_KEY
from app.rag.hybrid_retriever import search_hybrid
from app.utils.session_store import get_user_name
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

PLANNER_SYSTEM_PROMPT = """You are an expert Srisailam temple pilgrimage planner. 
You have deep knowledge of Srisailam temple, its sevas, timings, nearby attractions and travel logistics.

Your job is to create personalized pilgrimage itineraries for devotees based on:
- Their starting city
- Number of days available
- Family composition (elderly, children, etc.)
- Specific sevas or experiences they want
- Travel dates or season

Always create practical, devotion-focused itineraries that:
- Prioritize spiritual experiences
- Account for realistic travel times
- Include must-visit spots around the temple
- Suggest suitable sevas based on their needs
- Mention booking requirements
- Keep it concise for WhatsApp

Start response with 🙏 and use simple formatting suitable for WhatsApp.
For booking always direct to srisailadevasthanam.org or Mana Mitra (9552300009)."""

def extract_journey_details(message: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Extract journey planning details from this message.
Message: "{message}"

Reply in this exact format (use "unknown" if not mentioned):
FROM: <city>
DAYS: <number>
PEOPLE: <number or description>
DATE: <date or season>
SPECIAL: <any special requirements like elderly, children, specific seva>"""
            }],
            max_tokens=100,
            temperature=0
        )
        raw = response.choices[0].message.content.strip()
        details = {}
        for line in raw.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                details[key.strip()] = val.strip()
        return details
    except Exception as e:
        logger.error(f"Detail extraction error: {e}")
        return {}

def create_itinerary(message: str, phone: str) -> str:
    try:
        logger.info(f"🗺️ Creating itinerary for: {message}")

        # Extract journey details
        details = extract_journey_details(message)
        logger.info(f"📋 Journey details: {details}")

        # Get relevant knowledge from RAG
        rag_context = search_hybrid(message, top_k=3)
        context = "\n\n".join(rag_context)

        # Get pilgrim name if known
        name = get_user_name(phone)
        name_greeting = f"Dear {name}" if name else "Dear Devotee"

        # Build personalized prompt
        from_city = details.get("FROM", "unknown")
        days = details.get("DAYS", "unknown")
        people = details.get("PEOPLE", "unknown")
        date = details.get("DATE", "unknown")
        special = details.get("SPECIAL", "none")

        user_prompt = f"""Create a personalized Srisailam pilgrimage itinerary.

Pilgrim details:
- Name greeting: {name_greeting}
- Travelling from: {from_city}
- Number of days: {days}
- Group: {people}
- Date/Season: {date}
- Special needs: {special}

Relevant temple information:
{context}

Create a practical day-by-day itinerary. 
Include travel tips, best darshan times, seva recommendations and must-visit spots.
Keep it concise and formatted for WhatsApp with emojis."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )

        itinerary = response.choices[0].message.content
        logger.info("✅ Itinerary created successfully")

        # Add booking footer
        footer = "\n\n📱 Book darshan/seva: srisailadevasthanam.org\nor Mana Mitra: 9552300009"
        return itinerary + footer

    except Exception as e:
        logger.error(f"❌ Journey planner error: {e}")
        return """🙏 I'd love to plan your Srisailam pilgrimage!

Please tell me:
- Which city are you travelling from?
- How many days do you have?
- How many people in your group?
- Any special requirements?

📱 You can also book at: srisailadevasthanam.org"""

def needs_more_info(message: str) -> bool:
    details = extract_journey_details(message)
    from_city = details.get("FROM", "unknown")
    days = details.get("DAYS", "unknown")
    return from_city == "unknown" and days == "unknown"