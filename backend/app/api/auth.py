"""JWT authentication — register, login, refresh tokens."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import get_db
from app.models.user import User

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


# --- Schemas ---

class RegisterRequest(BaseModel):
    company_id: uuid.UUID
    email: str
    name: str
    password: str
    role: str = "seller"


class LoginRequest(BaseModel):
    email: str
    password: str
    company_id: uuid.UUID


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Helpers ---

def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_tokens(user_id: str, company_id: str, role: str) -> TokenResponse:
    access_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    refresh_expires = timedelta(days=settings.jwt_refresh_token_expire_days)

    access_token = create_token(
        {"sub": user_id, "company_id": company_id, "role": role, "type": "access"},
        access_expires,
    )
    refresh_token = create_token(
        {"sub": user_id, "company_id": company_id, "type": "refresh"},
        refresh_expires,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_expires.total_seconds()),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that extracts and validates JWT, returns User."""
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token invalido")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalido")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    return user


# --- Endpoints ---

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email already exists for this company
    result = await db.execute(
        select(User).where(User.company_id == data.company_id, User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password debe tener al menos 8 caracteres")

    user = User(
        company_id=data.company_id,
        email=data.email,
        name=data.name,
        role=data.role,
        password_hash=pwd_context.hash(data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return create_tokens(str(user.id), str(user.company_id), user.role)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.company_id == data.company_id, User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    return create_tokens(str(user.id), str(user.company_id), user.role)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(
            data.refresh_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token invalido")

        user_id = payload.get("sub")
        company_id = payload.get("company_id")

    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token invalido o expirado")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return create_tokens(str(user.id), str(user.company_id), user.role)


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "company_id": str(user.company_id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
    }
