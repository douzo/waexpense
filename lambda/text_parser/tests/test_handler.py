import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import handler


class DummyBody:
    def __init__(self, payload: str):
        self._payload = payload

    def read(self):
        return self._payload.encode("utf-8")


class DummyBedrock:
    def __init__(self, response_text: str):
        self.response_text = response_text

    def invoke_model(self, modelId, body):
        payload = json.dumps({"outputs": [{"text": self.response_text}]})
        return {"body": DummyBody(payload)}


def test_ensure_schema_defaults():
    out = handler._ensure_schema({"amount": "12.5"}, "coffee")
    assert out["amount"] == 12.5
    assert out["currency"]
    assert out["category"]
    assert out["notes"] == "coffee"


def test_lambda_handler_parses_bedrock_response(monkeypatch):
    monkeypatch.setattr(
        handler,
        "bedrock",
        DummyBedrock(
            json.dumps(
                {
                    "amount": 10,
                    "currency": "USD",
                    "expense_date": "2025-01-01",
                    "category": "food",
                    "merchant": "Cafe",
                    "notes": "coffee",
                }
            )
        ),
    )

    event = {
        "body": json.dumps({"text": "coffee 10", "reference_date": "2025-01-01"})
    }
    res = handler.lambda_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["amount"] == 10.0
    assert body["expense_date"] == "2025-01-01"
