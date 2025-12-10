import hmac
import json
import logging
from hashlib import sha256
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = "https://graph.facebook.com/v18.0"

    def verify_signature(self, body: bytes, signature: str) -> bool:
        expected = hmac.new(
            settings.whatsapp_app_secret.encode(), body, sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def send_text_message(self, wa_id: str, text: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": wa_id,
            "type": "text",
            "text": {"body": text},
        }

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                logger.error("Failed to send WhatsApp message: %s", exc)
                return None


whatsapp_service = WhatsAppService(
    access_token=settings.whatsapp_access_token,
    phone_number_id=settings.whatsapp_phone_number_id,
)
