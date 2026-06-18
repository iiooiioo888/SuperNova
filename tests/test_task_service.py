"""任务服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from backend.services.task_service import TaskService
from backend.models.pg.task import TaskStatus, TaskPriority


@pytest.fixture
def service():
    return TaskService()


@pytest.mark.asyncio
async def test_create_task(service, mock_db):
    """测试创建任务"""
    task = await service.create_task(
        mock_db,
        name="test-task",
        task_type="fetch_posts",
        platform="bilibili",
        target="user_123",
    )
    assert mock_db.add.called
    assert mock_db.flush.called
    assert mock_db.refresh.called


@pytest.mark.asyncio
async def test_get_task_not_found(service, mock_db):
    """测试获取不存在的任务"""
    result = await service.get_task(mock_db, 999)
    assert result is None


@pytest.mark.asyncio
async def test_cancel_task_not_found(service, mock_db):
    """测试取消不存在的任务"""
    result = await service.cancel_task(mock_db, 999)
    assert result is None


@pytest.mark.asyncio
async def test_delete_task_not_found(service, mock_db):
    """测试删除不存在的任务"""
    result = await service.delete_task(mock_db, 999)
    assert result is False


@pytest.mark.asyncio
async def test_retry_task_not_failed(service, mock_db):
    """测试重试非失败状态的任务"""
    mock_task = MagicMock()
    mock_task.status = TaskStatus.SUCCESS.value
    mock_task.retry_count = 0
    mock_task.max_retries = 3

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_task)
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await service.retry_task(mock_db, 1)
    assert result is None


@pytest.mark.asyncio
async def test_retry_task_max_exceeded(service, mock_db):
    """测试超过最大重试次数"""
    mock_task = MagicMock()
    mock_task.status = TaskStatus.FAILED.value
    mock_task.retry_count = 5
    mock_task.max_retries = 3

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_task)
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await service.retry_task(mock_db, 1)
    assert result is None
