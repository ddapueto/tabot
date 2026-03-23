"""Knowledge Base API — CRUD, health, promos, and catalog sync."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_company_id
from app.database import get_db
from app.models.knowledge import KnowledgeItem
from app.services.kb_manager import create_promo as _create_promo
from app.services.kb_manager import get_kb_health, sync_all_products_to_kb

router = APIRouter()


class KBItemCreate(BaseModel):
    source: str = "manual"
    title: str
    content: str
    media_urls: list[str] | None = None


class PromoCreate(BaseModel):
    title: str
    content: str
    expires_at: str  # ISO datetime
    channels: list[str] = ["whatsapp", "instagram", "web"]
    media_urls: list[str] | None = None


@router.get("/")
async def list_kb_items(
    company_id: uuid.UUID = Depends(get_current_company_id),
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List knowledge base items."""
    query = select(KnowledgeItem).where(
        KnowledgeItem.company_id == company_id,
    )
    if source:
        query = query.where(KnowledgeItem.source == source)
    query = query.order_by(KnowledgeItem.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        {
            "id": str(item.id),
            "source": item.source,
            "title": item.title,
            "content": item.content[:200],
            "media_urls": item.media_urls,
            "is_active": item.is_active,
            "auto_generated": item.auto_generated,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]


@router.post("/", status_code=201)
async def create_kb_item(
    data: KBItemCreate,
    company_id: uuid.UUID = Depends(get_current_company_id),
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


@router.delete("/{item_id}")
async def delete_kb_item(
    item_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company_id),
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


@router.post("/promos", status_code=201)
async def create_promo(
    data: PromoCreate,
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a promotional KB item with expiration."""
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
    return {
        "id": str(item.id),
        "expires_at": data.expires_at,
        "status": "created",
    }


@router.get("/health")
async def kb_health(
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base health metrics."""
    return await get_kb_health(db, company_id)


@router.post("/sync-catalog")
async def sync_catalog(
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Sync all products to knowledge base."""
    synced = await sync_all_products_to_kb(db, company_id)
    return {"synced": synced, "status": "catalog_synced"}
