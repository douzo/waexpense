import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.expenses import router as expenses_router
from app.api.webhook import router as webhook_router
from app.core.config import settings
from app.db import engine
from app.models import Base

logging.basicConfig(level=logging.INFO)

# Create tables for demo purposes (use migrations in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Permissive CORS for local dev; tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expenses_router)
app.include_router(webhook_router)
