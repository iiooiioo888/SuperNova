"""仪表板 API — 系统概览统计"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.v1.deps import get_db
from backend.services.task_service import task_service

router = APIRouter(prefix="/dashboard")


@router.get("/stats")
async def get_dashboard_stats(db=Depends(get_db)):
    """获取仪表板统计数据
    
    返回：
    - 各状态任务数量
    - 排队中 / 运行中任务数
    - 今日任务总数、成功数、成功率
    - 今日采集数据总量
    - 平均任务耗时
    - 各平台任务分布
    """
    stats = await task_service.get_statistics(db)
    return stats


@router.get("/summary")
async def get_dashboard_summary(db=Depends(get_db)):
    """获取仪表板摘要信息（精简版，用于卡片展示）"""
    stats = await task_service.get_statistics(db)
    return {
        "queue_count": stats["queue_count"],
        "running_count": stats["running_count"],
        "today_total": stats["today_total"],
        "today_success": stats["today_success"],
        "today_success_rate": stats["today_success_rate"],
        "today_items_collected": stats["today_items_collected"],
        "avg_duration_seconds": stats["avg_duration_seconds"],
    }
