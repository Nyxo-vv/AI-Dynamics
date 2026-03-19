# AI Dynamics API 文档

Base URL: `http://localhost:9100`

---

## 健康检查

### `GET /api/health`

检查服务是否正常运行。

**响应示例：**
```json
{"status": "ok"}
```

---

## 抓取控制 (`/api/fetch`)

### `GET /api/fetch/status`

获取当前抓取/处理任务的状态。

**响应字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 当前状态：`idle`（空闲）/ `fetching`（抓取中）/ `processing`（LLM处理中） |
| `total_sources` | int | 总信息源数量 |
| `processed_sources` | int | 已处理的信息源数量 |
| `new_articles` | int | 本次新抓取的文章数 |
| `llm_total` | int | 需要LLM处理的文章总数 |
| `llm_processed` | int | LLM已处理的文章数 |

---

### `GET /api/fetch/backlog`

获取未处理文章（积压）的数量。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | string | 否 | 日期（YYYY-MM-DD），按该日期的简报时间窗口过滤 |

**响应示例：**
```json
{"unprocessed": 15, "total": 120}
```

---

### `POST /api/fetch/run`

手动触发一次 RSS 抓取 + LLM 处理。任务在后台执行，接口立即返回。

**响应示例：**
```json
{"message": "Fetch started", "status": {"status": "fetching", ...}}
```

如果任务已在进行中：
```json
{"message": "Fetch already in progress", "status": {...}}
```

---

## 文章 (`/api/articles`)

### `GET /api/articles`

获取文章列表，支持分页和多条件筛选。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码（≥1） |
| `per_page` | int | 20 | 每页数量（1-100） |
| `category` | string | - | 按分类标签筛选（research/product/opensource/news/funding/policy/community） |
| `source_id` | int | - | 按信息源ID筛选 |
| `is_starred` | bool | - | 按收藏状态筛选 |
| `search` | string | - | 关键词搜索（匹配标题、中文标题、中文摘要） |

**响应字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `items` | array | 文章列表 |
| `total` | int | 总数 |
| `page` | int | 当前页码 |
| `per_page` | int | 每页数量 |
| `pages` | int | 总页数 |

**文章对象字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 文章ID |
| `source_id` | int | 信息源ID |
| `source_name` | string | 信息源名称 |
| `title` | string | 原文标题 |
| `title_zh` | string | 中文标题 |
| `url` | string | 原文链接 |
| `summary_zh` | string | 中文摘要（2-3句） |
| `importance` | int | 重要性评分（1-5） |
| `tags` | array | 分类标签列表 |
| `published_at` | string | 发布时间 |
| `fetched_at` | string | 抓取时间 |
| `is_read` | bool | 是否已读 |
| `is_starred` | bool | 是否收藏 |
| `related_links` | array | 相关链接（论文/GitHub/Demo等） |

---

### `GET /api/articles/{article_id}`

获取单篇文章的详细信息。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `article_id` | int | 文章ID |

**响应：** 完整的文章对象（字段同上），未找到返回 `{"error": "not found"}`。

---

### `PATCH /api/articles/{article_id}`

更新文章的已读/收藏状态。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `article_id` | int | 文章ID |

**请求体：**
```json
{
  "is_read": true,
  "is_starred": false
}
```

所有字段均为可选，仅更新传入的字段。

**响应示例：**
```json
{"ok": true}
```

---

## 信息源 (`/api/sources`)

### `GET /api/sources`

获取所有信息源列表，包含各源的文章数量统计。

**响应示例：**
```json
[
  {
    "id": 1,
    "name": "TechCrunch AI",
    "url": "https://...",
    "type": "rss",
    "category": "media",
    "enabled": true,
    "fetch_interval_min": 60,
    "article_count": 42
  }
]
```

---

### `PATCH /api/sources/{source_id}`

启用或禁用某个信息源。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `source_id` | int | 信息源ID |

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `enabled` | bool | `true` 启用 / `false` 禁用 |

**响应示例：**
```json
{"ok": true}
```

---

## 简报 (`/api/briefings`)

### `POST /api/briefings/generate`

为指定日期生成每日简报。简报基于前一天 09:00 到当天 09:00 的时间窗口内的文章。

**请求体：**
```json
{"date": "2026-03-19"}
```

**响应：** 生成的简报内容，包含头条、分类板块和统计信息。

---

### `GET /api/briefings/recent`

获取最近 N 天的简报状态列表。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `days` | int | 7 | 查询天数（1-30） |

**响应示例：**
```json
{
  "items": [
    {
      "date": "2026-03-19",
      "generated": true,
      "article_count": 35,
      "generated_at": "2026-03-19 09:15:00"
    },
    {
      "date": "2026-03-18",
      "generated": false,
      "article_count": 28,
      "generated_at": null
    }
  ]
}
```

---

### `GET /api/briefings/search`

在简报文章中搜索关键词，匹配标题、中文标题、中文摘要和信息源名称。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 搜索关键词 |
| `date` | string | 否 | 限定搜索某天的简报（YYYY-MM-DD） |

**响应示例：**
```json
{
  "items": [
    {
      "id": 123,
      "title": "GPT-5 Released",
      "title_zh": "GPT-5 发布",
      "url": "https://...",
      "summary_zh": "...",
      "importance": 5,
      "published_at": "2026-03-19T08:00:00",
      "source_name": "TechCrunch AI",
      "tags": ["product"]
    }
  ],
  "total": 1
}
```

---

### `GET /api/briefings/{briefing_date}`

获取指定日期的完整简报，包含头条文章、分类板块和完整文章数据。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `briefing_date` | string | 日期（YYYY-MM-DD） |

**响应：** 完整简报内容，包含 `headlines`（头条）、`sections`（分类板块）、`stats`（统计）和各文章详情。

未找到返回 `404`。
