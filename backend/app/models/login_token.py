import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin


def default_expiry(minutes: int = 10) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


class LoginToken(Base, TimestampMixin):
    __tablename__ = "login_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, default=default_expiry)
    used = Column(Boolean, default=False, nullable=False)


