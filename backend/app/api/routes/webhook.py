import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from app.services.text_parser import parse_expense_text
from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str,
):
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: str | None = Header(None),
):
    body_bytes = await request.body()
    if x_hub_signature_256 and not whatsapp_service.verify_signature(
        body_bytes, x_hub_signature_256
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad signature")

    payload = await request.json()
    logger.debug("Received webhook payload: %s", payload)

    entries = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            for message in messages:
                await _handle_message(db, message, contacts)

    return {"status": "received"}


async def _handle_message(db: Session, message: Dict[str, Any], contacts: list[Dict[str, Any]]):
    msg_type = message.get("type")
    wa_id = None
    if contacts:
        wa_id = contacts[0].get("wa_id")

    if not wa_id:
        logger.warning("No wa_id found in message; skipping")
        return

    user = db.query(User).filter(User.whatsapp_id == wa_id).first()
    if not user:
        user = User(whatsapp_id=wa_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    if msg_type == "text":
        await _handle_text_message(db, user, message)
    else:
        await whatsapp_service.send_text_message(
            wa_id, "Thanks! Image and other message types will be supported soon."
        )


def _extract_text_body(message: Dict[str, Any]) -> str:
    text_obj = message.get("text", {})
    return text_obj.get("body", "").strip()


async def _handle_text_message(db: Session, user: User, message: Dict[str, Any]):
    body = _extract_text_body(message)
    parsed = parse_expense_text(body)

    confirmation = (
        f"Recorded expense: {parsed['amount']} {parsed['currency']} for {parsed['merchant']}"
        f" on {parsed['expense_date']}."
    )
    await whatsapp_service.send_text_message(user.whatsapp_id, confirmation)
