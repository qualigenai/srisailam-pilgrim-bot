from fastapi import APIRouter, Request
from fastapi.responses import Response
from app.utils.whatsapp_client import send_whatsapp_message
from app.agents.orchestrator import process_message
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook")
async def receive_message(request: Request):
    try:
        # Twilio sends data as form-url-encoded
        body = await request.form()
        form_dict = dict(body)

        sender_phone = form_dict.get("From")
        message_body = form_dict.get("Body")

        logger.info(f"📩 From: {sender_phone} | Body: {message_body}")

        if not sender_phone or not message_body:
            return Response(status_code=200)

        # process_message now handles logging internally via AWPAuditor
        answer = process_message(message_body, sender_phone)

        send_whatsapp_message(to=sender_phone, message=answer)
        logger.info(f"✅ Reply sent to {sender_phone}")

        return Response(status_code=200)

    except Exception as e:
        logger.error(f"❌ Webhook Error: {e}")
        return Response(status_code=200)