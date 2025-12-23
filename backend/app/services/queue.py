import json
import os
from typing import Any, Dict, Optional

import boto3

INBOUND_QUEUE_URL = os.environ.get("INBOUND_QUEUE_URL")
OUTBOUND_QUEUE_URL = os.environ.get("OUTBOUND_QUEUE_URL")

sqs = boto3.client("sqs")


def enqueue_inbound(payload: Dict[str, Any]) -> bool:
    if not INBOUND_QUEUE_URL:
        return False
    sqs.send_message(QueueUrl=INBOUND_QUEUE_URL, MessageBody=json.dumps(payload))
    return True


def enqueue_outbound(payload: Dict[str, Any]) -> bool:
    if not OUTBOUND_QUEUE_URL:
        return False
    sqs.send_message(QueueUrl=OUTBOUND_QUEUE_URL, MessageBody=json.dumps(payload))
    return True


def enqueue_outbound_text(wa_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    payload: Dict[str, Any] = {"type": "send_text", "wa_id": wa_id, "text": text}
    if metadata:
        payload["metadata"] = metadata
    return enqueue_outbound(payload)
