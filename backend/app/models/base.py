from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base


Base = declarative_base()


def utcnow():
    return datetime.utcnow()


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
