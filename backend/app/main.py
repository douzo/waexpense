import logging
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.expenses import router as expenses_router
from app.api.routes.webhook import router as webhook_router
from app.core.config import settings
from app.db.session import engine
from app.models import base, expense, receipt, user

logging.basicConfig(level=logging.INFO)

# Create tables for demo purposes (in production use migrations)
base.Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(health_router)
app.include_router(expenses_router)
app.include_router(webhook_router)
