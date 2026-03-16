"""Celery configuration with Redis broker and beat schedule."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "tabot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.follow_ups",
        "app.tasks.notifications",
    ],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Montevideo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "execute-pending-followups": {
            "task": "app.tasks.follow_ups.execute_pending_followups",
            "schedule": 300.0,  # every 5 minutes
        },
        "check-stale-leads": {
            "task": "app.tasks.follow_ups.check_stale_leads",
            "schedule": crontab(hour="9", minute="0"),  # daily at 9am
        },
    },
)
