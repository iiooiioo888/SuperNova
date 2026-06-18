"""Celery 任务定义"""
import asyncio
import structlog
from celery import Task

from .celery_app import celery_app
from ..adapters.registry import get_adapter
from ..adapters.base import FetchParams
from ..infrastructure.account_pool.service import account_pool_service
from ..api.v1.deps import async_session_factory
from ..services.task_service import task_service

logger = structlog.get_logger()


class AdapterTask(Task):
    """适配器任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        logger.error("task.failure", task_id=task_id, error=str(exc))

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        logger.info("task.success", task_id=task_id)


def _run_async(coro):
    """在 Celery worker 中运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 嵌套事件循环场景
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(base=AdapterTask, bind=True)
def fetch_posts_task(self, platform: str, target: str, limit: int = 50, task_id: int | None = None):
    """获取帖子任务
    
    Args:
        platform: 目标平台
        target: 目标标识
        limit: 获取数量
        task_id: 数据库任务 ID（用于更新状态）
    """
    logger.info("task.fetch_posts", platform=platform, target=target, celery_task_id=self.request.id)
    return _run_async(_fetch_posts(platform, target, limit, task_id, self.request.id))


async def _fetch_posts(platform: str, target: str, limit: int, task_id: int | None, celery_task_id: str):
    """异步实现：获取帖子"""
    lease = None
    adapter = None

    # 更新任务状态为 running
    if task_id:
        async with async_session_factory() as db:
            await task_service.update_task_status(
                db, task_id,
                status="running",
                celery_task_id=celery_task_id,
            )

    try:
        # 获取账号
        lease = await account_pool_service.acquire(platform, "fetch_posts")

        # 获取适配器
        adapter = get_adapter(platform)
        await adapter.setup()

        # 执行采集
        params = FetchParams(limit=limit)
        posts = []
        async for post in adapter.fetch_posts(target, params):
            posts.append(post)

        # 报告成功
        await account_pool_service.report_success(lease)

        # 更新任务状态为 success
        if task_id:
            async with async_session_factory() as db:
                await task_service.update_task_status(
                    db, task_id,
                    status="success",
                    result_count=len(posts),
                    account_id=lease.account_id,
                )

        return {"count": len(posts), "platform": platform, "target": target}

    except Exception as e:
        logger.error("task.fetch_posts.failed", platform=platform, target=target, error=str(e))

        # 报告失败
        if lease:
            await account_pool_service.report_failure(lease, str(type(e)))

        # 更新任务状态为 failed
        if task_id:
            async with async_session_factory() as db:
                await task_service.update_task_status(
                    db, task_id,
                    status="failed",
                    error_message=str(e),
                    error_code=type(e).__name__,
                )
        raise

    finally:
        if adapter:
            await adapter.teardown()
        if lease:
            await account_pool_service.release(lease)


@celery_app.task(base=AdapterTask, bind=True)
def fetch_user_profile_task(self, platform: str, user_id: str, task_id: int | None = None):
    """获取用户资料任务"""
    logger.info("task.fetch_user_profile", platform=platform, user_id=user_id)
    return _run_async(_fetch_user_profile(platform, user_id, task_id, self.request.id))


async def _fetch_user_profile(platform: str, user_id: str, task_id: int | None, celery_task_id: str):
    """异步实现：获取用户资料"""
    adapter = None

    if task_id:
        async with async_session_factory() as db:
            await task_service.update_task_status(
                db, task_id,
                status="running",
                celery_task_id=celery_task_id,
            )

    try:
        adapter = get_adapter(platform)
        await adapter.setup()
        profile = await adapter.fetch_user_profile(user_id)

        if task_id:
            async with async_session_factory() as db:
                await task_service.update_task_status(db, task_id, status="success")

        return {"profile": str(profile), "platform": platform, "user_id": user_id}

    except Exception as e:
        logger.error("task.fetch_profile.failed", platform=platform, user_id=user_id, error=str(e))
        if task_id:
            async with async_session_factory() as db:
                await task_service.update_task_status(
                    db, task_id,
                    status="failed",
                    error_message=str(e),
                    error_code=type(e).__name__,
                )
        raise

    finally:
        if adapter:
            await adapter.teardown()
