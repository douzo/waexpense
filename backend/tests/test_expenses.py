from datetime import date
from decimal import Decimal

from app.api.routes.auth import _create_jwt
from app.models import Expense, User


def test_list_expenses(client, db_session):
    user = User(whatsapp_id="18887776666")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    expense = Expense(
        user_id=user.id,
        amount=Decimal("12.50"),
        currency="USD",
        category="food",
        merchant="Cafe",
        notes="Latte",
        expense_date=date.today(),
    )
    db_session.add(expense)
    db_session.commit()

    token = _create_jwt(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/expenses", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["merchant"] == "Cafe"


def test_update_expense(client, db_session):
    user = User(whatsapp_id="17776665555")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    expense = Expense(
        user_id=user.id,
        amount=Decimal("20.00"),
        currency="USD",
        category="food",
        merchant="Deli",
        notes="Sandwich",
        expense_date=date.today(),
    )
    db_session.add(expense)
    db_session.commit()
    db_session.refresh(expense)

    token = _create_jwt(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.patch(
        f"/api/expenses/{expense.id}",
        json={"amount": 25.5, "merchant": "New Deli"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["amount"] == 25.5
    assert data["merchant"] == "New Deli"
