"""Celery application configuration."""

from celery import Celery
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "bluescholar",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,  # Use same Redis for results
    include=["workers.tasks.ingest"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry config
    task_default_retry_delay=30,
    task_max_retries=3,
)
