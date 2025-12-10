import uuid
from sqlalchemy import Column, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount = Column(Numeric(scale=2), nullable=False)
    currency = Column(String, nullable=False)
    category = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    expense_date = Column(Date, nullable=False)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"), nullable=True)

    user = relationship("User", backref="expenses")
    receipt = relationship("Receipt", back_populates="expense")
