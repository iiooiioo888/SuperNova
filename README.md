# SuperHub — 统一社交数据采集平台

多平台社交数据采集系统，通过统一的接口管理多个社交平台的数据采集任务。

## 特性

- 🔄 插件化适配器设计，轻松接入新平台
- 📊 三层存储架构：原始数据 + 标准化数据 + 搜索索引
- 🛡️ 完善的容错机制：熔断器、重试策略、账号池管理
- 🚀 异步架构，高并发支持
- 📈 Prometheus + Grafana 监控

## 快速开始

```bash
# 安装依赖
poetry install

# 启动服务
docker-compose up -d

# 运行测试
pytest
```

## 项目结构

```
SuperHub/
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
├── docker/           # Docker 配置
├── scripts/          # 工具脚本
└── tests/            # 测试用例
```

## 已支持平台

- [x] Bilibili (Phase 1)
- [ ] Telegram (Phase 3)
- [ ] 更多平台...

## License

MIT
