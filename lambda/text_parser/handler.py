import json
import os
from datetime import date
from decimal import Decimal
from typing import Any, Dict

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "mistral.mistral-7b-instruct-v0:2")
DEFAULT_CURRENCY = os.environ.get("DEFAULT_CURRENCY", "USD")
DEFAULT_CATEGORY = os.environ.get("DEFAULT_CATEGORY", "general")
ALLOWED_CATEGORIES = {
    value.strip().lower()
    for value in os.environ.get(
        "ALLOWED_CATEGORIES", "grocery,food,transport,shopping,general"
    ).split(",")
    if value.strip()
}
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "256"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.1"))

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def _ensure_schema(obj: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    """Normalize and fill defaults so FastAPI always gets a valid object."""
    out: Dict[str, Any] = {}

    # amount
    amt = obj.get("amount")
    try:
        if amt is not None:
            out["amount"] = float(Decimal(str(amt)))
        else:
            out["amount"] = None
    except Exception:
        out["amount"] = None

    # currency
    cur = obj.get("currency")
    if cur is None or str(cur).strip() == "":
        out["currency"] = None
    else:
        out["currency"] = str(cur).upper()

    # date
    d = obj.get("expense_date") or date.today().isoformat()
    out["expense_date"] = str(d)

    # category
    cat = (obj.get("category") or DEFAULT_CATEGORY).lower()
    if cat not in ALLOWED_CATEGORIES:
        cat = DEFAULT_CATEGORY
    out["category"] = cat

    # merchant
    merch = obj.get("merchant")
    out["merchant"] = merch if merch is not None else None

    # notes
    out["notes"] = obj.get("notes") or original_text

    return out


def lambda_handler(event, context):
    # Expect JSON body { "text": "..." } via API Gateway
    if "body" in event:
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}
    else:
        body = event

    text = body.get("text")
    if not text:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing 'text'"})}

    reference_date = body.get("reference_date")
    if isinstance(reference_date, str):
        today = reference_date
    else:
        today = date.today().isoformat()

    prompt = f"""
You are an expense extraction engine.

Input: a short human message describing a personal expense.
Output: a single JSON object with exactly these fields:

- amount (number) – total amount spent
- currency (string or null) – 3-letter ISO code (e.g. "USD", "JPY", "INR"); use null if not specified
- expense_date (string) – ISO date "YYYY-MM-DD"; use "{today}" if not specified
- category (string) – one of: "grocery", "food", "transport", "shopping", "general"
- merchant (string or null) – store/provider name if present, otherwise null
- notes (string) – copy of the original message

Rules:
- Infer currency from symbols or words (e.g. "JPY", "¥", "yen" → "JPY"; "rupee", "rupees", "rs" → "INR").
- If the user does NOT specify currency, set currency to null.
- For transport (bus, train, taxi, uber, shinkansen, metro, subway, etc.) use category "transport".
- For fruits, vegetables, supermarket, groceries (apple, kg, grocery, supermarket, market, etc.) use category "grocery".
- For meals (dinner, lunch, breakfast, restaurant, cafe) use category "food".
- If you cannot infer a merchant, use null.
- Always return ONLY a valid JSON object, no explanations, no markdown.

Example input: "2kg apples 200 rupees"
Example output:
{{"amount": 200.0, "currency": "INR", "expense_date": "{today}", "category": "grocery", "merchant": null, "notes": "2kg apples 200 rupees"}}

Now process this input: "{text}"
"""

    # Mistral instruct models on Bedrock use a simple prompt + max_tokens schema
    request_body = {
        "prompt": prompt,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    try:
        resp = bedrock.invoke_model(modelId=MODEL_ID, body=json.dumps(request_body))
        raw_body = resp["body"].read().decode("utf-8")
        model_out = json.loads(raw_body)
        assistant_text = model_out.get("outputs", [{}])[0].get("text", "")
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Bedrock invocation failed: {str(e)}"}),
        }

    # Try to parse the model's JSON
    try:
        parsed_obj = json.loads(assistant_text)
    except Exception:
        # Try to salvage JSON substring
        try:
            start = assistant_text.index("{")
            end = assistant_text.rindex("}") + 1
            parsed_obj = json.loads(assistant_text[start:end])
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Failed to parse model JSON: {str(e)}"}),
            }

    normalized = _ensure_schema(parsed_obj, text)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(normalized),
    }
