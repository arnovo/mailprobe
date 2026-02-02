"""Celery app configuration."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mailprobe",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=["app.tasks.verify", "app.tasks.exports", "app.tasks.webhooks", "app.tasks.retention"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)
