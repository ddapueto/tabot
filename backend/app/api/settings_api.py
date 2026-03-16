"""Company settings and AI configuration API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company
from app.models.knowledge import KnowledgeItem

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


@router.get("/{company_id}")
async def get_settings(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get company settings."""
    result = await db.execute(select(Company).where(Company.id == company_id))
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


@router.patch("/{company_id}")
async def update_settings(
    company_id: uuid.UUID,
    data: CompanySettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update company settings."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    await db.flush()
    return {"status": "updated"}


@router.patch("/{company_id}/ai")
async def update_ai_config(
    company_id: uuid.UUID,
    data: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update AI agent configuration."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    await db.flush()
    return {"status": "ai_config_updated"}


# Knowledge Base CRUD

class KBItemCreate(BaseModel):
    source: str = "manual"
    title: str
    content: str
    media_urls: list[str] | None = None


@router.get("/{company_id}/knowledge-base")
async def list_kb_items(
    company_id: uuid.UUID,
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List knowledge base items."""
    query = select(KnowledgeItem).where(KnowledgeItem.company_id == company_id)
    if source:
        query = query.where(KnowledgeItem.source == source)
    query = query.order_by(KnowledgeItem.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        {
            "id": str(i.id),
            "source": i.source,
            "title": i.title,
            "content": i.content[:200],
            "media_urls": i.media_urls,
            "is_active": i.is_active,
            "auto_generated": i.auto_generated,
            "created_at": i.created_at.isoformat(),
        }
        for i in items
    ]


@router.post("/{company_id}/knowledge-base", status_code=201)
async def create_kb_item(
    company_id: uuid.UUID,
    data: KBItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a knowledge base item."""
    item = KnowledgeItem(
        company_id=company_id,
        source=data.source,
        title=data.title,
        content=data.content,
        media_urls=data.media_urls or [],
        is_active=True,
        auto_generated=False,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return {"id": str(item.id), "status": "created"}


@router.delete("/{company_id}/knowledge-base/{item_id}")
async def delete_kb_item(
    company_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a KB item."""
    result = await db.execute(
        select(KnowledgeItem).where(
            KnowledgeItem.id == item_id,
            KnowledgeItem.company_id == company_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    item.is_active = False
    await db.flush()
    return {"status": "deactivated"}


# ── Promos/Ofertas ──

class PromoCreate(BaseModel):
    title: str
    content: str
    expires_at: str  # ISO datetime
    channels: list[str] = ["whatsapp", "instagram", "web"]
    media_urls: list[str] | None = None


@router.post("/{company_id}/promos", status_code=201)
async def create_promo(
    company_id: uuid.UUID,
    data: PromoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a promotional KB item with expiration."""
    from datetime import datetime
    from app.services.kb_manager import create_promo as _create_promo

    expires = datetime.fromisoformat(data.expires_at)
    item = await _create_promo(
        db=db,
        company_id=company_id,
        title=data.title,
        content=data.content,
        expires_at=expires,
        channels=data.channels,
        media_urls=data.media_urls,
    )
    return {"id": str(item.id), "expires_at": data.expires_at, "status": "created"}


# ── KB Health ──

@router.get("/{company_id}/kb-health")
async def kb_health(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get knowledge base health metrics."""
    from app.services.kb_manager import get_kb_health
    return await get_kb_health(db, company_id)


# ── Sync Catalog to KB ──

@router.post("/{company_id}/sync-catalog")
async def sync_catalog(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Sync all products to knowledge base."""
    from app.services.kb_manager import sync_all_products_to_kb
    synced = await sync_all_products_to_kb(db, company_id)
    return {"synced": synced, "status": "catalog_synced"}
