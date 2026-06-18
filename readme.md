这是一份可以直接用于 AI 编程助手（Cursor / Claude / Copilot 等）的项目级系统提示词，涵盖了我们讨论过的所有设计决策：

---

```
# SuperHub — 统一社交数据采集平台

## 项目概述

SuperHub 是一个多平台社交数据采集系统，目标是通过统一的接口管理多个社交平台的数据采集任务。系统采用 Python 异步架构，支持插件化接入新平台，具备完善的任务调度、账号管理、反封禁和监控能力。

## 核心架构

五层架构，自上而下：
1. **用户交互层** — FastAPI REST API + React Web UI + CLI 工具
2. **任务调度层** — Celery + Redis（默认），Airflow 按需启用
3. **适配器层** — 每个社交平台一个 Adapter，插件化设计，统一接口
4. **基础设施层** — 代理池、账号池、会话管理、熔断器、限流控制
5. **数据存储层** — MongoDB（原始数据）+ PostgreSQL（结构化数据）+ Elasticsearch（索引检索）+ OSS/S3（媒体文件）

## 技术栈

- **后端框架**: FastAPI + Python 3.11+
- **异步运行时**: asyncio + uvloop
- **任务队列**: Celery + Redis（broker & backend）
- **HTTP 客户端**: curl_cffi（模拟 TLS 指纹）或 httpx
- **数据库**: MongoDB（Motor 异步驱动）+ PostgreSQL（SQLAlchemy 2.0 async + asyncpg）
- **搜索引擎**: Elasticsearch（elasticsearch-py async）
- **对象存储**: MinIO / 阿里云 OSS
- **监控**: Prometheus + Grafana
- **日志**: structlog（结构化日志）
- **容器化**: Docker + docker-compose
- **前端**: React + TypeScript + Ant Design
- **测试**: pytest + pytest-asyncio + respx（HTTP mock）

## 适配器接口规范

### 双模式设计

每个适配器必须实现标准接口，并可通过 capabilities 机制暴露平台特有功能。

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator
from pathlib import Path


# ── 统一数据模型 ──────────────────────────────────────────

@dataclass
class MediaRef:
    platform_media_id: str
    media_type: str  # "image" | "video" | "audio" | "document"
    url: str
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    file_size_bytes: int | None = None

@dataclass
class EngagementMetrics:
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    saves: int = 0
    platform_specific: dict[str, Any] = field(default_factory=dict)

@dataclass
class UnifiedPost:
    platform: str
    platform_post_id: str
    author_id: str
    author_name: str | None = None
    content_type: str  # "text" | "image" | "video" | "story" | "reel"
    text: str = ""
    media: list[MediaRef] = field(default_factory=list)
    metrics: EngagementMetrics = field(default_factory=EngagementMetrics)
    tags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    language: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    raw_data: dict[str, Any] = field(default_factory=dict)

@dataclass
class UnifiedProfile:
    platform: str
    platform_user_id: str
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    follower_count: int | None = None
    following_count: int | None = None
    post_count: int | None = None
    is_verified: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class UnifiedComment:
    platform: str
    platform_comment_id: str
    platform_post_id: str
    author_id: str
    author_name: str | None = None
    text: str = ""
    likes: int = 0
    reply_to_comment_id: str | None = None
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=datetime.utcnow)


# ── 采集参数 ──────────────────────────────────────────────

@dataclass
class FetchParams:
    limit: int = 50
    cursor: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    include_comments: bool = False
    max_depth: int = 1


# ── 能力描述 ──────────────────────────────────────────────

@dataclass
class Capability:
    name: str
    description: str
    params_schema: dict[str, Any]
    returns_schema: dict[str, Any]


# ── 基类 ─────────────────────────────────────────────────

class BaseAdapter(ABC):
    platform: str  # 子类必须定义

    # -- 标准模式（所有平台必须实现）--

    @abstractmethod
    async def fetch_user_profile(self, user_id: str) -> UnifiedProfile:
        """获取用户资料"""
        ...

    @abstractmethod
    async def fetch_posts(
        self, target: str, params: FetchParams
    ) -> AsyncIterator[UnifiedPost]:
        """获取帖子列表，支持分页游标"""
        ...

    @abstractmethod
    async def fetch_comments(
        self, post_id: str, params: FetchParams
    ) -> AsyncIterator[UnifiedComment]:
        """获取评论列表"""
        ...

    @abstractmethod
    async def download_media(
        self, media: MediaRef, dest: Path
    ) -> Path:
        """下载媒体文件到指定路径"""
        ...

    @abstractmethod
    async def search(
        self, query: str, params: FetchParams
    ) -> AsyncIterator[UnifiedPost]:
        """搜索公开内容"""
        ...

    # -- 高级模式（平台特有功能）--

    def capabilities(self) -> list[Capability]:
        """返回平台特有能力列表，默认为空"""
        return []

    async def invoke(self, capability_name: str, **kwargs) -> Any:
        """调用平台特有能力"""
        supported = {c.name for c in self.capabilities()}
        if capability_name not in supported:
            raise CapabilityNotSupported(capability_name, self.platform)
        raise NotImplementedError

    # -- 生命周期 --

    async def setup(self) -> None:
        """初始化时调用，用于建立连接、验证凭证等"""
        pass

    async def teardown(self) -> None:
        """清理资源"""
        pass
```

### 适配器注册与发现

适配器通过入口点（entry points）或显式注册表注册。新增平台只需：
1. 在 `backend/adapters/{platform}/` 下创建适配器实现
2. 实现 `BaseAdapter` 的所有抽象方法
3. 在注册表中注册

```python
# backend/adapters/registry.py
_adapter_registry: dict[str, type[BaseAdapter]] = {}

def register_adapter(platform_name: str):
    def decorator(cls):
        _adapter_registry[platform_name] = cls
        return cls
    return decorator

def get_adapter(platform: str) -> BaseAdapter:
    cls = _adapter_registry.get(platform)
    if not cls:
        raise UnknownPlatformError(platform)
    return cls()
```

## 账号池服务

账号池作为独立服务运行，与适配器解耦。

### 账号状态机（简化版）

```
active ──失败──► cooldown ──冷却完成──► active
  │                                        │
  │           连续失败达阈值               │
  └────────────► banned                    │
                    ▲                      │
                    └──────────────────────┘
```

### 接口

```python
@dataclass
class AccountLease:
    lease_id: str
    platform: str
    credentials: dict[str, Any]  # cookies, tokens, headers 等
    account_id: str
    acquired_at: datetime
    expires_at: datetime

class AccountPoolService:
    async def acquire(self, platform: str, task_type: str) -> AccountLease: ...
    async def report_success(self, lease: AccountLease) -> None: ...
    async def report_failure(self, lease: AccountLease, error_type: str) -> None: ...
    async def release(self, lease: AccountLease) -> None: ...
    async def health_check(self, platform: str) -> dict: ...
```

关键设计：
- `acquire` 返回 Lease（租约），含超时机制，防止账号被长期占用
- 每个账号维护权重分数（基于年龄、成功率、近期使用频率）
- 租约过期自动释放，由后台定时任务扫描清理

## 容错设计

### 重试策略

根据错误类型差异化处理：

| 错误类型 | 重试策略 |
|---|---|
| 网络超时 | 指数退避，1s → 2s → 4s → 8s，最多 3 次 |
| 频率限制 (HTTP 429) | 读取 Retry-After 头，长间隔退避 + 切换账号 |
| 账号被封禁 | 标记账号 banned，切换账号，不重试该账号 |
| 内容已删除 (HTTP 404) | 记录状态，跳过，不重试 |
| 数据格式异常 | 立即告警，不重试，需要人工介入适配器 |

### 熔断器

每个平台独立配置熔断器，使用 pybreaker：

```python
# 配置存数据库，运行时可热更新
CIRCUIT_BREAKER_CONFIG = {
    "bilibili": {"fail_max": 15, "reset_timeout": 300},
    "douyin": {"fail_max": 10, "reset_timeout": 600},
    "instagram": {"fail_max": 20, "reset_timeout": 300},
    "telegram": {"fail_max": 30, "reset_timeout": 180},
}
```

熔断触发后：任务回队列，延迟重试，发送告警通知。

## 数据存储

### 三层存储

| 层级 | 存储引擎 | 内容 | 写入时机 |
|---|---|---|---|
| Raw 层 | MongoDB | 平台原始 JSON 响应 | 采集时立即写入 |
| Standard 层 | PostgreSQL | UnifiedPost / UnifiedProfile / UnifiedComment | 适配器标准化后写入 |
| Analytics 层 | Elasticsearch | 聚合索引，供搜索和分析 | Standard 层写入后异步同步 |

### 去重

Standard 层用 `(platform, platform_post_id)` 做唯一约束，采用 UPSERT 策略。Raw 层保留所有版本，不做去重。

```sql
CREATE TABLE unified_posts (
    id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(32) NOT NULL,
    platform_post_id VARCHAR(255) NOT NULL,
    author_id VARCHAR(255) NOT NULL,
    content_type VARCHAR(32) NOT NULL,
    text TEXT,
    media JSONB,
    metrics JSONB,
    tags TEXT[],
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (platform, platform_post_id)
);

CREATE INDEX idx_posts_platform_author ON unified_posts(platform, author_id);
CREATE INDEX idx_posts_published ON unified_posts(platform, published_at DESC);
```

## 项目结构

```
SuperHub/
├── backend/
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # 配置管理（Pydantic Settings）
│   ├── api/
│   │   ├── v1/
│   │   │   ├── tasks.py            # 任务 CRUD API
│   │   │   ├── platforms.py        # 平台管理 API
│   │   │   ├── accounts.py         # 账号池 API
│   │   │   ├── data.py             # 数据查询 API
│   │   │   └── health.py           # 健康检查
│   │   └── deps.py                 # 依赖注入
│   ├── adapters/
│   │   ├── base.py                 # BaseAdapter + 数据模型
│   │   ├── registry.py             # 适配器注册表
│   │   ├── bilibili/
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py          # BilibiliAdapter 实现
│   │   │   ├── parser.py           # 响应解析
│   │   │   ├── constants.py
│   │   │   └── tests/
│   │   │       ├── test_adapter.py
│   │   │       └── fixtures/       # Mock 响应样本
│   │   ├── douyin/
│   │   ├── weibo/
│   │   ├── instagram/
│   │   ├── telegram/
│   │   └── ...
│   ├── scheduler/
│   │   ├── celery_app.py           # Celery 实例配置
│   │   ├── tasks.py                # 通用任务定义
│   │   ├── beats.py                # 定时任务配置
│   │   └── retry.py                # 重试策略
│   ├── infrastructure/
│   │   ├── proxy_pool/
│   │   │   ├── service.py          # 代理池管理
│   │   │   ├── providers/          # 代理供应商对接
│   │   │   └── scorer.py           # 代理质量评分
│   │   ├── account_pool/
│   │   │   ├── service.py          # 账号池服务
│   │   │   ├── models.py           # 账号模型 & Lease
│   │   │   └── state_machine.py    # 状态流转
│   │   ├── circuit_breaker.py      # 熔断器封装
│   │   └── rate_limiter.py         # 限流器
│   ├── models/
│   │   ├── mongo/                  # MongoDB 文档模型
│   │   ├── pg/                     # PostgreSQL ORM 模型
│   │   └── es/                     # ES 索引映射
│   ├── services/
│   │   ├── task_service.py         # 任务业务逻辑
│   │   ├── data_service.py         # 数据查询 & 导出
│   │   └── monitoring.py           # 指标采集
│   ├── storage/
│   │   ├── raw_store.py            # MongoDB 写入
│   │   ├── standard_store.py       # PostgreSQL 写入
│   │   ├── media_store.py          # OSS/S3 文件存储
│   │   └── index_sync.py           # ES 索引同步
│   └── utils/
│       ├── logging.py              # structlog 配置
│       ├── fingerprint.py          # HTTP 指纹工具
│       └── helpers.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── TaskManager.tsx
│   │   │   ├── PlatformExplorer.tsx
│   │   │   ├── AccountPool.tsx
│   │   │   └── DataViewer.tsx
│   │   ├── components/
│   │   └── services/
│   │       └── api.ts              # 后端 API 调用
│   ├── package.json
│   └── vite.config.ts
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.celery
│   └── docker-compose.yml
├── scripts/
│   ├── init_db.py
│   └── seed_accounts.py
├── tests/
│   ├── conftest.py                 # 共享 fixtures
│   ├── integration/
│   └── e2e/
├── pyproject.toml
└── README.md
```

## 编码规范

### Python

- 使用 Python 3.11+ 特性（match-case、ExceptionGroup 等）
- 类型注解全覆盖，使用 `from __future__ import annotations`
- 异步优先，所有 I/O 操作使用 async/await
- 日志使用 structlog，不要用 print 或标准 logging
- 错误处理：自定义异常体系，不要裸 except
- 配置通过 Pydantic Settings 管理，支持环境变量和 .env 文件

### 异常体系

```python
class SuperHubError(Exception):
    """基类"""
    pass

class AdapterError(SuperHubError):
    """适配器层错误"""
    pass

class AuthenticationError(AdapterError):
    """认证失败"""
    pass

class RateLimitError(AdapterError):
    """频率限制"""
    def __init__(self, retry_after: int | None = None): ...

class CapabilityNotSupported(AdapterError):
    """调用不支持的能力"""
    pass

class AccountPoolError(SuperHubError):
    """账号池错误"""
    pass

class NoAvailableAccountError(AccountPoolError):
    """无可用账号"""
    pass

class CircuitOpenError(SuperHubError):
    """熔断器打开"""
    pass
```

### 命名约定

- 模块名：snake_case
- 类名：PascalCase
- 常量：UPPER_SNAKE_CASE
- 私有方法：_leading_underscore
- 数据库表名：snake_case，复数形式（unified_posts）
- API 路径：kebab-case（/api/v1/task-templates）

### 提交规范

```
feat: 新功能
fix: 修复
refactor: 重构
test: 测试
docs: 文档
chore: 构建/工具链
```

## 开发优先级

按以下顺序实现，每个阶段的产出必须是可运行的：

### Phase 1 — MVP（当前阶段）

目标：跑通 B站平台的完整采集链路

1. 定义 BaseAdapter 接口和所有统一数据模型
2. 实现 BilibiliAdapter（视频信息 + 评论 + 媒体下载）
3. 实现 MongoDB 原始存储 + PostgreSQL 标准存储
4. 实现 AccountPoolService 简化版（三个状态：active / cooldown / banned）
5. 配置 Celery 任务，手动触发采集
6. 基础单元测试 + Mock 测试

### Phase 2 — 调度与容错

7. 完善 Celery 定时任务和任务依赖
8. 实现代理池管理
9. 实现熔断器和差异化重试策略
10. 添加 Prometheus 指标和结构化日志

### Phase 3 — 扩展平台

11. 接入第二个平台（Telegram），验证跨平台能力
12. 批量接入剩余平台
13. 完善 capabilities 机制

### Phase 4 — 前端与运维

14. React Web UI 管理后台
15. Docker 化部署
16. 监控面板（Grafana）

## 关键约束

- **不要过早抽象**：在只有 1-2 个适配器时，不要过度设计通用层。等第三个适配器出现时再提取共性。
- **Mock 测试优先**：每个适配器必须提供 fixtures/ 目录，存放真实的 API 响应样本（脱敏后），用于离线测试。
- **配置驱动**：所有阈值（重试次数、熔断阈值、限流速率、冷却时间）必须是可配置的，不要硬编码。
- **渐进式复杂度**：第一版账号池只需三状态，不要实现温度分层和养号逻辑。等运行数据积累后再优化。
- **日志即监控**：每条日志必须包含 platform、task_id、account_id，便于追踪和聚合分析。
```

---

这份提示词覆盖了架构、接口、数据模型、容错、命名、目录结构和实施优先级。可以直接粘贴到 Cursor 的 `.cursorrules` 或 Claude 的 Project Knowledge 中使用。

需要我调整什么地方吗？比如针对某个特定的 AI 编程工具做格式适配，或者增减某些模块的细节。