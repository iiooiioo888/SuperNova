"""PostgreSQL 数据模型：采集任务与任务历史"""
from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Text,
    Integer,
    Float,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.pg.base import Base


class TaskStatus(str, PyEnum):
    """任务状态枚举"""
    PENDING = "pending"          # 排队等待
    QUEUED = "queued"            # 已入队（Celery）
    RUNNING = "running"          # 执行中
    SUCCESS = "success"          # 成功
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
    RETRYING = "retrying"        # 重试中
    TIMEOUT = "timeout"          # 超时


class TaskPriority(str, PyEnum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskModel(Base):
    """采集任务模型
    
    记录所有采集任务的创建、执行和结果状态。
    排队任务通过 status='pending'|'queued' 过滤。
    历史记录通过 status='success'|'failed'|'cancelled'|'timeout' 过滤。
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 任务基本信息
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # fetch_posts / fetch_comments / fetch_profile / download_media / search
    
    # 目标平台与参数
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    # 目标标识：user_id / keyword / post_id 等
    
    params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # 额外参数：limit, cursor, since, until, include_comments 等
    
    # 调度与优先级
    priority: Mapped[str] = mapped_column(
        String(16), default=TaskPriority.NORMAL.value, nullable=False, index=True
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    # 定时执行时间，NULL 表示立即执行
    
    # 执行状态
    status: Mapped[str] = mapped_column(
        String(16), default=TaskStatus.PENDING.value, nullable=False, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Celery 任务 ID
    celery_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    
    # 执行信息
    account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    proxy_used: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # 结果统计
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 采集到的数据条数
    
    result_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # 结果摘要（不存完整数据，只存统计）
    
    # 耗时（秒）
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # 创建者
    created_by: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 复合索引
    __table_args__ = (
        Index("idx_tasks_platform_status", "platform", "status"),
        Index("idx_tasks_created_status", "created_at", "status"),
        Index("idx_tasks_type_status", "task_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, platform={self.platform}, status={self.status})>"


class TaskHistoryModel(Base):
    """任务历史归档表
    
    定期将已完成的任务从 tasks 表迁移到此表，保持 tasks 表轻量。
    """
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    original_task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    # 复制自 TaskModel 的核心字段
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    
    # 原始时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 归档时间
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    __table_args__ = (
        Index("idx_history_platform_completed", "platform", "completed_at"),
        Index("idx_history_type_status", "task_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<TaskHistory(original_id={self.original_task_id}, platform={self.platform}, status={self.status})>"
