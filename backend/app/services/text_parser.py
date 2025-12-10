import re
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional

CURRENCY_PATTERN = r"(?P<currency>[A-Za-z]{3}|\$|€|£|¥|₹)"
AMOUNT_PATTERN = r"(?P<amount>\d+[.,]?\d*)"
DATE_PATTERNS = [
    r"(?P<date>\d{4}-\d{2}-\d{2})",
    r"(?P<date>\d{2}/\d{2}/\d{4})",
]

CATEGORY_KEYWORDS = {
    "grocery": {"market", "grocery", "supermarket"},
    "transport": {"uber", "taxi", "train", "bus"},
    "food": {"dinner", "lunch", "breakfast", "restaurant"},
}


def parse_expense_text(message: str) -> Dict[str, Optional[str]]:
    lowered = message.lower()

    currency_match = re.search(CURRENCY_PATTERN, message)
    amount_match = re.search(AMOUNT_PATTERN, message)

    parsed_date = _extract_date(message)

    category = None
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(word in lowered for word in keywords):
            category = cat
            break

    merchant = None
    tokens = message.split()
    if tokens:
        merchant = tokens[0].strip()

    currency = None
    if currency_match:
        currency = currency_match.group("currency")

    amount = None
    if amount_match:
        amount_raw = amount_match.group("amount").replace(",", "")
        amount = Decimal(amount_raw)

    return {
        "amount": amount,
        "currency": currency or "USD",
        "expense_date": parsed_date or date.today(),
        "category": category or "general",
        "merchant": merchant,
        "notes": message,
    }


def _extract_date(message: str) -> Optional[date]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, message)
        if match:
            raw_date = match.group("date")
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(raw_date, fmt).date()
                except ValueError:
                    continue
    return None
