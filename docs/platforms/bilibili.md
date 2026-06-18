# Bilibili 平台接入文档

## 基本信息

- **平台官网**: https://www.bilibili.com
- **API 类型**: REST + WebSocket（弹幕）
- **认证方式**: Cookie / WBI 签名

## 已实现功能

| 功能 | 状态 | 备注 |
|---|---|---|
| fetch_user_profile | ✅ | 获取 UP 主资料 |
| fetch_posts | ✅ | 获取视频列表，分页使用页码 |
| fetch_comments | ✅ | 获取评论，支持楼中楼 |
| download_media | ✅ | 下载视频封面和预览图 |
| search | ⚠️ | 仅支持关键词搜索，无高级筛选 |

## 特有能力 (capabilities)

| 名称 | 描述 |
|---|---|
| fetch_video_info | 获取单个视频详细信息（时长、分辨率等） |
| fetch_danmaku | 获取视频弹幕（XML 格式） |
| fetch_user_relation | 获取关注/粉丝列表 |

## API 端点

### 用户信息

```
GET https://api.bilibili.com/x/space/acc/info
参数：mid={user_id}
```

### 视频列表

```
GET https://api.bilibili.com/x/space/wbi/arc/search
参数：
  - mid: 用户 ID
  - pn: 页码（从 1 开始）
  - ps: 每页数量（最大 30）
```

### 视频详情

```
GET https://api.bilibili.com/x/web-interface/view
参数：bvid={BV 号} 或 aid={AV 号}
```

### 评论列表

```
GET https://api.bilibili.com/x/v2/reply/wbi/main
参数：
  - oid: 视频 AV 号
  - type: 1（视频评论）
  - sort: 排序方式（0: 默认，1: 按赞，2: 按时间）
  - ps: 每页数量
  - pn: 页码
```

## 反爬策略

### WBI 签名

B 站使用 WBI 签名验证请求合法性：

1. 从 `https://api.bilibili.com/x/web-interface/nav` 获取 `img_key` 和 `sub_key`
2. 拼接参数并排序
3. 使用 key 生成签名

参考实现：[SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/misc/sign/wbi.md)

### TLS 指纹检测

- 使用 `curl_cffi` 模拟 Chrome 浏览器的 TLS 指纹
- 设置正确的 User-Agent 和 Referer

### 频率限制

- 未登录：约 20 请求/分钟
- 已登录：约 60 请求/分钟（取决于账号权重）
- 超过限制返回 HTTP 412

### Cookie 有效期

- Cookie 有效期约 7 天
- 需要定期刷新或重新登录

### 已知封禁触发条件

1. 短时间内大量请求同一接口
2. 使用过期的 WBI 签名
3. TLS 指纹不匹配
4. 缺少必要的 Header（如 Referer）

## 数据解析要点

### 视频 ID 处理

- B 站有两种视频 ID 格式：AV 号（数字）和 BV 号（字母数字混合）
- API 响应通常返回 BV 号，需要时可互相转换
- 建议使用 BV 号作为 `platform_post_id`

### 时间格式

- API 返回 Unix 时间戳（秒）
- 转换为 UTC datetime 存储

### 富文本处理

- 视频简介可能包含 emoji、@提及、话题标签
- 需要解析 `<emoticon>` 标签提取 emoji
- 使用正则提取 `@{username}` 和 `#{topic}#`

## 已知问题

1. **WBI key 缓存失效**: WBI key 会不定期更新，需要实现自动刷新机制
2. **部分视频地区限制**: 某些视频仅限中国大陆观看，海外服务器无法获取
3. **弹幕需要单独请求**: 弹幕不在评论 API 中返回，需要通过 WebSocket 或 XML 接口获取
4. **番剧/电影需要大会员**: 付费内容需要特殊权限

## 测试样本

 fixtures 目录包含以下脱敏样本：

- `fixtures/user_profile.json`: 用户资料响应
- `fixtures/user_posts_page1.json`: 视频列表第一页
- `fixtures/video_info.json`: 视频详情
- `fixtures/comments.json`: 评论列表

## 参考资料

- [bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect): 最全面的 B 站 API 文档
- [bilibili-api-python](https://github.com/Nemo2011/bilibili-api): Python SDK 参考
