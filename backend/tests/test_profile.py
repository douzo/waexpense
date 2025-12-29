from app.api.routes.auth import _create_jwt
from app.models import User


def test_profile_get_and_update(client, db_session):
    user = User(whatsapp_id="19998887777", name="Old Name")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = _create_jwt(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/profile", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Old Name"

    res = client.patch("/api/profile", json={"name": "New Name"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"
