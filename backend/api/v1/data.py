"""数据查询 API (占位)"""
from fastapi import APIRouter

router = APIRouter(prefix="/data")


@router.get("/posts")
async def get_posts():
    """获取帖子数据"""
    return {"posts": [], "count": 0}


@router.get("/users/{user_id}")
async def get_user_data(user_id: str):
    """获取用户数据"""
    return {"user_id": user_id, "data": {}}
