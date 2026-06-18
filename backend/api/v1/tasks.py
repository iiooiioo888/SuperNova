"""任务管理 API — 排队任务 / 历史记录 / CRUD"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum

from backend.api.v1.deps import get_db
from backend.services.task_service import task_service

router = APIRouter(prefix="/tasks")


# ── 枚举校验 ────────────────────────────────────────────

class TaskTypeEnum(str, Enum):
    FETCH_POSTS = "fetch_posts"
    FETCH_COMMENTS = "fetch_comments"
    FETCH_PROFILE = "fetch_profile"
    DOWNLOAD_MEDIA = "download_media"
    SEARCH = "search"


class PriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ── 请求/响应模型 ────────────────────────────────────────


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    name: str = Field(..., min_length=1, max_length=256, description="任务名称")
    task_type: TaskTypeEnum = Field(..., description="任务类型")
    platform: str = Field(..., min_length=1, max_length=64, description="目标平台")
    target: str = Field(..., min_length=1, max_length=512, description="目标标识")
    params: dict = Field(default_factory=dict, description="额外参数")
    priority: PriorityEnum = Field(default=PriorityEnum.NORMAL, description="优先级")
    scheduled_at: Optional[datetime] = Field(default=None, description="定时执行时间")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    created_by: str = Field(default="user", description="创建者")


class TaskBatchCreateRequest(BaseModel):
    """批量创建任务"""
    tasks: list[TaskCreateRequest] = Field(..., min_length=1, max_length=100)


class TaskBatchStatusRequest(BaseModel):
    """批量查询任务状态"""
    task_ids: list[int] = Field(..., min_length=1, max_length=200)


class TaskUpdateStatusRequest(BaseModel):
    """更新任务状态"""
    status: str
    celery_task_id: Optional[str] = None
    account_id: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    result_count: Optional[int] = None
    result_data: Optional[dict] = None


class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    name: str
    task_type: str
    platform: str
    target: str
    params: dict
    priority: str
    scheduled_at: Optional[datetime]
    status: str
    retry_count: int
    max_retries: int
    celery_task_id: Optional[str]
    account_id: Optional[str]
    error_message: Optional[str]
    error_code: Optional[str]
    result_count: int
    result_data: dict
    duration_seconds: Optional[float]
    created_by: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskHistoryResponse(BaseModel):
    """历史任务响应"""
    id: int
    original_task_id: int
    name: str
    task_type: str
    platform: str
    target: str
    params: dict
    status: str
    retry_count: int
    error_message: Optional[str]
    error_code: Optional[str]
    result_count: int
    result_data: dict
    duration_seconds: Optional[float]
    created_by: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    archived_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list
    total: int
    page: int
    page_size: int
    pages: int


# ── 端点 ────────────────────────────────────────────────


@router.get("/", response_model=PaginatedResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="按状态过滤"),
    platform: Optional[str] = Query(None, description="按平台过滤"),
    task_type: Optional[str] = Query(None, description="按任务类型过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """列出所有任务（支持过滤和分页）"""
    tasks, total = await task_service.list_tasks(
        db,
        status=status,
        platform=platform,
        task_type=task_type,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/queue", response_model=PaginatedResponse)
async def list_queued_tasks(
    platform: Optional[str] = Query(None, description="按平台过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """列出排队中的任务（pending / queued / retrying）"""
    tasks, total = await task_service.list_queued_tasks(
        db, platform=platform, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/history", response_model=PaginatedResponse)
async def list_task_history(
    platform: Optional[str] = Query(None, description="按平台过滤"),
    task_type: Optional[str] = Query(None, description="按任务类型过滤"),
    status: Optional[str] = Query(None, description="按状态过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """列出历史任务"""
    tasks, total = await task_service.list_history(
        db,
        platform=platform,
        task_type=task_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[TaskHistoryResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=TaskResponse)
async def create_task(body: TaskCreateRequest, db=Depends(get_db)):
    """创建新任务"""
    task = await task_service.create_task(
        db,
        name=body.name,
        task_type=body.task_type,
        platform=body.platform,
        target=body.target,
        params=body.params,
        priority=body.priority,
        scheduled_at=body.scheduled_at,
        max_retries=body.max_retries,
        created_by=body.created_by,
    )
    return TaskResponse.model_validate(task)


@router.post("/batch", response_model=dict)
async def batch_create_tasks(body: TaskBatchCreateRequest, db=Depends(get_db)):
    """批量创建任务"""
    created = []
    for item in body.tasks:
        task = await task_service.create_task(
            db,
            name=item.name,
            task_type=item.task_type,
            platform=item.platform,
            target=item.target,
            params=item.params,
            priority=item.priority,
            scheduled_at=item.scheduled_at,
            max_retries=item.max_retries,
            created_by=item.created_by,
        )
        created.append(TaskResponse.model_validate(task))
    return {"created": len(created), "tasks": created}


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db=Depends(get_db)):
    """获取任务详情"""
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(task_id: int, body: TaskUpdateStatusRequest, db=Depends(get_db)):
    """更新任务状态"""
    task = await task_service.update_task_status(
        db,
        task_id,
        status=body.status,
        celery_task_id=body.celery_task_id,
        account_id=body.account_id,
        error_message=body.error_message,
        error_code=body.error_code,
        result_count=body.result_count,
        result_data=body.result_data,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: int, db=Depends(get_db)):
    """取消任务"""
    task = await task_service.cancel_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel: task not found or not in cancellable state",
        )
    return TaskResponse.model_validate(task)


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(task_id: int, db=Depends(get_db)):
    """重试失败的任务"""
    task = await task_service.retry_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=400,
            detail="Cannot retry: task not found, not failed, or max retries exceeded",
        )
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def delete_task(task_id: int, db=Depends(get_db)):
    """删除任务"""
    deleted = await task_service.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "ok", "deleted": task_id}


@router.post("/archive", response_model=dict)
async def archive_completed_tasks(
    older_than_hours: int = Query(24, ge=1, le=720),
    db=Depends(get_db),
):
    """归档已完成任务到历史表"""
    count = await task_service.archive_completed_tasks(db, older_than_hours=older_than_hours)
    return {"archived": count}


@router.post("/batch-status", response_model=dict)
async def batch_get_task_status(body: TaskBatchStatusRequest, db=Depends(get_db)):
    """批量查询任务状态（用于前端轮询）"""
    from sqlalchemy import select
    from backend.models.pg.task import TaskModel
    
    result = await db.execute(
        select(TaskModel).where(TaskModel.id.in_(body.task_ids))
    )
    tasks = result.scalars().all()
    
    task_map = {t.id: t for t in tasks}
    statuses = {}
    for tid in body.task_ids:
        t = task_map.get(tid)
        if t:
            statuses[tid] = {
                "status": t.status,
                "result_count": t.result_count,
                "error_message": t.error_message,
                "duration_seconds": t.duration_seconds,
            }
        else:
            statuses[tid] = None
    
    return {"tasks": statuses}
