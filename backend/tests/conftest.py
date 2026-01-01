import os

import pytest
from fastapi.testclient import TestClient

# Ensure required settings exist before importing the app.
os.environ.setdefault("APP_NAME", "WA Expense")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault(
    "DATABASE_URL", "sqlite+pysqlite:////tmp/waexpense_test.db?check_same_thread=false"
)
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test-token")
os.environ.setdefault("WHATSAPP_APP_SECRET", "test-secret")
os.environ.setdefault("WHATSAPP_ACCESS_TOKEN", "test-access")
os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "1234567890")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("EXTERNAL_TEXT_PARSER_URL", "http://localhost:9999/parser")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")

from app.db import SessionLocal, engine, get_db
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def _get_test_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
