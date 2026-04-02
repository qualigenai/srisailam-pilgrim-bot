import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory session store
# Stores last detected language per user
sessions = {}
SESSION_TIMEOUT_HOURS = 24

def get_user_language(phone: str) -> str:
    try:
        if phone in sessions:
            session = sessions[phone]
            if datetime.now() - session["last_seen"] < timedelta(hours=SESSION_TIMEOUT_HOURS):
                return session["language"]
        return "en"
    except Exception as e:
        logger.error(f"❌ Session error: {e}")
        return "en"

def set_user_language(phone: str, language: str):
    try:
        sessions[phone] = {
            "language": language,
            "last_seen": datetime.now()
        }
        logger.info(f"✅ Session set for {phone}: {language}")
    except Exception as e:
        logger.error(f"❌ Session error: {e}")

def cleanup_sessions():
    try:
        now = datetime.now()
        expired = [
            phone for phone, data in sessions.items()
            if now - data["last_seen"] > timedelta(hours=SESSION_TIMEOUT_HOURS)
        ]
        for phone in expired:
            del sessions[phone]
        logger.info(f"🧹 Cleaned {len(expired)} expired sessions")
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")