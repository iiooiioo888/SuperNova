"""Celery 任务定义"""
import structlog
from celery import Task

from .celery_app import celery_app
from ..adapters.registry import get_adapter
from ..adapters.base import FetchParams
from ..infrastructure.account_pool.service import account_pool_service

logger = structlog.get_logger()


class AdapterTask(Task):
    """适配器任务基类"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        logger.error("task.failure", task_id=task_id, error=str(exc))


@celery_app.task(base=AdapterTask, bind=True)
async def fetch_posts_task(self, platform: str, target: str, limit: int = 50):
    """获取帖子任务"""
    logger.info("task.fetch_posts", platform=platform, target=target)
    
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
        await adapter.teardown()
        await account_pool_service.release(lease)
        
        return {"count": len(posts), "posts": [str(p) for p in posts]}
    
    except Exception as e:
        # 报告失败
        if 'lease' in locals():
            await account_pool_service.report_failure(lease, str(type(e)))
        raise


@celery_app.task(base=AdapterTask, bind=True)
async def fetch_user_profile_task(self, platform: str, user_id: str):
    """获取用户资料任务"""
    logger.info("task.fetch_user_profile", platform=platform, user_id=user_id)
    
    adapter = get_adapter(platform)
    await adapter.setup()
    
    try:
        profile = await adapter.fetch_user_profile(user_id)
        return {"profile": str(profile)}
    finally:
        await adapter.teardown()