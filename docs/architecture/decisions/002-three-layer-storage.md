# ADR 002: 三层存储架构设计

**日期**: 2024-01-15  
**状态**: 已接受  
**决策者**: SuperHub Team

## 背景

社交数据采集系统面临以下存储挑战：

1. **数据结构差异大**: 不同平台的 API 响应格式完全不同，且经常变更
2. **数据量大**: 帖子、评论等数据可能达到千万级
3. **查询需求多样**: 需要支持按用户、时间、关键词等多种维度查询
4. **原始数据保留**: 需要保留原始响应以便后续重新解析或审计
5. **媒体文件存储**: 图片、视频等二进制文件需要专门的存储方案

## 决策

**采用三层存储架构**：

| 层级 | 存储引擎 | 内容 | 写入时机 | 保留策略 |
|---|---|---|---|---|
| Raw 层 | MongoDB | 平台原始 JSON 响应 | 采集时立即写入 | 永久保留所有版本 |
| Standard 层 | PostgreSQL | 统一模型结构化字段 | 适配器标准化后写入 | UPSERT 去重，只保留最新版本 |
| Analytics 层 | Elasticsearch | 聚合索引 | Standard 层写入后异步同步 | 用于搜索和分析，可按需重建 |

### 媒体文件存储

- **对象存储**: MinIO（自建）或阿里云 OSS / AWS S3
- **文件路径**: `{platform}/{media_type}/{date}/{media_id}.{ext}`
- **元数据**: 存储在 PostgreSQL 的 `unified_posts.media` JSONB 字段中

## 结果

### 正面影响

1. **灵活性**: Raw 层允许在适配器逻辑变更后重新解析历史数据
2. **性能**: PostgreSQL 适合结构化查询，ES 适合全文搜索和聚合分析
3. **可靠性**: 原始数据先落库再做标准化，防止标准化失败导致数据丢失
4. **可扩展**: 每层可以独立扩展（如 ES 集群、MongoDB 分片）
5. **成本优化**: 冷数据可以归档到低成本存储（如 S3 Glacier）

### 负面影响

1. **数据一致性**: 三层之间可能存在短暂延迟（通过异步同步缓解）
2. **运维复杂度**: 需要维护三种数据库 + 对象存储
3. **开发成本**: 需要编写三层之间的数据同步逻辑

### 缓解措施

- 使用事务确保 Standard 层的原子性
- 通过事件驱动架构实现异步同步（Celery 任务）
- 提供数据修复工具，处理同步失败的情况
- Docker Compose 一键部署所有存储服务

## 数据库 Schema 设计原则

### PostgreSQL（Standard 层）

- 使用 `BIGSERIAL` 主键
- `(platform, platform_post_id)` 唯一约束
- JSONB 字段存储动态结构（media、metrics）
- 时间戳字段使用 `TIMESTAMPTZ`
- 索引覆盖常用查询模式

### MongoDB（Raw 层）

- 集合命名：`raw_{platform}_{entity_type}`（如 `raw_bilibili_posts`）
- 文档结构：`{metadata: {...}, raw_response: {...}, ingested_at: ISODate()}`
- TTL 索引（可选）：自动清理过期数据

### Elasticsearch（Analytics 层）

- 索引命名：`analytics-{entity_type}-{yyyy.mm}`（按月分索引）
- 映射定义：明确字段类型，避免动态映射导致的类型冲突
- 刷新间隔：生产环境调整为 30s 以上，减少 segment 数量

## 参考

- [MongoDB Schema Design](https://www.mongodb.com/docs/manual/applications/data-models/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [Elasticsearch Index Design](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
