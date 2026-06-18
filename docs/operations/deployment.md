# SuperHub 部署指南

## 前置要求

### 硬件要求

- **最小配置**: 2 vCPU, 4GB RAM, 20GB 存储
- **推荐配置**: 4 vCPU, 8GB RAM, 50GB+ 存储（取决于数据量）

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+（本地开发）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/superhub.git
cd superhub
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的变量
```

### 3. 启动服务

```bash
# 启动所有服务（后端、前端、数据库、消息队列等）
docker-compose -f docker/docker-compose.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f
```

### 4. 初始化数据库

```bash
# 等待 PostgreSQL 和 MongoDB 启动后执行
docker-compose -f docker/docker-compose.yml exec backend python -m scripts.init_db
```

### 5. 验证部署

访问以下地址：

- **API 文档**: http://localhost:8000/docs
- **前端界面**: http://localhost:3000
- **Grafana 监控**: http://localhost:3001（默认账号 admin/admin）
- **Prometheus**: http://localhost:9090

## 配置文件说明

### .env 文件

```bash
# ============ 数据库配置 ============
PG_PASSWORD=your_secure_password_here
MONGODB_URI=mongodb://mongodb:27017/superhub
REDIS_PASSWORD=your_redis_password_here
ELASTICSEARCH_URL=http://elasticsearch:9200

# ============ MinIO 对象存储 ============
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=minio:9000

# ============ Celery 配置 ============
CELERY_BROKER_URL=redis://:your_redis_password_here@redis:6379/0
CELERY_RESULT_BACKEND=redis://:your_redis_password_here@redis:6379/0

# ============ Grafana 配置 ============
GRAFANA_PASSWORD=your_grafana_password_here

# ============ 应用配置 ============
SECRET_KEY=your_secret_key_for_jwt
LOG_LEVEL=INFO
```

## 服务组件

| 服务 | 端口 | 说明 |
|---|---|---|
| backend | 8000 | FastAPI 后端 |
| frontend | 3000 | React 前端 |
| celery-worker | - | Celery 工作节点（2 副本） |
| celery-beat | - | Celery 定时任务调度器 |
| postgres | 5432 | PostgreSQL 数据库 |
| mongodb | 27017 | MongoDB 数据库 |
| redis | 6379 | Redis 消息队列 |
| elasticsearch | 9200 | Elasticsearch 搜索引擎 |
| prometheus | 9090 | Prometheus 监控 |
| grafana | 3001 | Grafana 可视化 |

## 生产环境部署

### 安全加固

1. **修改默认密码**: 所有服务的默认密码必须更改
2. **启用 SSL**: 
   ```bash
   # 使用 Let's Encrypt 或自有证书
   ```
3. **网络隔离**: 
   - 数据库不暴露到公网
   - 使用 Docker network 隔离服务
4. **Secrets 管理**: 
   - 使用 Docker Secrets 或外部 Vault
   - 不要将敏感信息写入 .env 文件

### 性能优化

1. **Celery Worker 扩展**:
   ```yaml
   deploy:
     replicas: 4  # 根据负载调整
   ```

2. **数据库连接池**:
   ```python
   # config.py
   DATABASE_POOL_SIZE = 20
   DATABASE_MAX_OVERFLOW = 10
   ```

3. **Elasticsearch 调优**:
   ```yaml
   environment:
     - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
   ```

### 备份策略

```bash
# PostgreSQL 备份
docker-compose exec postgres pg_dump -U superhub superhub > backup_$(date +%Y%m%d).sql

# MongoDB 备份
docker-compose exec mongodb mongodump --out /backup/mongodb_$(date +%Y%m%d)

# 定期清理旧备份（保留 7 天）
find /backup -name "*.sql" -mtime +7 -delete
```

## 故障排查

### 常见问题

#### 1. Celery Worker 无法连接 Redis

```bash
# 检查 Redis 是否运行
docker-compose ps redis

# 查看 Redis 日志
docker-compose logs redis

# 验证密码配置
docker-compose exec redis redis-cli -a your_password ping
```

#### 2. 数据库迁移失败

```bash
# 查看 Alembic 版本
docker-compose exec backend alembic current

# 手动升级
docker-compose exec backend alembic upgrade head

# 回滚到上一个版本
docker-compose exec backend alembic downgrade -1
```

#### 3. Elasticsearch 索引失败

```bash
# 检查 ES 健康状态
curl http://localhost:9200/_cluster/health?pretty

# 查看索引列表
curl http://localhost:9200/_cat/indices?v
```

### 日志收集

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend celery-worker

# 导出日志到文件
docker-compose logs backend > backend_logs.txt
```

## 升级指南

### 版本升级

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 停止服务
docker-compose down

# 3. 重新构建镜像
docker-compose build

# 4. 执行数据库迁移
docker-compose run --rm backend alembic upgrade head

# 5. 重启服务
docker-compose up -d
```

### 回滚

```bash
# 1. 回滚数据库迁移
docker-compose run --rm backend alembic downgrade -1

# 2. 切换到旧版本代码
git checkout <previous-tag>

# 3. 重新部署
docker-compose build
docker-compose up -d
```

## 监控与告警

### Prometheus 指标

关键指标：

- `celery_tasks_total`: 任务总数
- `celery_task_runtime_seconds`: 任务执行时间
- `adapter_requests_total`: 适配器请求数
- `adapter_errors_total`: 适配器错误数
- `account_pool_active_accounts`: 活跃账号数

### Grafana 仪表盘

预置仪表盘：

1. **系统概览**: CPU、内存、磁盘使用率
2. **任务监控**: 任务成功率、平均执行时间、队列长度
3. **平台监控**: 各平台采集成功率、错误分布
4. **账号池监控**: 各平台可用账号数、封禁率

### 告警规则

```yaml
# prometheus/alerts.yml
groups:
  - name: superhub
    rules:
      - alert: HighTaskFailureRate
        expr: rate(celery_task_failures_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "任务失败率过高"
          
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state == 1
        for: 1m
        annotations:
          summary: "熔断器打开"
```

## 参考资料

- [Docker 官方文档](https://docs.docker.com/)
- [Celery 部署指南](https://docs.celeryq.dev/en/stable/userguide/deployment.html)
- [Prometheus 最佳实践](https://prometheus.io/docs/practices/)
