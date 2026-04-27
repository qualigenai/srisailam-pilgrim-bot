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

# Conjunctions that split multi-intent queries
SPLIT_CONJUNCTIONS = [
    " and ", " also ", " plus ", " as well as ",
    "? and", "? also", ", and ", " & ",
    " మరియు ", " కూడా ",
    " और ", " भी "
]


def extract_search_query(question: str) -> str:
    """Extract clean user message — strip injected context."""
    if "Current message:" in question:
        parts = question.split("Current message:")
        clean = parts[-1].strip()
        if "\n" in clean:
            clean = clean.split("\n")[0].strip()
        return clean
    if "Based on the conversation" in question:
        parts = question.split("Based on the conversation")
        return parts[0].strip()
    return question.strip()


def split_multi_intent_query(query: str) -> list:
    """
    Split compound queries into sub-queries for parallel RAG search.
    e.g. 'darshan timings and bus from hyd?' →
         ['darshan timings', 'bus from hyd']
    """
    query_lower = query.lower()
    sub_queries = [query]  # default — single query

    for conjunction in SPLIT_CONJUNCTIONS:
        if conjunction in query_lower:
            parts = query_lower.split(conjunction, 1)
            part_a = parts[0].strip().rstrip("?").strip()
            part_b = parts[1].strip().rstrip("?").strip()
            if len(part_a) > 3 and len(part_b) > 3:
                sub_queries = [part_a, part_b]
                logger.info(
                    f"🔀 Multi-intent detected: "
                    f"'{part_a}' + '{part_b}'"
                )
                break

    return sub_queries


def search_multi_intent(query: str, top_k: int = 3) -> str:
    """
    Run parallel RAG searches for multi-intent queries.
    Merges and deduplicates results before returning context.
    """
    sub_queries = split_multi_intent_query(query)
    all_chunks = []
    seen = set()

    for sub_query in sub_queries:
        logger.info(f"🔍 Hybrid search for: {sub_query}")
        chunks = search_hybrid(sub_query, top_k=top_k)
        for chunk in chunks:
            # Deduplicate by first 100 chars
            key = chunk[:100]
            if key not in seen:
                seen.add(key)
                all_chunks.append(chunk)

    logger.info(
        f"📚 Found {len(all_chunks)} chunks "
        f"({len(sub_queries)} sub-queries)"
    )
    return "\n\n".join(all_chunks)


def _call_groq(messages: list, retries: int = 2, wait: int = 5) -> str:
    """Groq API call with retry logic for 429 rate limit errors."""
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
                    f"⚠️ Groq rate limit (attempt {attempt}/{retries}) "
                    f"— waiting {wait}s"
                )
                if attempt < retries:
                    time.sleep(wait)
                    continue
                logger.error("❌ Rate limit — all retries exhausted")
                return None
            elif "503" in error_str or "502" in error_str:
                logger.warning(
                    f"⚠️ Groq unavailable (attempt {attempt}/{retries}) "
                    f"— waiting {wait}s"
                )
                if attempt < retries:
                    time.sleep(wait)
                    continue
                logger.error("❌ Service unavailable — all retries exhausted")
                return None
            else:
                logger.error(f"❌ Groq API error: {e}")
                return None
    return None


def answer_question(question: str) -> str:
    try:
        # ── Extract clean query for RAG search ──
        search_query = extract_search_query(question)

        # ── Multi-intent parallel RAG search ──
        context = search_multi_intent(search_query)

        # ── LLM receives full question + merged context ──
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
- If asking multiple questions, answer each one
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