import json
import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Expense, User
from app.services.queue import enqueue_outbound_text

logger = logging.getLogger(__name__)


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _persist_expense(db: Session, wa_id: str, expense: Dict[str, Any]) -> Expense:
    user = db.query(User).filter(User.whatsapp_id == wa_id).first()
    if not user:
        user = User(whatsapp_id=wa_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    amount = expense.get("amount")
    if amount is not None:
        amount = Decimal(str(amount))

    expense_date = _parse_date(expense.get("expense_date")) or date.today()

    record = Expense(
        user_id=user.id,
        amount=amount,
        currency=expense.get("currency"),
        category=expense.get("category"),
        merchant=expense.get("merchant"),
        notes=expense.get("notes"),
        expense_date=expense_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _handle_record(db: Session, body: Dict[str, Any]):
    if body.get("type") != "expense":
        logger.warning("Unknown message type: %s", body.get("type"))
        return

    wa_id = body.get("wa_id")
    expense = body.get("expense") or {}
    if not wa_id:
        logger.warning("Missing wa_id; skipping message")
        return

    if expense.get("amount") is None:
        enqueue_outbound_text(
            wa_id,
            "I couldn't find an amount in that message. Please include something like 'Lunch 12 USD'.",
        )
        return

    record = _persist_expense(db, wa_id, expense)
    confirmation = (
        f"Recorded expense: {record.amount} {record.currency}"
        f" for {record.merchant or 'your expense'} on {record.expense_date}."
    )
    enqueue_outbound_text(wa_id, confirmation)


def lambda_handler(event, context):
    db = SessionLocal()
    try:
        for record in event.get("Records", []):
            body = json.loads(record.get("body", "{}"))
            _handle_record(db, body)
    finally:
        db.close()
