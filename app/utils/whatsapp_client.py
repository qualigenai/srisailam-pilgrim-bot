import os
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)


def send_whatsapp_message(to: str, message: str):
    from twilio.rest import Client

    # Load fresh every time — never use cached client
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

    logger.info(f"Using SID: {account_sid[:10]}...")
    logger.info(f"Token length: {len(auth_token) if auth_token else 'MISSING'}")

    try:
        client = Client(account_sid, auth_token)
        to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        logger.info(f"✅ Message sent: {msg.sid}")
        return msg.sid
    except Exception as e:
        logger.error(f"❌ Failed to send: {e}")
        raise