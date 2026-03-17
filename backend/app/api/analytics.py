from app.api.deps import get_current_company_id
"""Analytics API — conversion metrics, response times, product popularity, AI costs."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, case, extract, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead, LeadStageHistory
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter()


@router.get("/conversion-funnel")
async def conversion_funnel(
    company_id: uuid.UUID = Depends(get_current_company_id),
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Conversion funnel: how many leads at each stage."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Lead.stage, func.count(Lead.id))
        .where(Lead.company_id == company_id, Lead.created_at >= since)
        .group_by(Lead.stage)
    )
    stages = dict(result.all())

    ordered = ["new", "interested", "qualified", "negotiating", "visiting", "closing", "won", "lost"]
    funnel = [{"stage": s, "count": stages.get(s, 0)} for s in ordered]
    total = sum(v["count"] for v in funnel)

    return {
        "period_days": days,
        "total_leads": total,
        "funnel": funnel,
        "conversion_rate": round(stages.get("won", 0) / total * 100, 1) if total else 0,
    }


@router.get("/response-times")
async def response_times(
    company_id: uuid.UUID = Depends(get_current_company_id),
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Average response time (time between inbound and next outbound)."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Get leads with both message timestamps
    result = await db.execute(
        select(
            func.avg(
                extract("epoch", Lead.last_response_at) - extract("epoch", Lead.last_message_at)
            ).label("avg_seconds"),
            func.min(
                extract("epoch", Lead.last_response_at) - extract("epoch", Lead.last_message_at)
            ).label("min_seconds"),
            func.max(
                extract("epoch", Lead.last_response_at) - extract("epoch", Lead.last_message_at)
            ).label("max_seconds"),
            func.count(Lead.id).label("total"),
        )
        .where(
            Lead.company_id == company_id,
            Lead.last_message_at >= since,
            Lead.last_response_at.is_not(None),
        )
    )
    row = result.one()

    return {
        "period_days": days,
        "avg_response_seconds": round(float(row.avg_seconds or 0), 1),
        "min_response_seconds": round(float(row.min_seconds or 0), 1),
        "max_response_seconds": round(float(row.max_seconds or 0), 1),
        "leads_measured": row.total,
    }


@router.get("/ai-stats")
async def ai_stats(
    company_id: uuid.UUID = Depends(get_current_company_id),
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
):
    """AI performance stats: messages handled, tokens used, cost estimate."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(Message.id).label("total_messages"),
            func.count(case((Message.sender_type == "ai", 1))).label("ai_messages"),
            func.count(case((Message.sender_type == "human", 1))).label("human_messages"),
            func.count(case((Message.direction == "inbound", 1))).label("inbound"),
            func.sum(case((Message.sender_type == "ai", Message.ai_tokens_in), else_=0)).label("total_tokens_in"),
            func.sum(case((Message.sender_type == "ai", Message.ai_tokens_out), else_=0)).label("total_tokens_out"),
        )
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.company_id == company_id, Message.created_at >= since)
    )
    row = result.one()

    total_in = int(row.total_tokens_in or 0)
    total_out = int(row.total_tokens_out or 0)

    # Estimate cost (Groq is free tier, but calculate for reference)
    # Llama 3.3 70B: ~$0.59/M input, ~$0.79/M output on Groq
    cost_estimate = (total_in * 0.59 / 1_000_000) + (total_out * 0.79 / 1_000_000)

    inbound = int(row.inbound or 0)
    ai_msgs = int(row.ai_messages or 0)

    return {
        "period_days": days,
        "total_messages": row.total_messages,
        "ai_messages": ai_msgs,
        "human_messages": int(row.human_messages or 0),
        "inbound_messages": inbound,
        "ai_handle_rate": round(ai_msgs / inbound * 100, 1) if inbound else 0,
        "total_tokens_in": total_in,
        "total_tokens_out": total_out,
        "estimated_cost_usd": round(cost_estimate, 4),
    }


@router.get("/leads-over-time")
async def leads_over_time(
    company_id: uuid.UUID = Depends(get_current_company_id),
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
):
    """New leads per day over time."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date_trunc("day", Lead.created_at).label("day"),
            func.count(Lead.id).label("count"),
        )
        .where(Lead.company_id == company_id, Lead.created_at >= since)
        .group_by(text("1"))
        .order_by(text("1"))
    )

    return {
        "period_days": days,
        "data": [
            {"date": row.day.isoformat()[:10], "count": row.count}
            for row in result.all()
        ],
    }


@router.get("/top-products")
async def top_products(
    company_id: uuid.UUID = Depends(get_current_company_id),
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Most mentioned/queried products based on AI tool usage."""
    # Count how many conversations mention each product in messages
    from app.models.product import Product

    result = await db.execute(
        select(Product.id, Product.name, Product.category, Product.price)
        .where(Product.company_id == company_id, Product.is_active.is_(True))
        .order_by(Product.display_order)
    )
    products = result.all()

    # Count message mentions per product (simple keyword match)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    product_mentions = []

    for p_id, p_name, p_cat, p_price in products:
        mention_count = await db.execute(
            select(func.count(Message.id))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.company_id == company_id,
                Message.created_at >= since,
                Message.content.ilike(f"%{p_name.split()[0]}%"),
            )
        )
        count = mention_count.scalar() or 0
        product_mentions.append({
            "id": str(p_id),
            "name": p_name,
            "category": p_cat,
            "price": float(p_price) if p_price else None,
            "mentions": count,
        })

    product_mentions.sort(key=lambda x: x["mentions"], reverse=True)
    return {"period_days": days, "products": product_mentions}


@router.get("/scoring-distribution")
async def scoring_distribution(
    company_id: uuid.UUID = Depends(get_current_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Distribution of lead scores."""
    result = await db.execute(
        select(
            func.count(case((Lead.score < 26, 1))).label("low"),
            func.count(case((Lead.score.between(26, 50), 1))).label("medium"),
            func.count(case((Lead.score.between(51, 75), 1))).label("high"),
            func.count(case((Lead.score > 75, 1))).label("urgent"),
        )
        .where(Lead.company_id == company_id)
    )
    row = result.one()

    return {
        "low_0_25": row.low,
        "medium_26_50": row.medium,
        "high_51_75": row.high,
        "urgent_76_100": row.urgent,
        "total": row.low + row.medium + row.high + row.urgent,
    }
