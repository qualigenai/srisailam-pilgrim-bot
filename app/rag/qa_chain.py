from groq import Groq
from app.rag.hybrid_retriever import search_hybrid
from app.utils.config import GROQ_API_KEY, LLM_MODEL, MAX_TOKENS, TEMPERATURE
import logging
import time

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a helpful and knowledgeable pilgrim guide for Srisailam temple — one of the twelve Jyotirlingas of Lord Shiva in Andhra Pradesh, India.

Your role is to help devotees with accurate information about:
- Temple timings and darshan types
- How to reach Srisailam
- Sevas and rituals
- Significance of Mallikarjuna Swamy and Bhramarambika Devi
- Accommodation and facilities
- Festivals and auspicious days

Always respond with warmth and devotion. Start responses with 🙏.
If you don't know something, say so honestly and suggest visiting srisailadevasthanam.org for official information.
For booking darshan or sevas, always direct devotees to srisailadevasthanam.org or Mana Mitra WhatsApp (9552300009).
Keep responses concise and clear — suitable for WhatsApp messages.
Never make up information."""

FALLBACK_RESPONSE = "🙏 Temple information is temporarily unavailable. Please visit srisailadevasthanam.org or call 08524-288888 for accurate details."


def extract_search_query(question: str) -> str:
    """
    Extracts only the current user message for RAG search.
    Strips away conversation history/context that was injected
    by build_context_prompt in memory_agent.py.
    """
    # If context was injected, extract only "Current message:" part
    if "Current message:" in question:
        parts = question.split("Current message:")
        clean = parts[-1].strip()
        # Remove any trailing instructions
        if "\n" in clean:
            clean = clean.split("\n")[0].strip()
        return clean

    # If "Based on the conversation" injected — strip it
    if "Based on the conversation" in question:
        parts = question.split("Based on the conversation")
        # Take only the part before this instruction
        return parts[0].strip()

    # No context injection — return as-is
    return question.strip()


def _call_groq(messages: list, retries: int = 2, wait: int = 5) -> str:
    """
    Calls Groq API with retry logic for 429 rate limit errors.
    """
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e)

            if "429" in error_str:
                logger.warning(
                    f"⚠️ Groq rate limit hit (attempt {attempt}/{retries}) "
                    f"— waiting {wait}s before retry"
                )
                if attempt < retries:
                    time.sleep(wait)
                    continue
                else:
                    logger.error("❌ Groq rate limit — all retries exhausted")
                    return None

            elif "503" in error_str or "502" in error_str:
                logger.warning(
                    f"⚠️ Groq service unavailable (attempt {attempt}/{retries}) "
                    f"— waiting {wait}s"
                )
                if attempt < retries:
                    time.sleep(wait)
                    continue
                else:
                    logger.error("❌ Groq unavailable — all retries exhausted")
                    return None

            else:
                logger.error(f"❌ Groq API error: {e}")
                return None

    return None


def answer_question(question: str) -> str:
    try:
        # ── Extract clean query for RAG search ──
        search_query = extract_search_query(question)
        logger.info(f"🔍 Hybrid search for: {search_query}")

        # ── Use clean query for RAG retrieval ──
        relevant_chunks = search_hybrid(search_query, top_k=3)
        context = "\n\n".join(relevant_chunks)
        logger.info(f"📚 Found {len(relevant_chunks)} chunks via hybrid search")

        # ── Use full question (with history) for LLM answer generation ──
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Based ONLY on the following information about Srisailam temple, answer the devotee's question.

Context:
{context}

Devotee's question: {question}

IMPORTANT RULES:
- Answer ONLY if the context contains relevant information
- If context is not relevant say: "🙏 I don't have specific information about that. Please visit srisailadevasthanam.org or call 08524-288888 for accurate details."
- Never make up information
- Keep answer concise for WhatsApp"""
            }
        ]

        answer = _call_groq(messages)

        if answer is None:
            logger.warning("⚠️ Groq unavailable — returning fallback")
            return FALLBACK_RESPONSE

        logger.info("✅ Answer generated via Hybrid RAG")
        return answer

    except Exception as e:
        logger.error(f"❌ QA error: {e}")
        return FALLBACK_RESPONSE