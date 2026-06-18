"""任务管理 API (占位)"""
from fastapi import APIRouter

router = APIRouter(prefix="/tasks")


@router.get("/")
async def list_tasks():
    """列出所有任务"""
    return {"tasks": [], "count": 0}


@router.post("/")
async def create_task():
    """创建新任务"""
    return {"status": "ok", "task_id": "placeholder"}


@router.get("/{task_id}")
async def get_task(task_id: str):
    """获取任务详情"""
    return {"task_id": task_id, "status": "pending"}
