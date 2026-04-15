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

def _call_groq(messages: list, retries: int = 2, wait: int = 5) -> str:
    """
    Calls Groq API with retry logic for 429 rate limit errors.
    Retries up to `retries` times with `wait` seconds between attempts.
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
                    logger.error("❌ Groq service unavailable — all retries exhausted")
                    return None

            else:
                logger.error(f"❌ Groq API error: {e}")
                return None

    return None


def answer_question(question: str) -> str:
    try:
        logger.info(f"🔍 Hybrid search for: {question}")

        # Use hybrid retrieval (Vector + BM25)
        relevant_chunks = search_hybrid(question, top_k=3)
        context = "\n\n".join(relevant_chunks)
        logger.info(f"📚 Found {len(relevant_chunks)} chunks via hybrid search")

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
            logger.warning("⚠️ Groq unavailable — returning fallback response")
            return FALLBACK_RESPONSE

        logger.info("✅ Answer generated via Hybrid RAG")
        return answer

    except Exception as e:
        logger.error(f"❌ QA error: {e}")
        return FALLBACK_RESPONSE