from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PremiumToggleBody(BaseModel):
    is_premium: bool


def _require_admin(x_admin_token: Optional[str]):
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access not configured",
        )
    if x_admin_token != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )


@router.patch("/users/{whatsapp_id}/premium")
async def set_premium(
    whatsapp_id: str,
    body: PremiumToggleBody,
    db: Session = Depends(get_db),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    _require_admin(x_admin_token)

    user: Optional[User] = (
        db.query(User).filter(User.whatsapp_id == whatsapp_id).first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_premium = body.is_premium
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "whatsapp_id": user.whatsapp_id,
        "is_premium": user.is_premium,
    }
