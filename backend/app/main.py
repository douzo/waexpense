import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.expenses import router as expenses_router
from app.api.routes.profile import router as profile_router
from app.api.webhook import router as webhook_router
from app.core.config import settings
from app.db import engine
from app.models import Base
from pathlib import Path

logging.basicConfig(level=logging.INFO)

def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    config_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    alembic_cfg = Config(str(config_path))
    alembic_cfg.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "alembic")
    )
    command.upgrade(alembic_cfg, "head")


if settings.auto_migrate:
    _run_migrations()
else:
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

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(expenses_router)
app.include_router(profile_router)
app.include_router(webhook_router)
