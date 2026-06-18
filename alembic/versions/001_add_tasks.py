"""add tasks and task_history tables

Revision ID: 001_add_tasks
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "001_add_tasks"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── tasks 表 ──────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("target", sa.String(512), nullable=False),
        sa.Column("params", JSONB, nullable=False, server_default="{}"),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("celery_task_id", sa.String(128), nullable=True),
        sa.Column("account_id", sa.String(128), nullable=True),
        sa.Column("proxy_used", sa.String(256), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_by", sa.String(128), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # tasks 索引
    op.create_index("ix_tasks_name", "tasks", ["name"])
    op.create_index("ix_tasks_task_type", "tasks", ["task_type"])
    op.create_index("ix_tasks_platform", "tasks", ["platform"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_scheduled_at", "tasks", ["scheduled_at"])
    op.create_index("ix_tasks_celery_task_id", "tasks", ["celery_task_id"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])
    op.create_index("idx_tasks_platform_status", "tasks", ["platform", "status"])
    op.create_index("idx_tasks_created_status", "tasks", ["created_at", "status"])
    op.create_index("idx_tasks_type_status", "tasks", ["task_type", "status"])

    # ── task_history 表 ────────────────────────────────
    op.create_table(
        "task_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("original_task_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("target", sa.String(512), nullable=False),
        sa.Column("params", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("account_id", sa.String(128), nullable=True),
        sa.Column("created_by", sa.String(128), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # task_history 索引
    op.create_index("ix_task_history_original_task_id", "task_history", ["original_task_id"])
    op.create_index("ix_task_history_platform", "task_history", ["platform"])
    op.create_index("ix_task_history_status", "task_history", ["status"])
    op.create_index("ix_task_history_archived_at", "task_history", ["archived_at"])
    op.create_index("idx_history_platform_completed", "task_history", ["platform", "completed_at"])
    op.create_index("idx_history_type_status", "task_history", ["task_type", "status"])


def downgrade() -> None:
    op.drop_table("task_history")
    op.drop_table("tasks")
