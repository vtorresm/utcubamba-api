from celery import Celery
from src.core.config import settings

REDIS_URL = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "utcubamba",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.tasks.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Lima",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_max_tasks_per_child=200,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
