from datetime import date
import uuid
from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/expenses")
async def list_expenses():
    # Dummy payload until DB integration is ready
    return {
        "items": [
            {
                "id": str(uuid.uuid4()),
                "merchant": "Demo Grocery",
                "category": "grocery",
                "amount": 23.5,
                "currency": "USD",
                "expense_date": date.today().isoformat(),
            }
        ]
    }
