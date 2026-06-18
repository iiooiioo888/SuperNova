# ADR 001: 选择 Celery 而非 Airflow 作为任务调度器

**日期**: 2024-01-15  
**状态**: 已接受  
**决策者**: SuperHub Team

## 背景

SuperHub 需要处理以下类型的任务：

1. **短期采集任务**: 获取单个用户资料、帖子列表、评论等，通常在几秒到几分钟内完成
2. **周期性任务**: 定期更新已采集用户的数据
3. **任务依赖**: 某些任务需要在其他任务完成后执行（如先采集帖子再采集评论）
4. **高并发**: 需要同时运行数十到数百个采集任务

我们评估了两个主要选项：Celery 和 Airflow。

## 决策

**选择 Celery + Redis 作为默认任务队列**，Airflow 作为可选的高级调度器按需启用。

### 具体方案

- **Broker & Backend**: Redis（同时用于 Celery broker 和 result backend）
- **Worker 管理**: Celery worker 多进程并发
- **定时任务**: Celery Beat
- **任务编排**: Celery chain/chord/group  primitives
- **监控**: Flower（可选）+ Prometheus 指标

## 结果

### 正面影响

1. **轻量级部署**: Celery + Redis 比 Airflow 更简单，资源占用更少
2. **低延迟**: 适合秒级/分钟级的短期任务，任务提交后几乎立即执行
3. **异步友好**: 与 FastAPI 的 asyncio 架构天然契合
4. **渐进式扩展**: 可以从单机 Redis 扩展到 Redis Cluster，无需重构
5. **开发体验**: Celery 的任务定义更简洁，学习曲线更低

### 负面影响

1. **复杂工作流支持弱**: Airflow 的 DAG 可视化和管理更强大
2. **任务历史查询**: 需要自行实现任务历史记录（Celery 默认不持久化）
3. **动态 DAG**: 对于复杂的条件分支逻辑，不如 Airflow 直观

### 缓解措施

- 对于需要复杂调度的场景，保留 Airflow 集成能力
- 使用 PostgreSQL 存储任务元数据，弥补 Celery 结果存储的不足
- 通过 Prometheus + Grafana 实现任务监控面板

## 参考

- [Celery 官方文档](https://docs.celeryq.dev/)
- [Airflow 官方文档](https://airflow.apache.org/docs/)
