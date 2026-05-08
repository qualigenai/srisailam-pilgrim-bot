from groq import Groq
from app.utils.config import GROQ_API_KEY
from app.rag.hybrid_retriever import search_hybrid
from app.utils.session_store import get_user_name
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)


class JourneyDetailsError(Exception):
    """Raised when the Groq call inside extract_journey_details fails."""


class ItineraryGenerationError(Exception):
    """Raised when the main LLM call inside create_itinerary fails."""


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

IMPORTANT: Keep response under 1200 characters total.
Use emojis for structure instead of markdown bold.
Concise bullet points suitable for WhatsApp.
For booking always direct to srisailadevasthanam.org or Mana Mitra 9552300009."""


def extract_journey_details(message: str) -> dict:
    try:
        system_prompt = (
            "Extract journey planning details from the pilgrim's message.\n\n"
            "Reply in this exact format (use \"unknown\" if not mentioned):\n"
            "FROM: <city>\n"
            "DAYS: <number>\n"
            "PEOPLE: <number or description>\n"
            "DATE: <date or season>\n"
            "SPECIAL: <any special requirements like elderly, children, specific seva>"
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": message},
            ],
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
        raise JourneyDetailsError(str(e)) from e


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

        user_prompt = f"""Create a concise Srisailam pilgrimage itinerary under 1000 characters.

Pilgrim details:
- Greeting: {name_greeting}
- From: {from_city}
- Days: {days}
- Group: {people}
- Date: {date}
- Special: {special}

Temple info:
{context}

Format for WhatsApp — use emojis, short bullet points, day-wise plan.
Include travel tip and must-visit spot.
Keep total under 1000 characters."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        itinerary = response.choices[0].message.content
        logger.info("✅ Itinerary created successfully")

        # Booking footer
        footer = "\n\n📱 Book: srisailadevasthanam.org\nMana Mitra: 9552300009"
        full_response = itinerary + footer

        # WhatsApp 1600 char limit — compress if needed
        if len(full_response) > 1500:
            logger.info(f"⚠️ Response too long ({len(full_response)} chars) — compressing...")
            concise_prompt = f"""Rewrite this itinerary in under 1100 characters for WhatsApp.
Keep complete day-wise plan but make each point very brief.
Use emojis. No markdown formatting.
Itinerary: {itinerary}"""

            concise_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise travel planner. Keep responses under 1100 characters. No markdown."
                    },
                    {"role": "user", "content": concise_prompt}
                ],
                max_tokens=350,
                temperature=0.1
            )
            itinerary = concise_response.choices[0].message.content
            full_response = itinerary + footer
            logger.info(f"✅ Compressed to {len(full_response)} chars")

        logger.info(f"📏 Final response length: {len(full_response)} chars")
        return full_response

    except JourneyDetailsError as e:
        logger.warning(f"Journey detail extraction failed — returning info prompt: {e}")
        return """🙏 I'd love to plan your Srisailam pilgrimage!

Please tell me:
- Which city are you travelling from?
- How many days do you have?
- How many people in your group?
- Any special requirements?

📱 Book: srisailadevasthanam.org
Mana Mitra: 9552300009"""
    except Exception as e:
        logger.error(f"❌ Journey planner error: {e}")
        raise ItineraryGenerationError(str(e)) from e


def needs_more_info(message: str) -> bool:
    try:
        details = extract_journey_details(message)
    except JourneyDetailsError as e:
        logger.warning(f"Journey detail extraction failed — assuming more info needed: {e}")
        return True
    from_city = details.get("FROM", "unknown")
    days = details.get("DAYS", "unknown")
    return from_city == "unknown" and days == "unknown"