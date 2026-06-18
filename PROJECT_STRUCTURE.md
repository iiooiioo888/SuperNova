# SuperHub 项目结构说明

本文档说明项目的目录结构和关键文件。

## 目录树

```
SuperHub/
├── backend/                      # 后端代码
│   ├── main.py                   # FastAPI 应用入口
│   ├── config.py                 # 配置管理（Pydantic Settings）
│   ├── exceptions.py             # 异常体系定义
│   ├── api/v1/                   # REST API v1 版本
│   │   ├── tasks.py              # 任务管理 API
│   │   ├── platforms.py          # 平台管理 API
│   │   ├── accounts.py           # 账号池 API
│   │   ├── data.py               # 数据查询 API
│   │   ├── health.py             # 健康检查 API
│   │   └── deps.py               # 依赖注入
│   ├── adapters/                 # 适配器层
│   │   ├── base.py               # BaseAdapter + 统一数据模型
│   │   ├── registry.py           # 适配器注册表
│   │   ├── exceptions.py         # 适配器异常
│   │   └── {platform}/           # 各平台适配器
│   │       ├── adapter.py        # 适配器实现
│   │       ├── parser.py         # 响应解析
│   │       ├── constants.py      # 常量定义
│   │       └── tests/            # 测试代码
│   │           └── fixtures/     # Mock 数据样本
│   ├── scheduler/                # 任务调度
│   │   ├── celery_app.py         # Celery 配置
│   │   ├── tasks.py              # Celery 任务定义
│   │   ├── beats.py              # 定时任务配置
│   │   └── retry.py              # 重试策略
│   ├── infrastructure/           # 基础设施层
│   │   ├── account_pool/         # 账号池服务
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   └── state_machine.py
│   │   ├── proxy_pool/           # 代理池服务
│   │   │   ├── service.py
│   │   │   ├── providers/        # 代理供应商
│   │   │   └── scorer.py         # 代理评分
│   │   ├── circuit_breaker.py    # 熔断器
│   │   └── rate_limiter.py       # 限流器
│   ├── models/                   # 数据模型
│   │   ├── pg/                   # PostgreSQL ORM 模型
│   │   ├── mongo/                # MongoDB 文档模型
│   │   └── es/                   # Elasticsearch 映射
│   ├── services/                 # 业务逻辑层
│   │   ├── task_service.py       # 任务服务
│   │   ├── data_service.py       # 数据服务
│   │   └── monitoring.py         # 监控服务
│   ├── storage/                  # 存储层
│   │   ├── raw_store.py          # MongoDB 原始存储
│   │   ├── standard_store.py     # PostgreSQL 标准存储
│   │   ├── media_store.py        # 对象存储
│   │   └── index_sync.py         # ES 索引同步
│   └── utils/                    # 工具函数
│       ├── logging.py            # structlog 配置
│       ├── fingerprint.py        # HTTP 指纹工具
│       └── helpers.py            # 辅助函数
├── frontend/                     # 前端代码
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/                # 页面组件
│   │   ├── components/           # 通用组件
│   │   └── services/             # API 调用封装
│   ├── package.json
│   └── vite.config.ts
├── docker/                       # Docker 配置
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.celery
│   └── docker-compose.yml
├── docs/                         # 文档
│   ├── architecture/             # 架构文档
│   │   ├── README.md
│   │   └── decisions/            # ADR 文档
│   │       ├── 001-celery-over-airflow.md
│   │       ├── 002-three-layer-storage.md
│   │       └── 003-account-lease-model.md
│   ├── platforms/                # 平台接入文档
│   │   └── bilibili.md
│   ├── operations/               # 运维文档
│   │   └── deployment.md
│   └── api/                      # API 文档
├── alembic/                      # 数据库迁移
│   ├── env.py
│   ├── script.py.mako
│   ├── versions/                 # 迁移脚本
│   └── README.md
├── scripts/                      # 工具脚本
│   ├── init_db.py                # 数据库初始化
│   └── seed_accounts.py          # 种子账号脚本
├── tests/                        # 测试
│   ├── conftest.py               # 共享 fixtures
│   ├── integration/              # 集成测试
│   └── e2e/                      # 端到端测试
├── .cursorrules                  # Cursor AI 助手配置
├── .pre-commit-config.yaml       # Pre-commit hooks
├── .env.example                  # 环境变量示例
├── pyproject.toml                # Python 项目配置
├── alembic.ini                   # Alembic 配置
└── README.md                     # 项目说明
```

## 关键文件说明

### 配置文件

| 文件 | 用途 |
|---|---|
| `pyproject.toml` | Python 依赖和工具配置（Poetry） |
| `.env.example` | 环境变量模板 |
| `alembic.ini` | 数据库迁移工具配置 |
| `.pre-commit-config.yaml` | Git pre-commit hooks |
| `.cursorrules` | Cursor AI 助手项目指南 |

### 核心模块

| 模块 | 说明 |
|---|---|
| `backend/adapters/base.py` | 适配器基类和统一数据模型 |
| `backend/adapters/registry.py` | 适配器注册和发现机制 |
| `backend/exceptions.py` | 全局异常体系 |
| `backend/config.py` | 配置管理（支持环境变量） |
| `backend/scheduler/celery_app.py` | Celery 任务队列配置 |

### 文档

| 文档 | 内容 |
|---|---|
| `docs/architecture/decisions/` | 架构决策记录（ADR） |
| `docs/platforms/` | 各平台接入详细文档 |
| `docs/operations/deployment.md` | 部署指南 |

## 开发约定

### 命名规范

- **Python 模块**: snake_case（如 `account_pool.py`）
- **类名**: PascalCase（如 `BilibiliAdapter`）
- **常量**: UPPER_SNAKE_CASE（如 `MAX_RETRY_COUNT`）
- **API 路径**: kebab-case（如 `/api/v1/task-templates`）
- **数据库表**: snake_case 复数（如 `unified_posts`）

### 测试组织

- **单元测试**: 放在对应模块的 `tests/` 子目录
- **集成测试**: `tests/integration/`，标记为 `@pytest.mark.integration`
- **端到端测试**: `tests/e2e/`，标记为 `@pytest.mark.e2e`
- **Fixtures**: 每个适配器的 `tests/fixtures/` 目录存放 Mock 数据

### Git 工作流

```
main          ← 生产分支（保护）
  └── develop ← 开发分支
       └── feature branches
```

提交信息遵循 Conventional Commits：
```
feat: 新功能
fix: 修复
refactor: 重构
test: 测试
docs: 文档
chore: 构建/工具链
```

## 快速开始

```bash
# 1. 安装依赖
poetry install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际配置

# 3. 初始化数据库
python -m scripts.init_db

# 4. 启动开发服务器
uvicorn backend.main:app --reload

# 5. 运行测试
pytest
```

## 参考

- [完整系统提示词](readme.md)
- [部署指南](docs/operations/deployment.md)
- [架构决策](docs/architecture/README.md)
