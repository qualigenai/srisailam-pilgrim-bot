from groq import Groq
from app.utils.config import GROQ_API_KEY
from app.utils.session_store import get_history_as_text, get_user_name
import logging

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

def build_context_prompt(phone: str, current_message: str) -> str:
    history = get_history_as_text(phone)
    name = get_user_name(phone)

    context_parts = []

    if name:
        context_parts.append(f"Pilgrim's name: {name}")

    if history:
        context_parts.append(f"Recent conversation:\n{history}")

    if context_parts:
        context = "\n".join(context_parts)
        return f"""{context}

Current message: {current_message}

Based on the conversation history above, understand what the pilgrim is referring to and answer accordingly."""
    else:
        return current_message

def extract_name_from_message(message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Does this message contain a person's name being introduced? 
Message: "{message}"
If yes, reply with ONLY the name. If no, reply with NONE."""
            }],
            max_tokens=10,
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        if result and result.upper() != "NONE" and len(result) < 30:
            return result
        return None
    except Exception as e:
        logger.error(f"Name extraction error: {e}")
        return None

def is_follow_up(message: str, history: str) -> bool:
    if not history:
        return False
    follow_up_words = [
        "tell me more", "what about", "and then", "how about",
        "more details", "explain more", "what else", "how long",
        "how much", "when is it", "where is it", "can i", "is it",
        "that", "this", "it", "those", "these",
        "అది", "ఇది", "మరింత", "ఎంత", "ఎప్పుడు",
        "वह", "यह", "और", "कितना", "कब"
    ]
    message_lower = message.lower()
    return any(word in message_lower for word in follow_up_words)