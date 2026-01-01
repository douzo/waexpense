from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Expense, User


def daily_limit_for_user(user: User) -> int:
    return settings.daily_limit_premium if user.is_premium else settings.daily_limit_free


def has_reached_daily_limit(db: Session, user: User, expense_date: date) -> bool:
    count = (
        db.query(func.count(Expense.id))
        .filter(Expense.user_id == user.id, Expense.expense_date == expense_date)
        .scalar()
    )
    return count >= daily_limit_for_user(user)
