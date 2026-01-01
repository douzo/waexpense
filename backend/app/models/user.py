import uuid
from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_id = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    name = Column(String, nullable=True)
    default_currency = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False, nullable=False)
