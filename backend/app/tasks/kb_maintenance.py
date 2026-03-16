"""Celery tasks for KB maintenance — expiration, stale detection, cleanup."""

import asyncio
import logging

from app.celery_app import celery

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery.task(name="app.tasks.kb_maintenance.expire_kb_items")
def expire_kb_items():
    """Deactivate KB items that passed their expiration date. Runs every hour."""

    async def _expire():
        from app.database import async_session
        from app.services.kb_manager import deactivate_expired_items

        async with async_session() as db:
            count = await deactivate_expired_items(db)
            await db.commit()

        if count:
            logger.info("Expired %d KB items", count)
        return count

    return _run_async(_expire())


@celery.task(name="app.tasks.kb_maintenance.flag_stale_kb_items")
def flag_stale_kb_items():
    """Flag KB items that haven't been used in 90 days. Runs daily at 8am."""

    async def _flag():
        from sqlalchemy import select
        from app.database import async_session
        from app.models.company import Company
        from app.services.kb_manager import flag_stale_items

        async with async_session() as db:
            result = await db.execute(
                select(Company.id).where(Company.is_active.is_(True))
            )
            company_ids = result.scalars().all()

            total_flagged = 0
            for cid in company_ids:
                flagged = await flag_stale_items(db, cid)
                total_flagged += len(flagged)

            await db.commit()

        logger.info("Flagged %d stale KB items across %d companies", total_flagged, len(company_ids))
        return total_flagged

    return _run_async(_flag())
