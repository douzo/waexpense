from datetime import date
from decimal import Decimal
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
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

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    notes: Optional[str] = None
    expense_date: Optional[date] = None


class DevSeedBody(BaseModel):
    whatsapp_id: str = Field(..., min_length=5)
    amount: float = 12.5
    currency: str = "USD"
    category: str = "food"
    merchant: str = "Local Cafe"
    notes: str = "Dev seed"
    expense_date: Optional[date] = None


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


@router.patch("/expenses/{expense_id}")
async def update_expense(
    expense_id: str,
    body: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        expense_uuid = uuid.UUID(expense_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid expense id")

    expense: Optional[Expense] = (
        db.query(Expense)
        .filter(Expense.id == expense_uuid, Expense.user_id == current_user.id)
        .first()
    )
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    update = body.dict(exclude_unset=True)
    if "amount" in update:
        if update["amount"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount cannot be empty",
            )
        expense.amount = Decimal(str(update["amount"]))
    if "currency" in update and update["currency"]:
        expense.currency = update["currency"].upper()
    if "category" in update:
        expense.category = update["category"]
    if "merchant" in update:
        expense.merchant = update["merchant"]
    if "notes" in update:
        expense.notes = update["notes"]
    if "expense_date" in update:
        if update["expense_date"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense date cannot be empty",
            )
        expense.expense_date = update["expense_date"]

    db.commit()
    db.refresh(expense)
    return _serialize_expense(expense)


@router.post("/dev/seed")
async def dev_seed(
    body: DevSeedBody,
    db: Session = Depends(get_db),
) -> dict:
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user: Optional[User] = (
        db.query(User).filter(User.whatsapp_id == body.whatsapp_id).first()
    )
    if not user:
        user = User(whatsapp_id=body.whatsapp_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    expense_date = body.expense_date or date.today()
    expense = Expense(
        user_id=user.id,
        amount=Decimal(str(body.amount)),
        currency=body.currency.upper(),
        category=body.category,
        merchant=body.merchant,
        notes=body.notes,
        expense_date=expense_date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    return {
        "user_id": str(user.id),
        "expense": _serialize_expense(expense),
    }
