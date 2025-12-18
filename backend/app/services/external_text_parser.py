import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def call_external_text_parser(message: str) -> Optional[Dict[str, Any]]:
    """
    Optional integration point for an external text parser service.

    You can point EXTERNAL_TEXT_PARSER_URL at:
    - An AWS Lambda / API Gateway endpoint using Comprehend / Bedrock.
    - A Google Cloud Run / Cloud Functions endpoint using Cloud NL / Vertex AI.

    Expected response JSON shape:
    {
      "amount": 23.5,
      "currency": "USD",
      "expense_date": "2024-05-01",
      "category": "food",
      "merchant": "Uber",
      "notes": "original message or cleaned summary"
    }
    """
    if not settings.external_text_parser_url:
        return None

    payload = {"text": message}
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if settings.external_text_parser_api_key:
        headers["Authorization"] = f"Bearer {settings.external_text_parser_api_key}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                settings.external_text_parser_url, json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.error("External text parser call failed: %s", exc)
        return None

    # Basic validation: ensure required keys exist; let local parser fill gaps if needed.
    required_keys = {"amount", "currency", "expense_date", "category", "merchant", "notes"}
    if not required_keys.issubset(data.keys()):
        logger.warning(
            "External text parser returned incomplete data: keys=%s", list(data.keys())
        )
        return None

    return data


