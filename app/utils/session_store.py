import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)

SESSION_TIMEOUT_HOURS = 24
MAX_HISTORY = 10  # max exchanges to keep

sessions = {}


def get_session(phone: str) -> Dict:
    if phone in sessions:
        session = sessions[phone]
        if datetime.now() - session["last_seen"] < timedelta(
            hours=SESSION_TIMEOUT_HOURS
        ):
            session["last_seen"] = datetime.now()
            return session
    sessions[phone] = {
        "phone": phone,
        "language": "en",
        "history": [],
        "name": None,
        "last_seen": datetime.now(),
        "ritual_flow": {}
    }
    return sessions[phone]


def get_user_language(phone: str) -> str:
    return get_session(phone).get("language", "en")


def set_user_language(phone: str, language: str):
    get_session(phone)["language"] = language
    logger.info(f"Language set for {phone}: {language}")


def add_to_history(phone: str, role: str, message: str):
    session = get_session(phone)

    # Always append new message
    session["history"].append({
        "role": role,
        "message": message,
        "time": datetime.now().isoformat()
    })

    # Trim to MAX_HISTORY pairs (user + bot = 2 entries per exchange)
    max_entries = MAX_HISTORY * 2
    if len(session["history"]) > max_entries:
        # Keep only the most recent entries
        session["history"] = session["history"][-max_entries:]

    logger.info(
        f"History updated for {phone}: "
        f"{len(session['history'])} messages"
    )


def get_history(phone: str) -> List[Dict]:
    return get_session(phone).get("history", [])


def get_history_as_text(phone: str) -> str:
    history = get_history(phone)
    if not history:
        return ""
    lines = []
    for h in history:
        role = "Pilgrim" if h["role"] == "user" else "Bot"
        lines.append(f"{role}: {h['message']}")
    return "\n".join(lines)


def set_user_name(phone: str, name: str):
    get_session(phone)["name"] = name
    logger.info(f"Name set for {phone}: {name}")


def get_user_name(phone: str) -> str:
    return get_session(phone).get("name")


def get_ritual_flow(phone: str) -> Dict:
    return get_session(phone).get("ritual_flow", {})


def set_ritual_flow(phone: str, state: Dict):
    get_session(phone)["ritual_flow"] = state


def clear_session(phone: str):
    if phone in sessions:
        del sessions[phone]
    logger.info(f"Session cleared for {phone}")


def cleanup_sessions():
    now = datetime.now()
    expired = [
        phone for phone, data in sessions.items()
        if now - data["last_seen"] > timedelta(hours=SESSION_TIMEOUT_HOURS)
    ]
    for phone in expired:
        del sessions[phone]
    if expired:
        logger.info(f"Cleaned {len(expired)} expired sessions")