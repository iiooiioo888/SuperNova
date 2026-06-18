"""Prometheus 监控指标"""
from __future__ import annotations

import structlog
from prometheus_client import Counter, Histogram, Gauge, Info

logger = structlog.get_logger(__name__)

# ── 任务指标 ──────────────────────────────────────────────

task_counter = Counter(
    "superhub_tasks_total",
    "任务总数",
    ["platform", "task_type", "status"],
)

task_duration = Histogram(
    "superhub_task_duration_seconds",
    "任务耗时",
    ["platform", "task_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

tasks_in_queue = Gauge(
    "superhub_tasks_in_queue",
    "排队中任务数",
    ["platform"],
)

tasks_running = Gauge(
    "superhub_tasks_running",
    "运行中任务数",
    ["platform"],
)

# ── 采集指标 ──────────────────────────────────────────────

items_collected = Counter(
    "superhub_items_collected_total",
    "采集数据条数",
    ["platform", "data_type"],
)

api_requests = Counter(
    "superhub_api_requests_total",
    "外部 API 请求总数",
    ["platform", "endpoint", "status_code"],
)

api_latency = Histogram(
    "superhub_api_latency_seconds",
    "外部 API 请求延迟",
    ["platform", "endpoint"],
    buckets=[0.1, 0.3, 0.5, 1, 2, 5, 10],
)

# ── 熔断器指标 ────────────────────────────────────────────

circuit_state = Gauge(
    "superhub_circuit_breaker_state",
    "熔断器状态 (0=closed, 1=open, 2=half-open)",
    ["platform"],
)

circuit_failures = Counter(
    "superhub_circuit_breaker_failures_total",
    "熔断器失败计数",
    ["platform"],
)

# ── 账号池指标 ────────────────────────────────────────────

account_pool_active = Gauge(
    "superhub_account_pool_active",
    "可用账号数",
    ["platform"],
)

account_pool_banned = Gauge(
    "superhub_account_pool_banned",
    "被封禁账号数",
    ["platform"],
)

# ── 系统指标 ──────────────────────────────────────────────

app_info = Info(
    "superhub_app",
    "应用信息",
)


def record_task_completion(
    platform: str,
    task_type: str,
    status: str,
    duration_seconds: float | None = None,
) -> None:
    """记录任务完成指标"""
    task_counter.labels(platform=platform, task_type=task_type, status=status).inc()
    if duration_seconds is not None:
        task_duration.labels(platform=platform, task_type=task_type).observe(duration_seconds)


def record_api_call(
    platform: str,
    endpoint: str,
    status_code: int,
    latency_seconds: float | None = None,
) -> None:
    """记录 API 调用指标"""
    api_requests.labels(
        platform=platform, endpoint=endpoint, status_code=str(status_code)
    ).inc()
    if latency_seconds is not None:
        api_latency.labels(platform=platform, endpoint=endpoint).observe(latency_seconds)


def record_items_collected(platform: str, data_type: str, count: int) -> None:
    """记录采集数据量"""
    items_collected.labels(platform=platform, data_type=data_type).inc(count)
