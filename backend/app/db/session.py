from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


echo = settings.debug
engine = create_engine(settings.database_url, echo=echo, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
