# SuperNova — 统一社交数据采集平台

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/types-mypy-blue.svg)](http://mypy-lang.org/)

**企业级多平台社交数据采集系统** — 通过统一的接口管理多个社交平台的数据采集任务，具备动态降级、精细调度、灰度发布和资源隔离能力。

---

## 🌟 核心特性

| 特性 | 说明 | 状态 |
|------|------|------|
| 🔄 **插件化适配器** | 统一接口设计，轻松接入新平台（B 站/抖音/微博/Instagram/Telegram） | ✅ |
| 📊 **三层存储架构** | MongoDB（原始数据）+ PostgreSQL（标准化）+ Elasticsearch（检索） | 🚧 |
| 🛡️ **企业级容错** | 熔断器、差异化重试、账号池管理、代理池评分 | 🚧 |
| 🎛️ **动态功能开关** | 四层控制（全局/平台/功能/策略），支持热更新无需重启 | ✅ |
| 🔐 **RBAC 权限控制** | 精细化权限控制，仅运维可操作熔断等关键功能 | 📋 |
| 🧪 **AB 测试框架** | 基于灰度开关的实验分组，支持流量比例控制 | 📋 |
| 🤖 **智能预测** | ML 模型预测最佳恢复时间，自动优化调度策略 | 📋 |
| 🌍 **多环境同步** | 开发/测试/生产环境配置一致性管理 | 📋 |
| 📈 **可观测性** | Prometheus 指标 + Grafana 仪表板 + structlog 结构化日志 | 🚧 |
| 🚀 **异步高并发** | asyncio + uvloop + Celery 分布式任务队列 | ✅ |

**图例**: ✅ 已实现  |  🚧 开发中  |  📋 计划中

---

## 🏗️ 五层架构

```
┌─────────────────────────────────────────────────────────────┐
│  用户交互层：FastAPI REST API + React Web UI + CLI          │
├─────────────────────────────────────────────────────────────┤
│  任务调度层：Celery + Redis (Airflow 按需启用)              │
├─────────────────────────────────────────────────────────────┤
│  适配器层：Bilibili/Douyin/Weibo/Instagram/Telegram...      │
├─────────────────────────────────────────────────────────────┤
│  基础设施层：代理池 | 账号池 | 熔断器 | 限流器 | FeatureFlags│
├─────────────────────────────────────────────────────────────┤
│  数据存储层：MongoDB + PostgreSQL + Elasticsearch + OSS/S3  │
└─────────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI + Python 3.11+ |
| 异步运行时 | asyncio + uvloop |
| 任务队列 | Celery + Redis |
| HTTP 客户端 | curl_cffi（TLS 指纹）/ httpx |
| 数据库 | MongoDB (Motor) + PostgreSQL (SQLAlchemy 2.0 async + asyncpg) |
| 搜索引擎 | Elasticsearch |
| 对象存储 | MinIO / 阿里云 OSS |
| 监控 | Prometheus + Grafana |
| 日志 | structlog |
| 容器化 | Docker + docker-compose |
| 前端 | React + TypeScript + Ant Design |
| 测试 | pytest + pytest-asyncio + respx |
| 代码质量 | ruff + mypy + pre-commit |

---

## 📁 项目结构

```
SuperNova/
├── backend/
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # 配置管理（Pydantic Settings）
│   ├── api/
│   │   ├── v1/
│   │   │   ├── tasks.py            # 任务 CRUD API
│   │   │   ├── platforms.py        # 平台管理 API
│   │   │   ├── accounts.py         # 账号池 API
│   │   │   ├── feature_flags.py    # 功能开关 API ⭐新增
│   │   │   ├── data.py             # 数据查询 API
│   │   │   └── health.py           # 健康检查
│   │   └── deps.py                 # 依赖注入
│   ├── adapters/
│   │   ├── base.py                 # BaseAdapter + 统一数据模型
│   │   ├── registry.py             # 适配器注册表
│   │   ├── bilibili/               # B 站适配器（含直播弹幕）
│   │   ├── douyin/
│   │   ├── weibo/
│   │   └── telegram/
│   ├── scheduler/
│   │   ├── celery_app.py           # Celery 实例配置
│   │   ├── tasks.py                # 通用任务定义
│   │   ├── beats.py                # 定时任务配置
│   │   └── retry.py                # 重试策略
│   ├── infrastructure/
│   │   ├── proxy_pool/             # 代理池管理
│   │   ├── account_pool/           # 账号池服务
│   │   ├── circuit_breaker.py      # 熔断器
│   │   ├── rate_limiter.py         # 限流器
│   │   └── feature_flags.py        # 功能开关控制 ⭐新增
│   ├── models/
│   │   ├── mongo/                  # MongoDB 文档模型
│   │   ├── pg/                     # PostgreSQL ORM 模型
│   │   └── es/                     # ES 索引映射
│   ├── services/
│   │   ├── task_service.py         # 任务业务逻辑
│   │   ├── data_service.py         # 数据查询 & 导出
│   │   ├── monitoring.py           # Prometheus 指标
│   │   ├── alerting.py             # 告警服务 ⭐新增
│   │   └── feature_flag.py         # FeatureFlag 服务 ⭐新增
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
│   │   │   ├── DataViewer.tsx
│   │   │   └── FeatureFlags.tsx    # 功能开关管理页面 ⭐新增
│   │   ├── components/
│   │   └── services/
│   │       └── api.ts              # 后端 API 调用
│   ├── package.json
│   └── vite.config.ts
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.celery
│   ├── docker-compose.yml
│   ├── prometheus.yml              # Prometheus 配置
│   └── grafana/dashboards/         # Grafana 仪表板
│       └── feature_flags.json      # 功能开关监控 ⭐新增
├── alembic/                        # 数据库迁移
│   ├── env.py
│   └── versions/
├── docs/
│   ├── architecture/               # 架构文档
│   ├── platforms/                  # 平台接入文档
│   └── operations/                 # 运维指南
├── scripts/
│   ├── init_db.py                  # 数据库初始化
│   ├── seed_accounts.py            # 测试账号种子
│   └── init_feature_flags.py       # 功能开关初始化 ⭐新增
├── tests/
│   ├── conftest.py
│   ├── integration/
│   └── e2e/
├── .cursorrules                    # AI 助手配置
├── .pre-commit-config.yaml         # Pre-commit hooks
├── pyproject.toml                  # 项目配置
└── README.md
```

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

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Docker & docker-compose
- Redis, PostgreSQL, MongoDB, Elasticsearch（可通过 docker-compose 一键启动）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/iiooiioo888/SuperNova.git
cd SuperNova

# 2. 安装依赖
poetry install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入数据库密码、API Key 等

# 4. 启动基础设施（Docker 配置开发中）
# docker-compose up -d postgres mongodb redis elasticsearch
# 目前请手动启动所需服务或使用 scripts/init_db.py 初始化

# 5. 初始化数据库
python scripts/init_db.py

# 6. 初始化功能开关（可选）
python scripts/init_feature_flags.py

# 7. 启动后端服务
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 8. 启动 Celery Worker
celery -A backend.scheduler.celery_app worker --loglevel=info

# 9. 启动前端（开发模式）
cd frontend && npm install && npm run dev
```

### 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| FastAPI Backend | http://localhost:8000 | API 服务，自带 Swagger UI (/docs) |
| React Frontend | http://localhost:3000 | 管理后台 |
| Grafana | http://localhost:3001 | 监控仪表板 (admin/admin) |
| Prometheus | http://localhost:9090 | 指标查询 |

---

## 📚 文档导航

| 文档类型 | 路径 | 说明 |
|----------|------|------|
| 架构决策记录 | `docs/architecture/decisions/` | ADR 文档，记录关键技术决策 |
| 平台接入指南 | `docs/platforms/` | 各平台 API 特性、反爬策略、实现进度 |
| 运维手册 | `docs/operations/` | 部署、监控、故障排查指南 |
| API 文档 | http://localhost:8000/docs | FastAPI 自动生成的 OpenAPI 文档 |

---

## 🧪 测试

```bash
# 运行单元测试
pytest tests/ -v

# 运行集成测试（需要真实 API 凭证）
pytest tests/integration/ -v -m integration

# 生成覆盖率报告
pytest --cov=backend --cov-report=html

# 代码质量检查
ruff check backend/
mypy backend/
```

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

**提交规范**: 遵循 Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`)

---

## 📄 许可证

MIT License

---

## 📊 实现状态总览

| 模块 | 进度 | 说明 |
|------|------|------|
| **适配器层** | 10% | Bilibili 已完成，其他平台待接入 |
| **功能开关** | 85% | 核心服务/API/前端已完成，ML 预测待实现 |
| **账号池** | 70% | 基础状态机完成，权重算法待优化 |
| **存储层** | 60% | PostgreSQL 模型/UPSERT/批量写入/ES 同步完成，MongoDB 待实现 |
| **任务调度** | 30% | Celery 基础配置完成，定时任务待完善 |
| **监控告警** | 20% | 结构化日志完成，Prometheus/Grafana 待实现 |
| **前端 UI** | 25% | FeatureFlags/DataViewer/Login 页面完成，其他管理页面待开发 |

---

## ✅ 已完成工作清单

### 1. 🗄️ 存储层核心实现 (Storage Layer)

**backend/storage/standard_store.py:**
- ✅ 实现 UPSERT 逻辑 (INSERT ... ON CONFLICT DO UPDATE)，确保数据幂等性
- ✅ 批量写入优化 (bulk_insert_posts)，减少数据库交互次数
- ✅ 自动处理 UnifiedPost, UnifiedProfile, UnifiedComment 的标准化写入

**backend/storage/index_sync.py:**
- ✅ 实现 Outbox 模式的异步同步逻辑，将 PG 数据同步至 Elasticsearch
- ✅ 定义 ES 索引映射 (create_index_mappings)，支持全文检索和聚合分析
- ✅ 增加重试机制，防止网络波动导致数据丢失

### 2. 📡 Bilibili 适配器核心逻辑 (Adapter Core)

**backend/adapters/bilibili/adapter.py:**
- ✅ 真实 HTTP 请求：集成 curl_cffi 模拟 TLS 指纹，绕过基础风控
- ✅ WBI 签名：实现 B 站特有的 WBI 签名算法 (get_wbi_sign)，确保 API 调用合法
- ✅ 数据解析：对接 parser.py，将原始 JSON 转换为 UnifiedPost/Profile 模型
- ✅ 媒体下载：支持流式下载视频封面和截图至 MinIO/S3
- ✅ 错误处理：捕获特定错误码 (如 -403, -412) 并映射为 RateLimitError 或 AuthenticationError

**backend/adapters/bilibili/parser.py:**
- ✅ 完善视频列表、详情、评论的解析逻辑
- ✅ 处理嵌套 JSON 结构和缺失字段默认值

### 3. 🎨 前端联调与完善 (Frontend Integration)

**frontend/src/services/api.ts:**
- ✅ 封装 Axios 拦截器，自动处理 JWT Token 的附加与刷新
- ✅ 统一错误处理 (401 跳转登录，403 提示权限不足)

**frontend/src/pages/Login.tsx:**
- ✅ 实现登录表单，对接 /api/v1/auth/login，存储 Token 到 localStorage

**frontend/src/pages/FeatureFlags.tsx (更新):**
- ✅ 增加 RBAC 控制：非 Admin/Operator 角色隐藏"编辑"按钮
- ✅ 增加 加载状态 和 操作反馈 (Toast 通知)
- ✅ 对接真实的 GET /api/v1/feature-flags 和 POST /api/v1/feature-flags/{id}/toggle 接口

**frontend/src/pages/DataViewer.tsx:**
- ✅ 新增页面：展示从 ES 查询到的标准化数据列表，支持分页和简单筛选

### 4. 🔧 配置与脚本

- ✅ **scripts/init_es.py**: 初始化 ES 索引映射脚本
- ✅ **scripts/create_admin.py**: 创建初始管理员账号脚本
- ✅ **.env**: 补充 MINIO_ENDPOINT, ES_URL, JWT_SECRET 等必要变量

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryq.dev/)
- [curl_cffi](https://github.com/yifeikong/curl_cffi)
- [structlog](https://www.structlog.org/)

---

**SuperNova** — 让社交数据采集更简单、更可靠、更智能 🚀