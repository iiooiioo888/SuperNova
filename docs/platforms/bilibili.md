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
| fetch_live_stream | 🔄 | 获取直播信息（待实现） |
| fetch_danmaku | 🔄 | 获取直播/视频弹幕（待实现） |
| subscribe_danmaku | ❌ | 实时弹幕订阅（计划中） |

## 特有能力 (capabilities)

| 名称 | 描述 |
|---|---|
| fetch_video_info | 获取单个视频详细信息（时长、分辨率等） |
| fetch_danmaku | 获取视频弹幕（XML 格式或历史弹幕） |
| fetch_user_relation | 获取关注/粉丝列表 |
| fetch_live_danmaku | 获取直播间实时弹幕 |
| fetch_gift_record | 获取直播间礼物记录 |

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

### 直播信息

```
GET https://api.live.bilibili.com/room/v1/Room/get_info
参数：
  - room_id: 直播间 ID
  - from: room

响应字段：
  - room_info: 直播间基本信息
    - title: 直播标题
    - cover: 封面图 URL
    - play_url: 播放地址
    - live_status: 直播状态（0:未开播，1:直播中，2:轮播）
    - area_name: 分区名称
    - viewer_count: 观看人数
  - anchor_info: 主播信息
```

### 直播弹幕（历史）

```
GET https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory
参数：
  - roomid: 直播间 ID
  - cursor: 游标（从响应中获取下一页）

响应字段：
  - data: 
    - items: 弹幕列表
      - msg: 弹幕内容
      - timestamp: 发送时间
      - uid: 用户 ID
      - uname: 用户名
      - medal: 粉丝牌信息
```

### 视频弹幕（XML）

```
GET https://comment.bilibili.com/{cid}.xml
参数：cid = 视频 cid（从 video_info API 获取）

返回 XML 格式弹幕：
<d p="time,mode,size,color,timestamp,uid,crc32,cmid,...">弹幕内容</d>
```

### WebSocket 实时弹幕

```
wss://broadcastlv.chat.bilibili.com/sub

订阅消息：
{
  "protover": 3,
  "platform": "web",
  "type": 2,
  "roomid": {live_id}
}

服务器推送：
- 心跳包：定时发送保持连接
- 弹幕数据：需要解析 zlib 压缩的二进制数据
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

### 弹幕解析

#### XML 弹幕格式

```xml
<d p="15.5,1,25,16777215,1609459200,12345678,abc123,1234567890">弹幕内容</d>
```

参数说明：
- `p[0]`: 出现时间（秒）
- `p[1]`: 弹幕类型（1:滚动，4:底部，5:顶部，6:逆向，7:高级，8:代码）
- `p[2]`: 字体大小
- `p[3]`: 颜色（十进制 RGB）
- `p[4]`: 发送时间戳
- `p[5]`: 用户 ID
- `p[6]`: CRC32 校验
- `p[7]`: 弹幕 ID

#### 粉丝牌解析

```json
{
  "medal": {
    "target_name": "UP 主名字",
    "medal_name": "粉丝牌名称",
    "level": 10,
    "score": 5000,
    "is_lighted": true
  }
}
```

### 直播状态映射

| API 值 | 含义 | UnifiedLiveStream.status |
|---|---|---|
| 0 | 未开播 | "upcoming" |
| 1 | 直播中 | "live" |
| 2 | 轮播 | "live" |
| -1 | 直播间不存在 | null（返回 None） |

## 已知问题

1. **WBI key 缓存失效**: WBI key 会不定期更新，需要实现自动刷新机制
2. **部分视频地区限制**: 某些视频仅限中国大陆观看，海外服务器无法获取
3. **弹幕需要单独请求**: 弹幕不在评论 API 中返回，需要通过 XML 或 WebSocket 接口获取
4. **番剧/电影需要大会员**: 付费内容需要特殊权限
5. **直播弹幕协议复杂**: WebSocket 弹幕使用二进制协议，需要解析 zlib 压缩数据
6. **实时弹幕连接维护**: 需要定时发送心跳包保持 WebSocket 连接

## 测试样本

 fixtures 目录包含以下脱敏样本：

- `fixtures/user_profile.json`: 用户资料响应
- `fixtures/user_posts_page1.json`: 视频列表第一页
- `fixtures/video_info.json`: 视频详情
- `fixtures/comments.json`: 评论列表
- `fixtures/live_room_info.json`: 直播间信息（新增）
- `fixtures/live_danmaku_history.json`: 历史弹幕（新增）
- `fixtures/video_danmaku.xml`: 视频弹幕 XML（新增）

## 实现清单

### Phase 1 (已完成)
- [x] 定义 UnifiedDanmaku 和 UnifiedLiveStream 数据模型
- [x] 在 BaseAdapter 中添加直播相关方法
- [x] 更新 BilibiliAdapter 支持直播方法框架

### Phase 2 (进行中)
- [ ] 实现 fetch_live_stream() 调用直播信息 API
- [ ] 实现 fetch_danmaku() 调用历史弹幕 API
- [ ] 添加直播相关的 fixtures 测试样本
- [ ] 编写直播数据的 parser 解析模块

### Phase 3 (计划)
- [ ] 实现 subscribe_danmaku() WebSocket 实时订阅
- [ ] 实现礼物记录采集 (fetch_gift_record)
- [ ] 添加直播数据采集的 Celery 任务
- [ ] 实现直播状态监控和自动重连

## 参考资料

- [bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect): 最全面的 B 站 API 文档
- [bilibili-api-python](https://github.com/Nemo2011/bilibili-api): Python SDK 参考
