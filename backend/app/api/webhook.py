import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import Expense, User
from app.services.currency import resolve_currency
from app.services.limits import daily_limit_for_user, has_reached_daily_limit
from app.services.text_parser import parse_expense_text
from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


def _verify_webhook_logic(hub_mode: str, hub_verify_token: str, hub_challenge: str):
    """Shared webhook verification logic."""
    expected_token = settings.whatsapp_verify_token
    token_match = hub_verify_token == expected_token
    
    logger.info(
        "Webhook verification attempt: mode=%s, received_token=%s, expected_token=%s, match=%s",
        hub_mode,
        hub_verify_token[:10] + "..." if len(hub_verify_token) > 10 else hub_verify_token,
        expected_token[:10] + "..." if len(expected_token) > 10 else expected_token,
        token_match
    )
    
    if hub_mode == "subscribe" and token_match:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)
    else:
        logger.warning(
            "Webhook verification failed: mode=%s (expected 'subscribe'), token_match=%s",
            hub_mode,
            token_match
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    """
    Webhook verification endpoint for Meta's initial challenge.
    Meta will call GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
    """
    return _verify_webhook_logic(hub_mode, hub_verify_token, hub_challenge)



async def _handle_webhook_payload(
    request: Request,
    db: Session,
    x_hub_signature_256: Optional[str],
):
    """
    Shared webhook payload handling logic.
    Processes incoming WhatsApp messages and creates expenses.
    """
    body_bytes = await request.body()
    
    # Verify signature if provided (Meta sends it with "sha256=" prefix)
    if x_hub_signature_256:
        if not whatsapp_service.verify_signature(body_bytes, x_hub_signature_256):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad signature")

    # Parse JSON payload
    import json
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error("Failed to parse webhook JSON: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")
    
    logger.info("Received webhook payload: %s", payload)

    entries: List[Dict[str, Any]] = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            for message in messages:
                await _handle_message(db, message, contacts)

    return {"status": "received"}


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """
    WhatsApp webhook entry point for incoming messages at /webhook.
    - Verifies X-Hub-Signature-256 if provided.
    - Parses messages and creates expenses.
    """
    return await _handle_webhook_payload(request, db, x_hub_signature_256)




def _message_reference_date(message: Dict[str, Any]) -> Optional[date]:
    timestamp = message.get("timestamp")
    if not timestamp:
        return None
    try:
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).date()
    except (ValueError, TypeError):
        return None


async def _handle_message(db: Session, message: Dict[str, Any], contacts: List[Dict[str, Any]]):
    msg_type = message.get("type")
    # Meta sends wa_id in message["from"] field, fallback to contacts if available
    wa_id = message.get("from") or (contacts[0].get("wa_id") if contacts else None)

    if not wa_id:
        logger.warning("No wa_id found in message; skipping. Message: %s", message)
        return

    user = db.query(User).filter(User.whatsapp_id == wa_id).first()
    if not user:
        user = User(whatsapp_id=wa_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    if msg_type == "text":
        reference_date = _message_reference_date(message)
        await _handle_text_message(db, user, message, reference_date)
    else:
        from app.services.queue import enqueue_outbound_text

        fallback = "Thanks! Image and other message types will be supported soon."
        if not enqueue_outbound_text(wa_id, fallback):
            await whatsapp_service.send_text_message(wa_id, fallback)


def _extract_text_body(message: Dict[str, Any]) -> str:
    text_obj = message.get("text", {})
    return text_obj.get("body", "").strip()


async def _handle_text_message(
    db: Session, user: User, message: Dict[str, Any], reference_date: Optional[date]
):
    body = _extract_text_body(message)
    parsed = await parse_expense_text(body, reference_date=reference_date)

    amount = parsed.get("amount")
    if not amount or amount <= 0:
        logger.info("No valid amount found in message '%s'; skipping expense creation", body)
        await whatsapp_service.send_text_message(
            user.whatsapp_id,
            "I couldn't find a valid amount in that message. Please include something like 'Lunch 12 USD'.",
        )
        return

    currency = resolve_currency(db, user, parsed.get("currency"), user.whatsapp_id)
    parsed["currency"] = currency

    expense_date = parsed["expense_date"]
    if has_reached_daily_limit(db, user, expense_date):
        limit = daily_limit_for_user(user)
        await whatsapp_service.send_text_message(
            user.whatsapp_id,
            f"You've reached your daily limit of {limit} expenses. Try again tomorrow or upgrade for a higher limit.",
        )
        return

    expense = Expense(
        user_id=user.id,
        amount=amount,
        currency=currency,
        category=parsed["category"],
        merchant=parsed["merchant"],
        notes=parsed["notes"],
        expense_date=expense_date,
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    confirmation = (
        f"Recorded expense: {expense.amount} {expense.currency}"
        f" for {expense.merchant or 'your expense'} on {expense.expense_date}."
    )
    from app.services.queue import enqueue_outbound_text

    if not enqueue_outbound_text(user.whatsapp_id, confirmation):
        await whatsapp_service.send_text_message(user.whatsapp_id, confirmation)
