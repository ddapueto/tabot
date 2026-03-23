"""Company settings and AI configuration API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_company_id
from app.database import get_db
from app.models.company import Company

router = APIRouter()


class CompanySettingsUpdate(BaseModel):
    name: str | None = None
    business_type: str | None = None
    description: str | None = None
    whatsapp_phone: str | None = None
    timezone: str | None = None
    currency: str | None = None
    business_hours: dict | None = None


class AIConfigUpdate(BaseModel):
    ai_personality: str | None = None
    ai_language: str | None = None
    ai_sales_goal: str | None = None
    ai_custom_rules: str | None = None
    ai_model: str | None = None
    scoring_rules: dict | None = None


@router.get("/")
async def get_settings(
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Get company settings."""
    result = await db.execute(
        select(Company).where(Company.id == company_id),
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    return {
        "id": str(company.id),
        "name": company.name,
        "slug": company.slug,
        "business_type": company.business_type,
        "description": company.description,
        "whatsapp_phone": company.whatsapp_phone,
        "timezone": company.timezone,
        "currency": company.currency,
        "business_hours": company.business_hours,
        "ai_personality": company.ai_personality,
        "ai_language": company.ai_language,
        "ai_sales_goal": company.ai_sales_goal,
        "ai_custom_rules": company.ai_custom_rules,
        "ai_model": company.ai_model,
        "scoring_rules": company.scoring_rules,
        "is_active": company.is_active,
        "channels": {
            "whatsapp": bool(company.phone_number_id),
            "instagram": bool(company.ig_account_id),
        },
    }


@router.patch("/")
async def update_settings(
    data: CompanySettingsUpdate,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Update company settings."""
    result = await db.execute(
        select(Company).where(Company.id == company_id),
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    await db.flush()
    return {"status": "updated"}


@router.patch("/ai")
async def update_ai_config(
    data: AIConfigUpdate,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Update AI agent configuration."""
    result = await db.execute(
        select(Company).where(Company.id == company_id),
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    await db.flush()
    return {"status": "ai_config_updated"}
