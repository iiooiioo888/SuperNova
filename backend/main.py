"""FastAPI 应用入口"""
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.v1 import tasks, platforms, accounts, data, health, dashboard, feature_flags
from .api.exception_handlers import register_exception_handlers
from .adapters import bilibili  # 注册适配器
from .api.v1.deps import engine
from .middleware.logging import RequestLoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.security import SecurityHeadersMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("app.startup", name=settings.app_name)
    
    # 初始化适配器
    await bilibili.BilibiliAdapter().setup()
    
    yield
    
    # 优雅关闭：等待进行中的请求完成
    logger.info("app.shutdown.begin", name=settings.app_name)
    
    # 关闭适配器
    try:
        await bilibili.BilibiliAdapter().teardown()
    except Exception as e:
        logger.warning("app.adapter_teardown_error", error=str(e))
    
    # 关闭数据库连接池
    await engine.dispose()
    logger.info("app.shutdown.complete")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    
    app = FastAPI(
        title=settings.app_name,
        description="""## 统一社交数据采集平台

企业级多平台社交数据采集系统，支持：
- **多平台适配器**：B站、抖音、微博、Instagram、Telegram
- **三层存储架构**：MongoDB（原始）+ PostgreSQL（标准化）+ Elasticsearch（检索）
- **企业级容错**：熔断器、差异化重试、账号池管理、代理池评分
- **动态功能开关**：四层控制（全局/平台/功能/策略），支持热更新
- **RBAC 权限控制**：精细化权限控制

### 认证
所有 API 需要通过 `Authorization: Bearer <token>` 认证（开发环境可关闭）。

### 限流
- 默认：100 请求/分钟/IP
- 健康检查接口不限流
""",
        version="0.2.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "tasks", "description": "任务管理 — 创建、查询、取消、重试采集任务"},
            {"name": "platforms", "description": "平台管理 — 查看已接入平台及能力"},
            {"name": "accounts", "description": "账号池 — 管理采集账号的租约和状态"},
            {"name": "data", "description": "数据查询 — 查询已采集的帖子、用户、评论数据"},
            {"name": "health", "description": "健康检查 — 服务就绪和组件状态检测"},
            {"name": "dashboard", "description": "仪表板 — 系统统计概览"},
            {"name": "feature-flags", "description": "功能开关 — 动态控制功能启停和灰度发布"},
        ],
    )
    
    # 注册全局异常处理器
    register_exception_handlers(app)
    
    # 安全 headers
    app.add_middleware(SecurityHeadersMiddleware)
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
