from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User

_SYMBOL_MAP = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
}

# Longest prefixes first for greedy match.
_COUNTRY_CURRENCY_PREFIX = [
    ("971", "AED"),
    ("966", "SAR"),
    ("65", "SGD"),
    ("62", "IDR"),
    ("63", "PHP"),
    ("61", "AUD"),
    ("91", "INR"),
    ("81", "JPY"),
    ("86", "CNY"),
    ("55", "BRL"),
    ("49", "EUR"),
    ("44", "GBP"),
    ("39", "EUR"),
    ("34", "EUR"),
    ("33", "EUR"),
    ("1", "USD"),
]


def _normalize_currency(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw in _SYMBOL_MAP:
        return _SYMBOL_MAP[raw]
    return raw.upper()


def _infer_currency_from_wa_id(wa_id: Optional[str]) -> Optional[str]:
    if not wa_id:
        return None
    digits = "".join(ch for ch in wa_id if ch.isdigit())
    if not digits:
        return None
    for prefix, currency in _COUNTRY_CURRENCY_PREFIX:
        if digits.startswith(prefix):
            return currency
    return None


def resolve_currency(
    db: Session,
    user: User,
    parsed_currency: Optional[str],
    wa_id: Optional[str],
) -> str:
    normalized = _normalize_currency(parsed_currency)
    if normalized:
        if user.default_currency != normalized:
            user.default_currency = normalized
            db.add(user)
            db.commit()
            db.refresh(user)
        return normalized

    if user.default_currency:
        return user.default_currency

    inferred = _infer_currency_from_wa_id(wa_id)
    resolved = inferred or settings.default_currency
    user.default_currency = resolved
    db.add(user)
    db.commit()
    db.refresh(user)
    return resolved
