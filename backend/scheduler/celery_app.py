"""Celery 配置"""
from celery import Celery

from ..config import settings

celery_app = Celery(
    "superhub",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["backend.scheduler.tasks"],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 分钟超时
    worker_prefetch_multiplier=1,
)