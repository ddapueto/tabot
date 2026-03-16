"""Knowledge Base Manager — smart lifecycle, auto-sync, expiration, channel targeting."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, case, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeItem
from app.models.product import Product

logger = logging.getLogger(__name__)

# Max active items per company (prevents context bloat)
MAX_ACTIVE_ITEMS = 50
# Items older than this without usage get flagged
STALE_THRESHOLD_DAYS = 90


# ─────────────────────────────────────────────
# 1. AUTO-SYNC: Catalog → KB
# ─────────────────────────────────────────────

async def sync_product_to_kb(db: AsyncSession, product: Product, company_id: uuid.UUID) -> KnowledgeItem:
    """When a product is created/updated, auto-create/update its KB entry.
    NOTE: KB entry has product INFO (description, features) but NOT prices.
    Prices always come from catalog in real-time."""

    # Check if KB entry already exists for this product
    result = await db.execute(
        select(KnowledgeItem).where(
            KnowledgeItem.company_id == company_id,
            KnowledgeItem.source == "catalog",
            KnowledgeItem.product_id == product.id,
        )
    )
    existing = result.scalar_one_or_none()

    # Build content WITHOUT prices (prices come from catalog tool in real-time)
    content_parts = [f"Producto: {product.name}"]
    if product.category:
        content_parts.append(f"Categoria: {product.category}")
    if product.description:
        content_parts.append(f"Descripcion: {product.description}")
    if product.specs:
        specs_str = ", ".join(f"{k}: {v}" for k, v in product.specs.items())
        content_parts.append(f"Especificaciones: {specs_str}")
    if product.features:
        content_parts.append(f"Incluye: {', '.join(product.features)}")
    if product.price_notes:
        content_parts.append(f"Nota de precio: {product.price_notes}")

    content = "\n".join(content_parts)

    if existing:
        existing.content = content
        existing.title = f"Producto: {product.name}"
        existing.is_active = product.is_active
        existing.updated_at = datetime.now(timezone.utc)
        await db.flush()
        logger.info("KB synced (update) for product %s", product.name)
        return existing

    item = KnowledgeItem(
        company_id=company_id,
        source="catalog",
        product_id=product.id,
        title=f"Producto: {product.name}",
        content=content,
        item_type="permanent",
        priority=3,
        channels=["whatsapp", "instagram", "web"],
        is_active=product.is_active,
        auto_generated=True,
    )
    db.add(item)
    await db.flush()
    logger.info("KB synced (new) for product %s", product.name)
    return item


async def sync_all_products_to_kb(db: AsyncSession, company_id: uuid.UUID) -> int:
    """Sync entire product catalog to KB. Used during onboarding."""
    result = await db.execute(
        select(Product).where(Product.company_id == company_id)
    )
    products = result.scalars().all()
    synced = 0
    for product in products:
        await sync_product_to_kb(db, product, company_id)
        synced += 1
    logger.info("Synced %d products to KB for company %s", synced, company_id)
    return synced


# ─────────────────────────────────────────────
# 2. PROMOS & OFERTAS (temporal, con expiración)
# ─────────────────────────────────────────────

async def create_promo(
    db: AsyncSession,
    company_id: uuid.UUID,
    title: str,
    content: str,
    expires_at: datetime,
    channels: list[str] | None = None,
    media_urls: list[str] | None = None,
    source_url: str | None = None,
) -> KnowledgeItem:
    """Create a promotional KB item with expiration date."""
    item = KnowledgeItem(
        company_id=company_id,
        source="promo",
        source_url=source_url,
        title=title,
        content=content,
        media_urls=media_urls or [],
        item_type="temporal",
        expires_at=expires_at,
        priority=1,  # Promos get highest priority
        channels=channels or ["whatsapp", "instagram", "web"],
        is_active=True,
        auto_generated=False,
    )
    db.add(item)
    await db.flush()
    logger.info("Promo created: %s (expires %s)", title, expires_at)
    return item


# ─────────────────────────────────────────────
# 3. EXPIRATION & CLEANUP
# ─────────────────────────────────────────────

async def deactivate_expired_items(db: AsyncSession) -> int:
    """Deactivate KB items that have passed their expiration date.
    Should run via Celery beat (every hour)."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        update(KnowledgeItem)
        .where(
            KnowledgeItem.expires_at.is_not(None),
            KnowledgeItem.expires_at < now,
            KnowledgeItem.is_active.is_(True),
        )
        .values(is_active=False, review_reason="Expirado automaticamente")
        .returning(KnowledgeItem.id)
    )
    expired_ids = result.scalars().all()
    if expired_ids:
        logger.info("Deactivated %d expired KB items", len(expired_ids))
    return len(expired_ids)


async def flag_stale_items(db: AsyncSession, company_id: uuid.UUID) -> list[dict]:
    """Flag items that haven't been used in STALE_THRESHOLD_DAYS.
    Returns list of stale items for admin review."""
    threshold = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS)

    result = await db.execute(
        select(KnowledgeItem).where(
            KnowledgeItem.company_id == company_id,
            KnowledgeItem.is_active.is_(True),
            KnowledgeItem.item_type == "permanent",
            # Never used, or last used before threshold
            (KnowledgeItem.last_used_at.is_(None)) | (KnowledgeItem.last_used_at < threshold),
            KnowledgeItem.created_at < threshold,
        )
    )
    stale = result.scalars().all()

    flagged = []
    for item in stale:
        item.needs_review = True
        item.review_reason = f"Sin uso en {STALE_THRESHOLD_DAYS} dias"
        flagged.append({
            "id": str(item.id),
            "title": item.title,
            "source": item.source,
            "times_used": item.times_used,
            "created_at": item.created_at.isoformat(),
        })

    if flagged:
        await db.flush()
        logger.info("Flagged %d stale KB items for company %s", len(flagged), company_id)
    return flagged


# ─────────────────────────────────────────────
# 4. SMART RETRIEVAL (for AI agent)
# ─────────────────────────────────────────────

async def get_relevant_kb(
    db: AsyncSession,
    company_id: uuid.UUID,
    channel: str = "whatsapp",
    max_items: int = 10,
) -> list[KnowledgeItem]:
    """Get active, non-expired KB items relevant to the channel.
    Sorted by priority (1=highest) then recency.
    Used by the AI agent to build context."""
    now = datetime.now(timezone.utc)

    query = (
        select(KnowledgeItem)
        .where(
            KnowledgeItem.company_id == company_id,
            KnowledgeItem.is_active.is_(True),
            # Not expired
            (KnowledgeItem.expires_at.is_(None)) | (KnowledgeItem.expires_at > now),
        )
        .order_by(KnowledgeItem.priority.asc(), KnowledgeItem.updated_at.desc())
        .limit(max_items)
    )

    result = await db.execute(query)
    items = result.scalars().all()

    # Filter by channel (JSONB contains check)
    filtered = []
    for item in items:
        item_channels = item.channels or ["whatsapp", "instagram", "web"]
        if channel in item_channels or "all" in item_channels:
            filtered.append(item)

    return filtered[:max_items]


async def record_kb_usage(db: AsyncSession, item_ids: list[uuid.UUID]):
    """Record that KB items were used in a response. For usage tracking."""
    if not item_ids:
        return
    now = datetime.now(timezone.utc)
    for item_id in item_ids:
        await db.execute(
            update(KnowledgeItem)
            .where(KnowledgeItem.id == item_id)
            .values(
                times_used=KnowledgeItem.times_used + 1,
                last_used_at=now,
            )
        )


# ─────────────────────────────────────────────
# 5. KB HEALTH CHECK (for dashboard)
# ─────────────────────────────────────────────

async def get_kb_health(db: AsyncSession, company_id: uuid.UUID) -> dict:
    """Get KB health metrics for the dashboard."""
    now = datetime.now(timezone.utc)

    # Single query with conditional counts using case()
    result = await db.execute(
        select(
            func.count(KnowledgeItem.id).label("total"),
            func.count(case((KnowledgeItem.is_active.is_(True), 1))).label("active"),
            func.count(case((and_(KnowledgeItem.expires_at.is_not(None), KnowledgeItem.expires_at < now), 1))).label("expired"),
            func.count(case((KnowledgeItem.needs_review.is_(True), 1))).label("needs_review"),
            func.count(case((and_(KnowledgeItem.is_active.is_(True), KnowledgeItem.times_used == 0), 1))).label("never_used"),
            func.count(case((and_(
                KnowledgeItem.is_active.is_(True),
                KnowledgeItem.expires_at.is_not(None),
                KnowledgeItem.expires_at.between(now, now + timedelta(days=7)),
            ), 1))).label("expiring_soon"),
        )
        .where(KnowledgeItem.company_id == company_id)
    )
    row = result.one()

    # By source (separate query)
    source_result = await db.execute(
        select(KnowledgeItem.source, func.count(KnowledgeItem.id))
        .where(KnowledgeItem.company_id == company_id, KnowledgeItem.is_active.is_(True))
        .group_by(KnowledgeItem.source)
    )

    return {
        "total": row.total,
        "active": row.active,
        "max_allowed": MAX_ACTIVE_ITEMS,
        "expired": row.expired,
        "needs_review": row.needs_review,
        "never_used": row.never_used,
        "expiring_soon_7d": row.expiring_soon,
        "by_source": dict(source_result.all()),
        "health_score": _calc_health_score(row.active, row.needs_review, row.never_used),
    }


def _calc_health_score(active: int, needs_review: int, never_used: int) -> str:
    """Simple health indicator."""
    if active == 0:
        return "empty"
    review_ratio = needs_review / active if active else 0
    unused_ratio = never_used / active if active else 0
    if review_ratio > 0.3 or unused_ratio > 0.5:
        return "needs_attention"
    if review_ratio > 0.1 or unused_ratio > 0.3:
        return "fair"
    return "healthy"


# ─────────────────────────────────────────────
# 6. COMMERCIAL CHANNEL TEMPLATES
# ─────────────────────────────────────────────

CHANNEL_TEMPLATES = {
    "whatsapp": {
        "promo": "🔥 *{title}*\n\n{content}\n\n📲 Responde a este mensaje para mas info!",
        "product_highlight": "✨ *{name}*\n{short_desc}\n\n💰 Consulta precio\n📍 {location}",
        "new_arrival": "🆕 *Novedad!* {name}\n\n{description}\n\n¿Te interesa? Escribinos!",
    },
    "instagram": {
        "promo": "🔥 {title}\n\n{content}\n\n👉 Link en bio o escribinos por DM!\n\n{hashtags}",
        "product_highlight": "✨ {name}\n\n{short_desc}\n\n{features}\n\n💰 Consultas por DM\n\n{hashtags}",
        "new_arrival": "🆕 Nueva llegada: {name}\n\n{description}\n\n¿Que te parece? 👇\n\n{hashtags}",
    },
    "web": {
        "promo": "<h3>{title}</h3><p>{content}</p><a href='{cta_url}'>Ver oferta</a>",
        "product_highlight": "<div class='product-card'><h4>{name}</h4><p>{short_desc}</p></div>",
        "new_arrival": "<div class='new-badge'>Nuevo</div><h4>{name}</h4><p>{description}</p>",
    },
}


def format_for_channel(
    template_type: str,
    channel: str,
    data: dict,
) -> str:
    """Format content for a specific commercial channel."""
    templates = CHANNEL_TEMPLATES.get(channel, CHANNEL_TEMPLATES["whatsapp"])
    template = templates.get(template_type, "{content}")

    # Add default hashtags for Instagram
    if channel == "instagram" and "hashtags" not in data:
        data["hashtags"] = "#oferta #promo"

    try:
        return template.format(**data)
    except KeyError:
        return data.get("content", str(data))
