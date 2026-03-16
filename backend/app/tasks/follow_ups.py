"""Celery tasks for follow-up execution."""

import asyncio
import logging

from app.celery_app import celery

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async code in sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery.task(name="app.tasks.follow_ups.execute_pending_followups")
def execute_pending_followups():
    """Execute all pending follow-ups that are due. Runs every 5 minutes."""

    async def _execute():
        from app.database import async_session
        from app.services.follow_up_engine import get_pending_followups, execute_followup

        pending = await get_pending_followups()
        if not pending:
            return 0

        executed = 0
        async with async_session() as db:
            for followup in pending:
                try:
                    success = await execute_followup(followup, db)
                    if success:
                        executed += 1
                except Exception:
                    logger.exception("Error executing follow-up %s", followup.get("id"))
            await db.commit()

        logger.info("Executed %d/%d follow-ups", executed, len(pending))
        return executed

    return _run_async(_execute())


@celery.task(name="app.tasks.follow_ups.check_stale_leads")
def check_stale_leads():
    """Check for leads that haven't responded in 48h and schedule reactivation. Runs daily at 9am."""

    async def _check():
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import select
        from app.database import async_session
        from app.models.lead import Lead
        from app.models.conversation import Conversation
        from app.services.follow_up_engine import schedule_followup

        threshold = datetime.now(timezone.utc) - timedelta(hours=48)
        scheduled = 0

        async with async_session() as db:
            result = await db.execute(
                select(Lead)
                .where(
                    Lead.last_message_at < threshold,
                    Lead.stage.in_(["new", "interested"]),
                    Lead.is_active.is_(True),
                )
                .limit(50)
            )
            stale_leads = result.scalars().all()

            for lead in stale_leads:
                # Find their active conversation
                conv_result = await db.execute(
                    select(Conversation)
                    .where(
                        Conversation.lead_id == lead.id,
                        Conversation.status == "active",
                    )
                    .limit(1)
                )
                conv = conv_result.scalar_one_or_none()
                if conv:
                    await schedule_followup(db, lead.id, lead.company_id, conv.id, "reactivacion")
                    scheduled += 1

            await db.commit()

        logger.info("Scheduled %d reactivation follow-ups for stale leads", scheduled)
        return scheduled

    return _run_async(_check())
