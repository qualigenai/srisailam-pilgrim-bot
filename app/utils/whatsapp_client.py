import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to: str, message: str):
    try:
        to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_number
        )
        logger.info(f"✅ Message sent: {msg.sid}")
        return msg.sid
    except Exception as e:
        logger.error(f"❌ Failed to send: {e}")
        raise