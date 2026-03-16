"""Celery tasks for notifications — alert sellers about hot leads."""

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


@celery.task(name="app.tasks.notifications.alert_hot_lead")
def alert_hot_lead(lead_id: str, company_id: str, score: int, lead_name: str | None = None):
    """Send WhatsApp notification to assigned seller about a hot lead."""

    async def _alert():
        from sqlalchemy import select
        from app.database import async_session
        from app.models.lead import Lead
        from app.models.user import User
        from app.models.company import Company

        async with async_session() as db:
            # Get lead
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                return

            # Get company
            company_result = await db.execute(select(Company).where(Company.id == company_id))
            company = company_result.scalar_one_or_none()
            if not company or not company.whatsapp_token:
                logger.info("Skipping alert — no WhatsApp token for company %s", company_id)
                return

            # Find seller to notify (assigned or first admin)
            seller = None
            if lead.assigned_to:
                seller_result = await db.execute(select(User).where(User.id == lead.assigned_to))
                seller = seller_result.scalar_one_or_none()

            if not seller:
                # Find first admin/manager with WhatsApp
                seller_result = await db.execute(
                    select(User).where(
                        User.company_id == company.id,
                        User.role.in_(["admin", "manager"]),
                        User.whatsapp_phone.is_not(None),
                        User.is_active.is_(True),
                    ).limit(1)
                )
                seller = seller_result.scalar_one_or_none()

            if not seller or not seller.whatsapp_phone:
                logger.info("No seller with WhatsApp to notify for lead %s", lead_id)
                return

            # Send notification
            message = (
                f"🔥 *Lead caliente!*\n\n"
                f"*{lead.name or 'Sin nombre'}* (score: {score})\n"
                f"Canal: {lead.source_channel or 'desconocido'}\n"
                f"Telefono: {lead.whatsapp_phone or 'N/A'}\n\n"
                f"El lead tiene alta intencion de compra. Revisalo en el dashboard."
            )

            try:
                from app.services.whatsapp_client import send_text_message
                await send_text_message(
                    company.phone_number_id or "",
                    seller.whatsapp_phone,
                    message,
                )
                logger.info("Hot lead alert sent to %s for lead %s", seller.name, lead_id)
            except Exception:
                logger.warning("Failed to send hot lead alert for %s", lead_id)

    return _run_async(_alert())
