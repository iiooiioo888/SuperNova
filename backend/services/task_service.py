"""任务服务 — 任务 CRUD、队列管理、历史归档"""
from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import Optional

import structlog
from sqlalchemy import select, func, update, delete, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pg.task import TaskModel, TaskHistoryModel, TaskStatus, TaskPriority

logger = structlog.get_logger()


class TaskService:
    """任务业务逻辑层"""

    # ── 创建任务 ────────────────────────────────────────

    async def create_task(
        self,
        db: AsyncSession,
        *,
        name: str,
        task_type: str,
        platform: str,
        target: str,
        params: dict | None = None,
        priority: str = TaskPriority.NORMAL.value,
        scheduled_at: datetime | None = None,
        max_retries: int = 3,
        created_by: str = "system",
    ) -> TaskModel:
        """创建新任务"""
        task = TaskModel(
            name=name,
            task_type=task_type,
            platform=platform,
            target=target,
            params=params or {},
            priority=priority,
            scheduled_at=scheduled_at,
            max_retries=max_retries,
            status=TaskStatus.PENDING.value,
            created_by=created_by,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)
        logger.info(
            "task.created",
            task_id=task.id,
            platform=platform,
            task_type=task_type,
            target=target,
        )
        return task

    # ── 查询任务 ────────────────────────────────────────

    async def get_task(self, db: AsyncSession, task_id: int) -> TaskModel | None:
        """获取单个任务"""
        result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        platform: str | None = None,
        task_type: str | None = None,
        created_by: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TaskModel], int]:
        """列出任务（支持过滤和分页）"""
        query = select(TaskModel)
        count_query = select(func.count(TaskModel.id))

        conditions = []
        if status:
            conditions.append(TaskModel.status == status)
        if platform:
            conditions.append(TaskModel.platform == platform)
        if task_type:
            conditions.append(TaskModel.task_type == task_type)
        if created_by:
            conditions.append(TaskModel.created_by == created_by)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = query.order_by(desc(TaskModel.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        tasks = list(result.scalars().all())

        return tasks, total

    async def list_queued_tasks(
        self,
        db: AsyncSession,
        *,
        platform: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TaskModel], int]:
        """列出排队中的任务（pending + queued + retrying）"""
        queue_statuses = [
            TaskStatus.PENDING.value,
            TaskStatus.QUEUED.value,
            TaskStatus.RETRYING.value,
        ]
        query = select(TaskModel).where(TaskModel.status.in_(queue_statuses))
        count_query = select(func.count(TaskModel.id)).where(
            TaskModel.status.in_(queue_statuses)
        )

        if platform:
            query = query.where(TaskModel.platform == platform)
            count_query = count_query.where(TaskModel.platform == platform)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 按优先级排序：urgent > high > normal > low，然后按创建时间
        # 在 SQL 层排序，确保分页结果正确
        from sqlalchemy import case
        priority_order = case(
            (TaskModel.priority == TaskPriority.URGENT.value, 0),
            (TaskModel.priority == TaskPriority.HIGH.value, 1),
            (TaskModel.priority == TaskPriority.NORMAL.value, 2),
            (TaskModel.priority == TaskPriority.LOW.value, 3),
            else_=2,
        )
        query = query.order_by(priority_order, TaskModel.created_at)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        tasks = list(result.scalars().all())

        return tasks, total

    async def list_history(
        self,
        db: AsyncSession,
        *,
        platform: str | None = None,
        task_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TaskHistoryModel], int]:
        """列出历史任务"""
        query = select(TaskHistoryModel)
        count_query = select(func.count(TaskHistoryModel.id))

        conditions = []
        if platform:
            conditions.append(TaskHistoryModel.platform == platform)
        if task_type:
            conditions.append(TaskHistoryModel.task_type == task_type)
        if status:
            conditions.append(TaskHistoryModel.status == status)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(TaskHistoryModel.completed_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        tasks = list(result.scalars().all())

        return tasks, total

    # ── 更新任务状态 ────────────────────────────────────

    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: int,
        *,
        status: str,
        celery_task_id: str | None = None,
        account_id: str | None = None,
        error_message: str | None = None,
        error_code: str | None = None,
        result_count: int | None = None,
        result_data: dict | None = None,
    ) -> TaskModel | None:
        """更新任务状态"""
        task = await self.get_task(db, task_id)
        if not task:
            return None

        task.status = status
        now = datetime.now(UTC)

        if status == TaskStatus.RUNNING.value:
            task.started_at = now
        elif status in (
            TaskStatus.SUCCESS.value,
            TaskStatus.FAILED.value,
            TaskStatus.CANCELLED.value,
            TaskStatus.TIMEOUT.value,
        ):
            task.completed_at = now
            if task.started_at:
                task.duration_seconds = (now - task.started_at).total_seconds()

        if celery_task_id is not None:
            task.celery_task_id = celery_task_id
        if account_id is not None:
            task.account_id = account_id
        if error_message is not None:
            task.error_message = error_message
        if error_code is not None:
            task.error_code = error_code
        if result_count is not None:
            task.result_count = result_count
        if result_data is not None:
            task.result_data = result_data

        task.updated_at = now
        await db.flush()
        await db.refresh(task)

        logger.info(
            "task.status_updated",
            task_id=task_id,
            new_status=status,
        )
        return task

    async def cancel_task(self, db: AsyncSession, task_id: int) -> TaskModel | None:
        """取消任务（仅 pending/queued 状态可取消）"""
        task = await self.get_task(db, task_id)
        if not task:
            return None
        if task.status not in (TaskStatus.PENDING.value, TaskStatus.QUEUED.value):
            return None
        return await self.update_task_status(
            db, task_id, status=TaskStatus.CANCELLED.value
        )

    async def retry_task(self, db: AsyncSession, task_id: int) -> TaskModel | None:
        """重试失败的任务"""
        task = await self.get_task(db, task_id)
        if not task:
            return None
        if task.status not in (TaskStatus.FAILED.value, TaskStatus.TIMEOUT.value):
            return None
        if task.retry_count >= task.max_retries:
            return None

        task.retry_count += 1
        return await self.update_task_status(
            db, task_id, status=TaskStatus.RETRYING.value
        )

    async def delete_task(self, db: AsyncSession, task_id: int) -> bool:
        """删除任务"""
        task = await self.get_task(db, task_id)
        if not task:
            return False
        await db.delete(task)
        await db.flush()
        logger.info("task.deleted", task_id=task_id)
        return True

    # ── 历史归档 ────────────────────────────────────────

    async def archive_completed_tasks(
        self,
        db: AsyncSession,
        *,
        older_than_hours: int = 24,
    ) -> int:
        """将已完成的任务归档到历史表"""
        cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
        completed_statuses = [
            TaskStatus.SUCCESS.value,
            TaskStatus.FAILED.value,
            TaskStatus.CANCELLED.value,
            TaskStatus.TIMEOUT.value,
        ]

        # 查询待归档任务
        result = await db.execute(
            select(TaskModel).where(
                and_(
                    TaskModel.status.in_(completed_statuses),
                    TaskModel.completed_at < cutoff,
                )
            )
        )
        tasks = list(result.scalars().all())

        for task in tasks:
            history = TaskHistoryModel(
                original_task_id=task.id,
                name=task.name,
                task_type=task.task_type,
                platform=task.platform,
                target=task.target,
                params=task.params,
                status=task.status,
                retry_count=task.retry_count,
                error_message=task.error_message,
                error_code=task.error_code,
                result_count=task.result_count,
                result_data=task.result_data,
                duration_seconds=task.duration_seconds,
                account_id=task.account_id,
                created_by=task.created_by,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
            )
            db.add(history)
            await db.delete(task)

        await db.flush()
        logger.info("task.archived", count=len(tasks))
        return len(tasks)

    # ── 统计 ────────────────────────────────────────────

    async def get_statistics(self, db: AsyncSession) -> dict:
        """获取任务统计概览（优化：8 次查询 → 2 次）"""
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        from sqlalchemy import case as sa_case

        # ── 第 1 次查询：各状态×平台 聚合
        agg_result = await db.execute(
            select(
                TaskModel.status,
                TaskModel.platform,
                func.count(TaskModel.id).label("cnt"),
            ).group_by(TaskModel.status, TaskModel.platform)
        )
        rows = agg_result.all()

        status_counts: dict[str, int] = {}
        platform_counts: dict[str, int] = {}
        running_by_platform: dict[str, int] = {}

        for status_val, platform_val, cnt in rows:
            status_counts[status_val] = status_counts.get(status_val, 0) + cnt
            platform_counts[platform_val] = platform_counts.get(platform_val, 0) + cnt
            if status_val == TaskStatus.RUNNING.value:
                running_by_platform[platform_val] = cnt

        # ── 第 2 次查询：今日汇总（一次聚合）
        today_result = await db.execute(
            select(
                func.count(TaskModel.id).label("total"),
                func.count(
                    sa_case((TaskModel.status == TaskStatus.SUCCESS.value, 1))
                ).label("success"),
                func.coalesce(func.sum(
                    sa_case(
                        (TaskModel.status == TaskStatus.SUCCESS.value, TaskModel.result_count),
                        else_=0,
                    )
                ), 0).label("items"),
                func.coalesce(func.avg(
                    sa_case((TaskModel.status == TaskStatus.SUCCESS.value, TaskModel.duration_seconds))
                ), 0).label("avg_dur"),
            ).where(TaskModel.created_at >= today_start)
        )
        tr = today_result.one()

        today_total = tr.total or 0
        today_success = tr.success or 0
        today_items = int(tr.items or 0)
        avg_duration = round(float(tr.avg_dur or 0), 2)

        queue_count = (
            status_counts.get(TaskStatus.PENDING.value, 0)
            + status_counts.get(TaskStatus.QUEUED.value, 0)
            + status_counts.get(TaskStatus.RETRYING.value, 0)
        )

        return {
            "status_counts": status_counts,
            "queue_count": queue_count,
            "running_count": status_counts.get(TaskStatus.RUNNING.value, 0),
            "today_total": today_total,
            "today_success": today_success,
            "today_success_rate": round(today_success / today_total * 100, 1) if today_total > 0 else 0,
            "today_items_collected": today_items,
            "avg_duration_seconds": avg_duration,
            "platform_counts": platform_counts,
            "running_by_platform": running_by_platform,
        }


# 全局单例
task_service = TaskService()
