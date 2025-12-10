import uuid
from sqlalchemy import Column, Enum, ForeignKey, String, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ReceiptStatus(str):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    s3_key = Column(String, nullable=False)
    ocr_status = Column(String, default=ReceiptStatus.PENDING, nullable=False)
    total_amount = Column(Numeric(scale=2), nullable=True)
    merchant = Column(String, nullable=True)
    ocr_raw = Column(JSON, nullable=True)

    user = relationship("User", backref="receipts")
    expense = relationship("Expense", back_populates="receipt", uselist=False)
