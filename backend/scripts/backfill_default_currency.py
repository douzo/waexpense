import sys
from pathlib import Path

from sqlalchemy import desc

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal
from app.models import Expense, User


def main() -> None:
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.default_currency.is_(None)).all()
        if not users:
            print("No users to backfill.")
            return

        updated = 0
        for user in users:
            latest = (
                db.query(Expense)
                .filter(Expense.user_id == user.id, Expense.currency.isnot(None))
                .order_by(desc(Expense.expense_date), desc(Expense.created_at))
                .first()
            )
            if not latest or not latest.currency:
                continue
            user.default_currency = latest.currency
            db.add(user)
            updated += 1

        db.commit()
        print(f"Updated {updated} user(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
