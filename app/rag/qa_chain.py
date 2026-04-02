from groq import Groq
from app.rag.vectorstore import search_vectorstore
from app.utils.config import GROQ_API_KEY, LLM_MODEL, MAX_TOKENS, TEMPERATURE
import logging

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

def answer_question(question: str) -> str:
    try:
        logger.info(f"🔍 Searching knowledge base for: {question}")
        relevant_chunks = search_vectorstore(question, top_k=3)
        context = "\n\n".join(relevant_chunks)
        logger.info(f"📚 Found {len(relevant_chunks)} relevant chunks")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Based ONLY on the following information about Srisailam temple, answer the devotee's question.

Context:
{context}

Devotee's question: {question}

IMPORTANT RULES:
- Answer ONLY if the context contains relevant information
- If the context does not contain relevant information, say exactly:
  "🙏 I don't have specific information about that. Please visit srisailadevasthanam.org or call 08524-288888 for accurate details."
- Never make up information
- Never answer questions unrelated to Srisailam temple
- Keep answer concise and clear for WhatsApp"""}
        ]

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )

        answer = response.choices[0].message.content
        logger.info("✅ Answer generated")
        return answer

    except Exception as e:
        logger.error(f"❌ QA error: {e}")
        return "🙏 Sorry, I couldn't process your question right now. Please visit srisailadevasthanam.org or call 08524-288888."