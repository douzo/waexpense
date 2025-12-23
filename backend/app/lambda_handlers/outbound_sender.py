import asyncio
import json
import logging

from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)


def _handle_message(body):
    if body.get("type") != "send_text":
        logger.warning("Unsupported outbound message type: %s", body.get("type"))
        return

    wa_id = body.get("wa_id")
    text = body.get("text")
    if not wa_id or not text:
        logger.warning("Missing wa_id or text for outbound message")
        return

    asyncio.run(whatsapp_service.send_text_message(wa_id, text))


def lambda_handler(event, context):
    for record in event.get("Records", []):
        body = json.loads(record.get("body", "{}"))
        _handle_message(body)
