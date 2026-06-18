"""FastAPI 应用入口"""
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.v1 import tasks, platforms, accounts, data, health, dashboard, feature_flags
from .adapters import bilibili  # 注册适配器
from .api.v1.deps import engine
from .middleware.logging import RequestLoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("app.startup", name=settings.app_name)
    
    # 初始化适配器
    await bilibili.BilibiliAdapter().setup()
    
    yield
    
    # 清理资源
    logger.info("app.shutdown", name=settings.app_name)
    await engine.dispose()
    logger.info("app.db_pool_disposed")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    
    app = FastAPI(
        title=settings.app_name,
        description="统一社交数据采集平台",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # 限流中间件（每分钟 100 次请求）
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: 生产环境限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(tasks.router, prefix=settings.api_prefix, tags=["tasks"])
    app.include_router(platforms.router, prefix=settings.api_prefix, tags=["platforms"])
    app.include_router(accounts.router, prefix=settings.api_prefix, tags=["accounts"])
    app.include_router(data.router, prefix=settings.api_prefix, tags=["data"])
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(dashboard.router, prefix=settings.api_prefix, tags=["dashboard"])
    app.include_router(feature_flags.router, prefix=settings.api_prefix, tags=["feature-flags"])
    
    @app.get("/")
    async def root():
        return {"name": settings.app_name, "version": "0.1.0"}
    
    return app


app = create_app()
