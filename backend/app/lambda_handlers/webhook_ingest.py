import asyncio
import base64
import json
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.queue import enqueue_inbound, enqueue_outbound_text
from app.services.text_parser import parse_expense_text
from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)


def _run_async(coro):
    return asyncio.run(coro)


def _extract_text_body(message: Dict[str, Any]) -> str:
    text_obj = message.get("text", {})
    return text_obj.get("body", "").strip()


def _normalize_parsed(
    parsed: Dict[str, Any], original_text: str, reference_date: Optional[date]
) -> Dict[str, Any]:
    amount = parsed.get("amount")
    if isinstance(amount, Decimal):
        amount = float(amount)

    expense_date = parsed.get("expense_date")
    if isinstance(expense_date, date):
        expense_date = expense_date.isoformat()
    elif expense_date is None:
        expense_date = (reference_date or date.today()).isoformat()

    return {
        "amount": amount,
        "currency": parsed.get("currency"),
        "category": parsed.get("category"),
        "merchant": parsed.get("merchant"),
        "notes": parsed.get("notes") or original_text,
        "expense_date": expense_date,
    }


def _handle_webhook_payload(
    payload: Dict[str, Any],
    raw_body: bytes,
    x_hub_signature_256: Optional[str],
) -> Dict[str, Any]:
    if x_hub_signature_256:
        if not whatsapp_service.verify_signature(raw_body, x_hub_signature_256):
            return {"statusCode": 403, "body": json.dumps({"error": "Bad signature"})}

    entries: List[Dict[str, Any]] = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            for message in messages:
                _handle_message(message, contacts)

    return {"statusCode": 200, "body": json.dumps({"status": "received"})}


def _message_reference_date(message: Dict[str, Any]) -> Optional[date]:
    timestamp = message.get("timestamp")
    if not timestamp:
        return None
    try:
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).date()
    except (ValueError, TypeError):
        return None


def _handle_message(message: Dict[str, Any], contacts: List[Dict[str, Any]]):
    msg_type = message.get("type")
    wa_id = message.get("from") or (contacts[0].get("wa_id") if contacts else None)

    if not wa_id:
        logger.warning("No wa_id found in message; skipping. Message: %s", message)
        return

    if msg_type != "text":
        enqueue_outbound_text(
            wa_id, "Thanks! Image and other message types will be supported soon."
        )
        return

    body = _extract_text_body(message)
    reference_date = _message_reference_date(message)
    parsed = _run_async(parse_expense_text(body, reference_date=reference_date))
    normalized = _normalize_parsed(parsed, body, reference_date)

    payload = {"type": "expense", "wa_id": wa_id, "expense": normalized}
    enqueue_inbound(payload)


def _verify_webhook(query: Dict[str, str]) -> Dict[str, Any]:
    hub_mode = query.get("hub.mode")
    hub_verify_token = query.get("hub.verify_token")
    hub_challenge = query.get("hub.challenge")

    if not hub_mode or not hub_verify_token or not hub_challenge:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing hub parameters"}),
        }

    expected_token = settings.whatsapp_verify_token
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return {"statusCode": 200, "body": hub_challenge}

    return {"statusCode": 403, "body": json.dumps({"error": "Verification failed"})}


def lambda_handler(event, context):
    request_context = event.get("requestContext", {})
    method = request_context.get("http", {}).get("method")

    if method == "GET":
        return _verify_webhook(event.get("queryStringParameters") or {})

    if method != "POST":
        return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}

    raw_body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw_body_bytes = base64.b64decode(raw_body)
        raw_body = raw_body_bytes.decode("utf-8")
    else:
        raw_body_bytes = raw_body.encode("utf-8")
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    signature = headers.get("x-hub-signature-256")

    return _handle_webhook_payload(payload, raw_body_bytes, signature)
