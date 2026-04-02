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
        body = await request.form()
        form_dict = dict(body)

        From = form_dict.get("From")
        Body = form_dict.get("Body")

        logger.info(f"📩 From: {From} | Body: {Body}")

        if not From or not Body:
            return Response(status_code=200)

        # Pass phone number for session tracking
        answer = process_message(Body, From)
        send_whatsapp_message(to=From, message=answer)
        logger.info("✅ Reply sent!")
        return Response(status_code=200)

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return Response(status_code=200)
