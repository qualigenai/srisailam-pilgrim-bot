import logging

logger = logging.getLogger(__name__)

GREETING_MESSAGE = """🙏 ఓం నమః శివాయ! OM SREE MATREY NAMAHA! नमस्ते!

Welcome to Srisailam Pilgrim Guide!


I can help you with | నేను సహాయం చేయగలను:
- Temple timings | గుడి సమయాలు
- How to reach | ఎలా చేరుకోవాలి
- Sevas & rituals | సేవలు & పూజలు
- Festivals | పండుగలు
- Accommodation | వసతి

📱 Bookings: 9552300009 (Mana Mitra)
🌐 srisailadevasthanam.org
📞 08524-288888

Ask in Telugu, Hindi or English! 🕉️
తెలుగు, హిందీ లేదా ఇంగ్లీష్‌లో అడగండి!"""

def handle_greeting() -> str:
    logger.info("👋 Handling greeting")
    return GREETING_MESSAGE
