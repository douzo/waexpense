import hashlib
import logging
import random
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import LoginToken, RefreshToken, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class RequestCodeBody(BaseModel):
    whatsapp_id: str


class VerifyCodeBody(BaseModel):
    whatsapp_id: str
    code: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _create_jwt(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.access_token_expiry_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256((settings.jwt_secret_key + token).encode()).hexdigest()


def _create_refresh_token(user_id: str, db: Session) -> str:
    raw = secrets.token_urlsafe(32)
    token = RefreshToken(
        user_id=user_id,
        token_hash=_hash_refresh_token(raw),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expiry_days),
    )
    db.add(token)
    db.commit()
    return raw

@router.post("/request-code")
async def request_login_code(body: RequestCodeBody, db: Session = Depends(get_db)) -> dict:
    """
    Start WhatsApp-based login:
    - User enters their WhatsApp number (wa_id).
    - We look up the existing User created via webhook.
    - Generate a one-time code and send it via WhatsApp.
    """
    user: Optional[User] = (
        db.query(User).filter(User.whatsapp_id == body.whatsapp_id).first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please send a message to the WhatsApp bot first.",
        )

    code = _generate_code()
    token = LoginToken(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(
            minutes=settings.login_code_expiry_minutes
        ),
    )
    db.add(token)
    db.commit()

    # Send code via SQS if configured; fallback to direct WhatsApp send.
    from app.services.queue import enqueue_outbound_text
    from app.services.whatsapp import whatsapp_service

    message = f"Your login code for WA Expense Tracker is: {code}"
    if not enqueue_outbound_text(user.whatsapp_id, message):
        await whatsapp_service.send_text_message(user.whatsapp_id, message)

    logger.info("Login code generated for user %s", user.id)
    return {"status": "ok"}


@router.post("/verify-code", response_model=TokenResponse)
async def verify_login_code(body: VerifyCodeBody, db: Session = Depends(get_db)):
    """
    Verify the one-time code and return a JWT for the web dashboard.
    """
    user: Optional[User] = (
        db.query(User).filter(User.whatsapp_id == body.whatsapp_id).first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    now = datetime.now(timezone.utc)
    token: Optional[LoginToken] = (
        db.query(LoginToken)
        .filter(
            LoginToken.user_id == user.id,
            LoginToken.code == body.code,
            LoginToken.used.is_(False),
            LoginToken.expires_at > now,
        )
        .order_by(LoginToken.created_at.desc())
        .first()
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code.",
        )

    token.used = True
    db.commit()

    access_token = _create_jwt(str(user.id))
    refresh_token = _create_refresh_token(user.id, db)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expiry_minutes * 60,
    )


class RefreshTokenBody(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(body: RefreshTokenBody, db: Session = Depends(get_db)):
    token_hash = _hash_refresh_token(body.refresh_token)
    now = datetime.now(timezone.utc)
    stored: Optional[RefreshToken] = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > now,
        )
        .first()
    )

    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    stored.revoked = True
    db.commit()

    access_token = _create_jwt(str(stored.user_id))
    refresh_token = _create_refresh_token(stored.user_id, db)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expiry_minutes * 60,
    )


@router.post("/logout")
async def logout(body: RefreshTokenBody, db: Session = Depends(get_db)):
    token_hash = _hash_refresh_token(body.refresh_token)
    stored: Optional[RefreshToken] = (
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    )
    if stored and not stored.revoked:
        stored.revoked = True
        db.commit()
    return {"status": "ok"}
