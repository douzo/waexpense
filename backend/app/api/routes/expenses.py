from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Expense
from app.services.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api")


def _serialize_expense(expense: Expense) -> dict:
    return {
        "id": str(expense.id),
        "user_id": str(expense.user_id),
        "amount": float(expense.amount),
        "currency": expense.currency,
        "category": expense.category,
        "merchant": expense.merchant,
        "notes": expense.notes,
        "expense_date": expense.expense_date.isoformat() if expense.expense_date else None,
        "receipt_id": str(expense.receipt_id) if expense.receipt_id else None,
        "created_at": expense.created_at.isoformat() if expense.created_at else None,
    }


@router.get("/expenses")
async def list_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
) -> dict:
    query = (
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
    )
    if category:
        query = query.where(Expense.category == category)

    expenses: List[Expense] = db.execute(query.limit(limit).offset(offset)).scalars().all()
    return {"items": [_serialize_expense(e) for e in expenses]}
