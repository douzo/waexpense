from datetime import date
from decimal import Decimal

from app.models import Expense, User
from app.services.currency import resolve_currency
from app.services.limits import daily_limit_for_user, has_reached_daily_limit


def test_currency_resolve_uses_parsed_and_sets_default(db_session):
    user = User(whatsapp_id="15551234567")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    resolved = resolve_currency(db_session, user, "eur", user.whatsapp_id)
    assert resolved == "EUR"

    db_session.refresh(user)
    assert user.default_currency == "EUR"


def test_currency_resolve_uses_existing_default(db_session):
    user = User(whatsapp_id="15551234567", default_currency="JPY")
    db_session.add(user)
    db_session.commit()

    resolved = resolve_currency(db_session, user, None, user.whatsapp_id)
    assert resolved == "JPY"


def test_currency_resolve_falls_back_to_wa_id(db_session):
    user = User(whatsapp_id="919876543210")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    resolved = resolve_currency(db_session, user, None, user.whatsapp_id)
    assert resolved == "INR"


def test_daily_limit_for_user(db_session):
    free_user = User(whatsapp_id="15550001111", is_premium=False)
    premium_user = User(whatsapp_id="15550002222", is_premium=True)
    db_session.add_all([free_user, premium_user])
    db_session.commit()

    assert daily_limit_for_user(free_user) == 10
    assert daily_limit_for_user(premium_user) == 50


def test_has_reached_daily_limit(db_session):
    user = User(whatsapp_id="15550003333", is_premium=False)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    for _ in range(10):
        expense = Expense(
            user_id=user.id,
            amount=Decimal("1.00"),
            currency="USD",
            category="food",
            merchant="Cafe",
            notes="Test",
            expense_date=date.today(),
        )
        db_session.add(expense)
    db_session.commit()

    assert has_reached_daily_limit(db_session, user, date.today())


def test_admin_toggle_premium(client, db_session):
    user = User(whatsapp_id="15550004444", is_premium=False)
    db_session.add(user)
    db_session.commit()

    res = client.patch(
        "/api/admin/users/15550004444/premium",
        headers={"X-Admin-Token": "test-admin-key"},
        json={"is_premium": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_premium"] is True


def test_admin_requires_token(client, db_session):
    user = User(whatsapp_id="15550005555", is_premium=False)
    db_session.add(user)
    db_session.commit()

    res = client.patch(
        "/api/admin/users/15550005555/premium",
        json={"is_premium": True},
    )
    assert res.status_code == 403
