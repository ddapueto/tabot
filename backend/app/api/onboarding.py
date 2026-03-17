"""Onboarding API — setup a new company without SQL."""

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.api.auth import _hash_password, create_tokens

router = APIRouter()


class OnboardingRequest(BaseModel):
    # Company
    company_name: str
    business_type: str
    description: str | None = None
    currency: str = "USD"
    timezone: str = "America/Montevideo"

    # AI config
    ai_personality: str = "Amigable y profesional"
    ai_language: str = "es-UY"
    ai_sales_goal: str = "Guiar al cliente hacia una compra o cita"

    # Admin user
    admin_name: str
    admin_email: str
    admin_password: str


class OnboardingResponse(BaseModel):
    company_id: str
    company_name: str
    access_token: str
    refresh_token: str
    message: str


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:100]


@router.post("/setup", response_model=OnboardingResponse)
async def setup_company(data: OnboardingRequest, db: AsyncSession = Depends(get_db)):
    """Create a new company with admin user in one step. No auth required."""

    # Validate
    if len(data.admin_password) < 8:
        raise HTTPException(status_code=400, detail="Password debe tener al menos 8 caracteres")
    if not data.company_name.strip():
        raise HTTPException(status_code=400, detail="Nombre de empresa requerido")
    if not data.admin_email.strip():
        raise HTTPException(status_code=400, detail="Email requerido")

    # Check slug uniqueness
    slug = _slugify(data.company_name)
    existing = await db.execute(select(Company).where(Company.slug == slug))
    if existing.scalar_one_or_none():
        slug = slug + "-" + str(hash(data.admin_email))[-4:]

    # 1. Create company
    company = Company(
        name=data.company_name.strip(),
        slug=slug,
        business_type=data.business_type,
        description=data.description,
        currency=data.currency,
        timezone=data.timezone,
        ai_personality=data.ai_personality,
        ai_language=data.ai_language,
        ai_sales_goal=data.ai_sales_goal,
        ai_model="llama-3.3-70b-versatile",
        is_active=True,
    )
    db.add(company)
    await db.flush()

    # 2. Create admin user
    user = User(
        company_id=company.id,
        email=data.admin_email.strip(),
        name=data.admin_name.strip(),
        role="admin",
        password_hash=_hash_password(data.admin_password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # 3. Create default KB items
    from app.models.knowledge import KnowledgeItem
    default_kb = [
        ("faq", "Horario de atencion", f"Nuestro horario de atencion es de lunes a viernes de 9 a 18hs."),
        ("faq", "Formas de pago", "Aceptamos efectivo, tarjeta de credito/debito, y transferencia bancaria."),
        ("faq", "Contacto", f"Podes contactarnos por WhatsApp o Instagram. Responderemos lo antes posible."),
    ]
    for source, title, content in default_kb:
        item = KnowledgeItem(
            company_id=company.id,
            source=source,
            title=title,
            content=content,
            item_type="permanent",
            priority=3,
            channels=["whatsapp", "instagram", "web"],
            is_active=True,
            auto_generated=True,
            needs_review=True,
            review_reason="Generado automaticamente — revisar y personalizar",
        )
        db.add(item)

    await db.flush()

    # 4. Generate tokens
    tokens = create_tokens(str(user.id), str(company.id), user.role)

    return OnboardingResponse(
        company_id=str(company.id),
        company_name=company.name,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        message=f"Empresa '{company.name}' creada. Configura tu catalogo y conocimiento en Settings.",
    )
