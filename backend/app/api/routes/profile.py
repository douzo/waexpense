from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/api")


class ProfileResponse(BaseModel):
    id: str
    whatsapp_id: str
    name: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    return ProfileResponse(
        id=str(current_user.id),
        whatsapp_id=current_user.whatsapp_id,
        name=current_user.name,
    )


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    name = body.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty",
        )

    current_user.name = name
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return ProfileResponse(
        id=str(current_user.id),
        whatsapp_id=current_user.whatsapp_id,
        name=current_user.name,
    )
