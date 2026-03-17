"""Shared dependencies for authenticated endpoints."""

import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models.user import User


async def get_current_company_id(user: User = Depends(get_current_user)) -> uuid.UUID:
    """Extract company_id from authenticated user. Use this in all business endpoints."""
    return user.company_id


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin or manager role."""
    if user.role not in ("admin", "manager", "super_admin"):
        raise HTTPException(status_code=403, detail="Se requiere rol admin o manager")
    return user


async def get_optional_user(
    user: User | None = Depends(get_current_user),
) -> User | None:
    """Optional auth — returns None if no token. For endpoints that work with or without auth."""
    return user
