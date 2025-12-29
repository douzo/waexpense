from datetime import datetime, timedelta, timezone

from app.api.routes.auth import _create_jwt, _create_refresh_token
from app.models import LoginToken, User


def test_verify_code_returns_tokens(client, db_session):
    user = User(whatsapp_id="15551234567")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = LoginToken(
        user_id=user.id,
        code="123456",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db_session.add(token)
    db_session.commit()

    res = client.post(
        "/auth/verify-code",
        json={"whatsapp_id": "15551234567", "code": "123456"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_tokens_rotates(client, db_session):
    user = User(whatsapp_id="15550001111")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    refresh_token = _create_refresh_token(user.id, db_session)
    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
