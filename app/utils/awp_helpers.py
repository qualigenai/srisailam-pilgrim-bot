from app.webhook.models import AWPArtifact
from app.multilingual.translator import translate_from_english
from app.utils.message_templates import get_disclaimer
from app.utils.session_store import add_to_history


def finalize_awp_artifact(data: str, lang: str, phone: str, confidence: float = 1.0) -> str:
    """Ensures every response is a guaranteed AWP Artifact."""
    # Translate if necessary
    final_text = data
    if lang != "en":
        final_text = translate_from_english(data, lang)

    # Append required business disclaimers
    final_text += get_disclaimer(lang)

    # Save to history and return as the final product [cite: 110]
    add_to_history(phone, "bot", final_text)
    return final_text