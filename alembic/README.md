# Alembic Migrations

本目录包含 PostgreSQL 数据库的迁移脚本。

## 使用方法

### 创建新迁移

```bash
# 自动检测模型变更生成迁移
alembic revision --autogenerate -m "描述变更内容"

# 手动创建空迁移
alembic revision -m "添加新表"
```

### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade <revision_id>

# 回滚一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade <revision_id>
```

### 查看状态

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看待应用的迁移
alembic heads
```

## 最佳实践

1. **每次迁移只做一件事**: 不要在一个迁移中同时创建多个表
2. **测试 downgrade**: 确保每个迁移都可以安全回滚
3. **大表变更谨慎**: 对于千万级数据的表，使用 `CREATE INDEX CONCURRENTLY`
4. **数据迁移分开**: 结构变更和数据迁移分开成不同的脚本
5. **代码审查**: 所有迁移脚本必须经过审查才能合并

## 故障排查

### 迁移失败

```bash
# 查看当前版本
alembic current

# 如果是部分失败的迁移，可能需要手动修复后标记
alembic stamp <revision_id>
```

### 模型不同步

```bash
# 重新生成迁移（注意审查差异）
alembic revision --autogenerate -m "sync models"
```

## 参考

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 异步 ORM](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
