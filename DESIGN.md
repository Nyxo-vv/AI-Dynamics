# AI Dynamics — 全球 AI 行业动态追踪工具

> 设计文档 v0.4 | 2026-03-18

## 1. 项目目标

构建一个个人工具，自动聚合全球 AI 行业的关键信息源，帮助用户高效掌握行业动态，包括：研究突破、产品发布、开源进展、投融资、政策法规等。

---

## 2. 数据来源

### 2.1 实验室 / 公司官方

| 来源 | RSS / 地址 | 说明 |
|------|-----------|------|
| OpenAI | `https://openai.com/news/rss.xml` | 新模型、o 系列、API 更新 |
| Google DeepMind | `https://deepmind.google/blog/rss.xml` | Gemini、AlphaFold 等研究进展 |
| Google AI Blog | `https://blog.google/technology/ai/rss/` | Google 产品层面的 AI 动态 |
| Anthropic | `https://www.anthropic.com/news/rss` | Claude 系列、安全研究 |
| Meta AI | `https://ai.meta.com/blog/rss/` | LLaMA 系列、开源大模型 |
| Microsoft AI | `https://blogs.microsoft.com/ai/feed/` | Copilot、Azure AI |

### 2.2 学术 / 论文

| 来源 | RSS / 地址 | 说明 |
|------|-----------|------|
| arXiv cs.AI | `https://arxiv.org/rss/cs.AI` | 突破性论文第一现场，量大需过滤 |
| Papers with Code | `https://paperswithcode.com/latest` | 论文 + 代码配对，可看 trending |
| MarkTechPost | `https://www.marktechpost.com/feed/` | 论文 + 新模型快讯，摘要质量不错 |

> **arXiv 量控策略：** arXiv cs.AI 日均 50-100+ 篇，全量调 LLM 成本过高。采用两阶段过滤：
> 1. **预筛**：仅对标题 + 摘要做轻量关键词匹配（LLM、transformer、agent、reasoning 等高价值关键词），过滤掉明显无关的论文
> 2. **LLM 处理**：仅对通过预筛的论文（预计日均 10-20 篇）调用 Claude 做意译 + 分类 + 评分

### 2.3 Newsletter / 快讯聚合

| 来源 | 获取方式 | 说明 |
|------|---------|------|
| The Rundown AI | 邮件订阅 → 转 RSS | 日更质量最高的 AI 快讯 |
| Ben's Bites | 邮件 / RSS | 工具 + 产品 + 小突破汇总 |

> **邮件 Newsletter 接入方案：** 对于仅支持邮件订阅的来源，使用 [kill-the-newsletter](https://kill-the-newsletter.com) 等服务将邮件订阅转为 RSS feed，统一走 RSS 抓取管线。

### 2.4 科技媒体

| 来源 | RSS / 地址 | 说明 |
|------|-----------|------|
| MIT Technology Review (AI) | `https://www.technologyreview.com/topic/artificial-intelligence/feed/` | 深度报道 |
| WIRED AI | `https://www.wired.com/feed/tag/ai/latest/rss` | 科技文化视角 |
| Ars Technica (AI) | `https://arstechnica.com/tag/artificial-intelligence/feed/` | 技术深度分析 |

### 2.5 开源社区

| 来源 | RSS / 地址 | 说明 |
|------|-----------|------|
| Hugging Face Blog | `https://huggingface.co/blog/feed.xml` | 开源模型、数据集、工具 |
| GitHub Trending (ML) | `https://github.com/trending?since=daily` | 无 RSS，需爬取并过滤 ML 相关 |

### 2.6 社区讨论 / 信号源

| 来源 | RSS / 地址 | 说明 |
|------|-----------|------|
| Reddit r/MachineLearning | `https://www.reddit.com/r/MachineLearning/.rss` | 一线研究者讨论，需自定义 User-Agent |
| Reddit r/LocalLLaMA | `https://www.reddit.com/r/LocalLLaMA/.rss` | 开源模型社区风向标，需自定义 User-Agent |
| Hacker News | 需通过 API 过滤 AI 相关 | 技术社区早期信号 |

### 2.7 投融资 / 商业

| 来源 | 获取方式 | 说明 |
|------|---------|------|
| CB Insights AI Newsletter | 邮件订阅 | AI 投融资、市场格局 |
| The Information (AI) | 付费订阅 | 信息密度极高，业内必读 |

### 2.8 中文来源

| 来源 | RSS / 地址 | 说明 |
|------|-----------|------|
| 机器之心 | `https://www.jiqizhixin.com/rss` | 国内最好的 AI 媒体 |
| 量子位 | 需爬取或关注公众号 | 国内 AI 快讯 |

---

## 3. 信息分类体系

所有抓取的内容按以下维度分类：

| 类别 | 标签 | 典型来源 |
|------|------|---------|
| 研究突破 | `research` | arXiv, Papers with Code, DeepMind |
| 产品发布 | `product` | OpenAI, Google, Anthropic 官方博客 |
| 开源动态 | `opensource` | Hugging Face, GitHub Trending, r/LocalLLaMA |
| 行业新闻 | `news` | MIT Tech Review, WIRED, Ars Technica |
| 投融资 | `funding` | CB Insights, The Information |
| 政策法规 | `policy` | 各媒体 + 专门来源 |
| 社区讨论 | `community` | Reddit, Hacker News |

---

## 4. 系统架构

### 4.1 呈现方式

**本地 Web Dashboard** — 浏览器访问 `http://localhost:5173`

### 4.2 技术栈

| 层 | 技术选型 | 理由 |
|----|---------|------|
| 后端 | Python + FastAPI | 生态成熟，RSS 解析 / LLM 调用库丰富 |
| 前端 | Vite + React + TailwindCSS + shadcn/ui | Vite 构建快，shadcn/ui 提供高质量基础组件 |
| 数据库 | SQLite | 零配置，单文件，个人工具足够 |
| 定时任务 | APScheduler | Python 原生，无需外部 cron |
| RSS 解析 | feedparser | Python RSS 解析标准库 |
| LLM (主) | Google Gemini API (gemini-2.0-flash) | 免费额度充足，质量好 |
| LLM (次) | Groq (llama-3.3-70b-versatile) | 免费 100K tokens/天，响应极快 |
| LLM (三) | OpenRouter (多模型可选) | 聚合平台，提供多种免费模型 |
| LLM (兜底) | Ollama (本地) | 所有云端额度耗尽时本地兜底 |
| 后端端口 | 9100 | `http://localhost:9100` |
| 前端端口 | 5173 | `http://localhost:5173`（Vite 默认） |

#### 4.2.1 LLM 多引擎策略

```
请求 → Gemini API
         │
         ├─ 成功 → 返回结果
         │
         └─ 失败 (429/额度耗尽)
              │
              └─ Groq API (自动重试 429)
                   │
                   ├─ 成功 → 返回结果
                   │
                   └─ 失败
                        │
                        └─ OpenRouter API (自动重试 429)
                             │
                             ├─ 成功 → 返回结果
                             │
                             └─ 失败
                                  │
                                  └─ Ollama (本地兜底)
                                       │
                                       └─ 返回结果
```

**批量合并 Prompt：** 5 篇文章合并为一次 API 调用，返回 JSON 数组，API 调用次数减少 80%。批量失败时自动降级为逐篇处理。

**配置方式（.env）：**
```env
# Gemini API (主引擎，留空则跳过)
GEMINI_API_KEY=

# Groq API (次引擎，留空则跳过)
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# OpenRouter API (三引擎，留空则跳过)
# 免费模型：meta-llama/llama-3.3-70b-instruct:free
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Ollama (兜底引擎，本地运行)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

- 各引擎 API Key 为空时自动跳过，不报错
- 429 限流时自动解析 `retryDelay` 重试（最多 3 次），超限后降级到下一引擎
- 所有引擎使用统一的 prompt 模板，输出格式一致
- 启动时自动检测积压文章并在后台处理

### 4.3 抓取策略

| 触发方式 | 时间 | 说明 |
|---------|------|------|
| 定时抓取 | 每天 **10:00** 和 **17:00** | APScheduler 定时任务，覆盖早晚两个信息高峰 |
| 手动刷新 | 随时 | Dashboard 页面「立即刷新」按钮，后端收到请求后即时拉取全部 RSS |
| 启动积压处理 | 后端启动时 | 自动检测未处理文章，后台批量处理（不阻塞 API） |

- 后端启动时若已过当天的定时点但未执行过，自动补抓（同启动时自检逻辑）
- 两种方式共用同一个抓取管线（拉 RSS → 去重 → LLM 处理 → 入库）
- 手动刷新期间前端显示抓取进度，完成后自动刷新文章列表

**API：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/fetch/run` | 手动触发立即抓取 |
| `GET` | `/api/fetch/status` | 查询当前抓取状态（idle / running / 进度） |
| `GET` | `/api/fetch/backlog?date=` | 查询积压文章数（可选按日期窗口筛选） |

### 4.4 整体架构

```
┌───────────────────────────────────────────────────────────┐
│              浏览器 Dashboard (:5173)                       │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │ 每日简报  │ 信息流   │ 按类别   │  按来源   │ 收藏     │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘ │
└────────────────────────────┬──────────────────────────────┘
                             │ HTTP API
┌────────────────────────────┴──────────────────────────────┐
│                   FastAPI 后端 (:9100)                      │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ REST API   │  │ 抓取调度器    │  │ LLM 多引擎         │  │
│  │ /api/*     │  │ 10:00 + 17:00│  │ Gemini→Groq→      │  │
│  │            │  │ + 手动刷新    │  │ OpenRouter→Ollama  │  │
│  └─────┬──────┘  └──────┬───────┘  └──────┬────────────┘  │
│        │                │                 │               │
│  ┌─────┴────────────────┴─────────────────┴─────────────┐ │
│  │                  SQLite 数据库                         │ │
│  │  articles │ sources │ article_tags │ briefings        │ │
│  └───────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

### 4.5 数据模型

```sql
-- 信息来源
CREATE TABLE sources (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,           -- 'OpenAI'
    url         TEXT NOT NULL,           -- RSS URL
    type        TEXT NOT NULL,           -- 'rss' | 'scrape' | 'api'
    category    TEXT NOT NULL,           -- 'lab' | 'academic' | 'media' | ...
    enabled     BOOLEAN DEFAULT 1,
    fetch_interval_min INTEGER DEFAULT 60,
    last_fetched_at    DATETIME,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 文章/条目
CREATE TABLE articles (
    id          INTEGER PRIMARY KEY,
    source_id   INTEGER NOT NULL REFERENCES sources(id),
    title       TEXT NOT NULL,
    title_zh    TEXT,                    -- 中文意译标题
    url         TEXT NOT NULL UNIQUE,    -- 原文链接，用于去重
    author      TEXT,
    content     TEXT,                    -- 原始内容
    summary_zh  TEXT,                    -- LLM 生成的中文意译摘要
    cover_image TEXT,                    -- 封面图 URL (从原文提取)
    images      TEXT,                    -- 文章内图片 URL 列表 (JSON 数组)
    related_links TEXT,                  -- 相关链接 (JSON 数组，如论文/代码/Demo)
    language    TEXT DEFAULT 'en',       -- 原文语言: 'en' | 'zh' | ...
    published_at DATETIME,
    fetched_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    importance  INTEGER DEFAULT 0,      -- LLM 评分 1-5
    is_read     BOOLEAN DEFAULT 0,
    is_starred  BOOLEAN DEFAULT 0
);

-- 文章标签 (LLM 自动分类)
CREATE TABLE article_tags (
    article_id  INTEGER NOT NULL REFERENCES articles(id),
    tag         TEXT NOT NULL,           -- 'research' | 'product' | ...
    PRIMARY KEY (article_id, tag)
);
```

### 4.6 LLM 内容处理策略

#### 4.6.1 中文意译

对非中文来源的文章，LLM 在抓取入库时自动处理：

| 字段 | 处理方式 |
|------|---------|
| `title_zh` | 将原标题意译为自然流畅的中文，非逐字翻译，保留专有名词原文（如 GPT-5、LLaMA） |
| `summary_zh` | 基于原文内容生成 2-3 句中文摘要，突出核心信息，使用符合中文阅读习惯的表达 |

对中文来源（机器之心、量子位等），`title_zh` 直接使用原标题，`summary_zh` 基于原文提炼摘要。

**意译原则：**
- 传达原意而非逐字翻译，让中文读者能快速理解
- 专业术语保留英文原文，如 Transformer、RLHF、fine-tuning
- 公司/产品名保留原文，如 OpenAI、Claude、Hugging Face
- 数字、指标等精确信息必须保留

#### 4.6.2 媒体与链接提取

抓取文章时，从 RSS 内容和原文页面中提取：

| 字段 | 提取策略 |
|------|---------|
| `cover_image` | 优先取 RSS `<media:content>` / `<enclosure>`，其次取正文第一张图 |
| `images` | 提取正文中所有 `<img>` 的 src，过滤 icon/logo/tracker 等无关图片 |
| `related_links` | LLM 从正文中识别相关资源链接（论文 PDF、GitHub 仓库、Demo 页面、HuggingFace 模型页等） |

`related_links` JSON 格式：
```json
[
  { "label": "论文 PDF", "url": "https://arxiv.org/pdf/2026.xxxxx" },
  { "label": "GitHub 代码", "url": "https://github.com/org/repo" },
  { "label": "在线 Demo", "url": "https://huggingface.co/spaces/..." },
  { "label": "模型权重", "url": "https://huggingface.co/org/model" }
]
```

### 4.7 UI 设计规范

#### 4.7.1 整体风格

白色基调、极简干净、清晰易读、高专注度。目标：30-90 秒内快速抓住重点。

参考风格：Notion 极简白 + Linear/Superhuman 生产力感 + 清晰层级。
避免：渐变背景、neumorphism、玻璃态、过多图标。

#### 4.7.2 色彩规范

| 元素 | 背景色 | 文字色 | 强调色 | 圆角 | 阴影 |
|------|--------|--------|--------|------|------|
| 页面背景 | #FAFAFA | - | - | - | - |
| 卡片/头条 | #FFFFFF | #111827 | #3B82F6 (链接) | 8-12px | `0 1px 3px rgba(0,0,0,0.06)` |
| Tabs 未选 | #F3F4F6 | #4B5563 | - | 6-8px | - |
| Tabs 选中 | #FFFFFF | #2563EB | 底部 2px #2563EB | 6-8px | - |
| 分割线 | - | - | #E5E7EB | - | - |
| 次要文字 | - | #6B7280 | - | - | - |
| 来源标签 pill | #EFF6FF | #2563EB | - | 9999px | - |

分类标签配色：

| 分类 | 颜色 | Tailwind |
|------|------|---------|
| research 研究突破 | #10B981 绿 | `bg-emerald-50 text-emerald-700` |
| product 产品发布 | #3B82F6 蓝 | `bg-blue-50 text-blue-700` |
| opensource 开源动态 | #8B5CF6 紫 | `bg-violet-50 text-violet-700` |
| news 行业新闻 | #F59E0B 橙 | `bg-amber-50 text-amber-700` |
| funding 投融资 | #EC4899 粉 | `bg-pink-50 text-pink-700` |
| policy 政策法规 | #6366F1 靛 | `bg-indigo-50 text-indigo-700` |
| community 社区讨论 | #14B8A6 青 | `bg-teal-50 text-teal-700` |

#### 4.7.3 字体与排版

```css
font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

| 用途 | 字号 | 字重 | 行高 |
|------|------|------|------|
| 页面标题 | 24-28px | 700 | 1.3 |
| 卡片标题 | 18px | 600 | 1.4 |
| 正文/摘要 | 15-16px | 400 | 1.6 |
| 小字/时间/标签 | 13px | 400-500 | 1.4 |

间距：页面 padding 24-32px，卡片间距 16-24px，元素内部 padding 16-20px。

#### 4.7.4 交互

- hover：轻微抬升 `translateY(-1px)` + 背景 `#F3F4F6` + 阴影增强
- 卡片 hover：左侧 3px 蓝色边框
- 按钮 hover：背景加深一级
- 过渡：`transition-all duration-150 ease-in-out`

### 4.8 页面结构与布局

#### 4.8.1 页面总览

| 页面 | Tab 名称 | 说明 |
|------|---------|------|
| **每日简报** | 简报 | 默认首页，头条 + 分类浏览 |
| **信息流** | 信息流 | 按时间排列的全部文章，支持筛选/搜索 |
| **收藏** | 收藏 | 星标文章 |

#### 4.8.2 固定顶部导航栏 (Header)

```
┌──────────────────────────────────────────────────────────────────────┐
│  AI Daily          [简报]  [信息流]  [收藏]          [立即刷新] [⚙]  │
│                                                                      │
│  2026-03-17                          最后更新：15 分钟前              │
└──────────────────────────────────────────────────────────────────────┘
```

- 高度：64px，背景白色，底部 1px `#E5E7EB` 分割线
- 左：「AI Daily」文字 logo（20px bold）
- 中：页面 Tab 切换（简报 / 信息流 / 收藏）
- 右：「立即刷新」按钮（触发 `POST /api/fetch/run`） + 设置图标
- 日期 + 最后更新时间显示在导航栏下方或内部

#### 4.8.3 每日简报页面布局（默认首页）

```
┌──────────────────────────────────────────────────────────────────────┐
│  AI Daily          [简报]  [信息流]  [收藏]          [立即刷新] [⚙]  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ← 3/11  3/12  3/13  3/14  3/15  3/16 [3/17] →                      │
│     ○     ○     ●     ●     ●     ●    ○                             │
│                                                                      │
│  [生成今日简报]                            状态：未生成 │ 共 58 条    │
│                                                                      │
│  🔍 [搜索关键词...]                                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ★ 头条 Top 10                                          24px bold    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   3 列卡片    │
│  │ 标题 (18px)   │  │ 标题          │  │ 标题          │   网格       │
│  │ 摘要 2行灰字  │  │ 摘要          │  │ 摘要          │              │
│  │               │  │               │  │               │              │
│  │ [OpenAI] 2h前 │  │ [arXiv] 3h前  │  │ [Meta] 5h前   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ ...           │  │ ...           │  │ ...           │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ...（共 10 张卡片，4行 / 3+3+3+1）                                  │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  分类浏览                                               24px bold    │
│                                                                      │
│  [研究突破(15)] [产品发布(12)] [开源动态(10)] [行业新闻(8)]           │
│  [投融资(3)]   [社区讨论(2)]                                         │
│  （无文章的分类自动隐藏）                                             │
│                                                                      │
│  ▼ 研究突破 (15)                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ · DeepMind 提出线性注意力变体      [arXiv]   07:45  → 原文     │  │
│  │   一种新的线性复杂度注意力机制...                    (14px灰)  │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │ · Anthropic 发布对齐研究新框架      [Anthropic] 06:20  → 原文  │  │
│  │   提出基于宪法 AI 的改进方法...                               │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │ · ...                                                         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  [查看更多 ↓]（超过 8 条时显示）                                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**头条卡片规格：**
- 布局：CSS Grid 3 列（桌面 1200px+），2 列（平板），1 列（手机）
- 最小高度：140px，内部 padding 16-20px
- 标题：18px semibold，最多 2 行截断 `line-clamp-2`
- 摘要：15px，行高 1.6，灰色 `#4B5563`，最多 2 行
- 底部：来源 pill 标签（带分类配色） + 相对时间（「2小时前」） + → 原文链接
- hover：左侧 3px 蓝色边框 + 轻微阴影增强

**分类列表规格：**
- Tab 式切换，横向排列，可滚动
- 每个 Tab 显示分类名 + 文章数量，使用对应分类配色
- 当天无文章的分类自动隐藏
- 列表模式（紧凑），每行：标题 16px + 来源 pill + 时间 + 1 行摘要（可选 14px 灰色）
- 点击标题展开完整摘要或跳转原文
- 超过 8 条显示「查看更多」折叠按钮

**日期导航规格：**
- 默认选中今天，点击切换日期查看历史简报
- 每个日期下方显示状态指示点（已生成 ● 蓝色 / 未生成 ○ 灰色）
- 未生成的日期可补生成（只要数据库中有对应时间窗口的文章）

**搜索栏：**
- 全宽，圆角 8px，placeholder「搜索关键词...」
- 支持对已生成简报的全部文章全文检索（匹配标题、摘要、来源名）
- 支持跨日期搜索全部历史简报

**空状态：**
- 当天无文章时，居中温和提示 + 建议点击「立即刷新」抓取

### 4.9 每日简报功能

#### 4.9.1 简报时间窗口

每份简报覆盖 **前一天 09:00 ~ 当天 09:00**（24 小时），以用户本地时区为准。

```
示例：3月17日的简报
  时间范围：3月16日 09:00 ~ 3月17日 09:00
  包含：该窗口内 published 的所有文章
  回退：若 published_at 为空，则以 fetched_at 为准
```

#### 4.9.2 简报生成流程

1. 用户在页面点击 **「生成今日简报」** 按钮
2. 后端收集时间窗口内的所有文章
3. 调用 LLM 生成结构化简报：
   - **头条 Top 10**：从全部文章中选出最重要的 10 条，标记为「头条」
   - **分类归档**：剩余文章按 research / product / opensource / news 等分组，无文章的分类不生成
   - **所有文章**均附带中文意译摘要、原文链接、封面图
   - **数据统计**：各类别文章数量、来源分布
4. 简报存入数据库，后续可直接查看无需重新生成

#### 4.9.3 简报数据模型

```sql
-- 每日简报
CREATE TABLE briefings (
    id          INTEGER PRIMARY KEY,
    date        DATE NOT NULL UNIQUE,      -- 简报日期，如 '2026-03-17'
    window_start DATETIME NOT NULL,         -- 时间窗口起点 (前一天 09:00)
    window_end  DATETIME NOT NULL,          -- 时间窗口终点 (当天 09:00)
    content     TEXT NOT NULL,              -- LLM 生成的简报内容 (JSON)
    article_count INTEGER NOT NULL,         -- 窗口内文章总数
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

简报 `content` JSON 结构：

```json
{
  "headlines": [
    { "article_id": 42, "rank": 1 },
    { "article_id": 17, "rank": 2 }
  ],
  "sections": [
    {
      "category": "research",
      "label": "研究突破",
      "article_ids": [10, 23, 35, 48]
    },
    {
      "category": "product",
      "label": "产品发布",
      "article_ids": [11, 29]
    }
  ],
  "stats": {
    "total": 58,
    "headline_count": 10,
    "by_category": { "research": 15, "product": 12, "opensource": 10 },
    "by_source": { "arXiv": 8, "OpenAI": 3 }
  }
}
```

> **设计原则：** 简报 JSON 只存 `article_id` 引用，不冗余存储文章内容。前端查询简报时，后端 JOIN `articles` 表返回完整数据（title_zh、summary_zh、cover_image、related_links 等）。这样文章数据只维护一份，避免不一致。
>
> `headlines` 固定 10 条，按重要性排序（rank 1-10）；`sections` 中为头条以外的剩余文章，每个分类内按 `published_at` 倒序排列。

#### 4.9.4 API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/briefings/generate` | 生成指定日期简报，body: `{ "date": "2026-03-17" }` |
| `GET` | `/api/briefings/{date}` | 获取指定日期简报 |
| `GET` | `/api/briefings/recent?days=7` | 获取最近 7 天简报状态列表 |
| `GET` | `/api/briefings/search?q=关键词&date=2026-03-17` | 搜索简报文章，`date` 可选，不传则搜索全部历史简报 |

### 4.10 数据生命周期管理

#### 4.10.1 自动月度清理

每月最后一天自动清理**上个月整月**的历史数据：

```
示例：9月30日触发清理
  清理范围：8月1日 00:00 ~ 8月31日 23:59:59
  保留范围：9月1日至今的所有数据
```

**触发方式 — 启动时自检：**

由于本工具运行在个人电脑上，不保证 24 小时在线，因此**不依赖定时任务触发清理**，而是在每次后端启动时自动检查：

```python
# main.py FastAPI startup 事件中执行
def check_and_cleanup():
    today = date.today()
    if today.day >= 1:  # 每月任意一天启动都会检查
        # 计算上个月的月份
        last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        # 检查上个月的数据是否仍存在
        count = db.query("SELECT COUNT(*) FROM articles WHERE published_at >= ? AND published_at < ?",
                         last_month, last_month + 1month)
        if count > 0:
            run_cleanup(last_month)  # 归档 + 清理
```

- 每次启动后端时自动检查，无需依赖开机时间
- 如果上个月数据已清理过，跳过不重复执行
- 无论是 10/1 还是 10/15 才开机，都能补上 9 月数据的清理

**清理流程：**

1. 启动时检测到上个月数据仍存在，触发清理
2. 清理前自动备份待删数据到 `data/archive/` 目录（压缩 JSON），以防误删后需恢复
3. 按顺序删除：
   - `article_tags` — 删除关联的标签记录
   - `briefings` — 删除对应月份的简报
   - `articles` — 删除对应月份的文章
4. 执行 `VACUUM` 回收 SQLite 磁盘空间
5. 记录清理日志（删除了多少条记录、释放了多少空间）

**清理 SQL：**

```sql
-- 以 9月30日清理 8月数据为例
-- 1. 删除文章标签
DELETE FROM article_tags WHERE article_id IN (
    SELECT id FROM articles
    WHERE published_at >= '2026-08-01 00:00:00'
      AND published_at <  '2026-09-01 00:00:00'
);

-- 2. 删除简报
DELETE FROM briefings
WHERE date >= '2026-08-01' AND date < '2026-09-01';

-- 3. 删除文章
DELETE FROM articles
WHERE published_at >= '2026-08-01 00:00:00'
  AND published_at <  '2026-09-01 00:00:00';

-- 4. 回收空间
VACUUM;
```

#### 4.10.2 归档备份

清理前将待删数据导出为压缩 JSON 归档：

```
data/
├── ai_dynamics.db
└── archive/
    ├── 2026-08.json.gz      # 8月归档 (约 500 KB 压缩后)
    ├── 2026-07.json.gz
    └── ...
```

归档文件包含该月所有 articles + briefings + article_tags 的完整数据，可用于：
- 误删恢复
- 离线分析历史趋势
- 长期归档保存

#### 4.10.3 数据保留策略总结

| 数据 | 保留时长 | 说明 |
|------|---------|------|
| 当月 + 上月数据 | 实时可查 | 数据库在线，Dashboard 可浏览 |
| 更早的月份 | 自动清理 | 每月最后一天清理上个月数据 |
| 归档文件 | 永久保存 | 压缩 JSON，每月约 500 KB |

> **存储影响：** 数据库始终只保留最近 ~2 个月数据（约 30 MB），不会无限增长。归档文件每月约 500 KB，10 年也才 ~60 MB。

### 4.11 核心功能与优先级

| 优先级 | 功能 | MVP | 说明 |
|--------|------|-----|------|
| P0 | RSS 抓取 + 存储 + 去重 | ✓ | 核心数据管线 |
| P0 | LLM 意译 + 分类 + 重要性评分 | ✓ | 简报生成的前置依赖，抓取时即处理 |
| P0 | 每日简报生成 + 7天日期导航 | ✓ | 核心阅读体验 |
| P0 | Dashboard 简报 + 信息流展示 | ✓ | 基本可用 |
| P1 | 简报内搜索 + 筛选 | ✓ | 关键词精筛已生成简报 |
| P2 | 已读/收藏管理 | | 个人阅读状态 |
| P3 | 非 RSS 来源抓取 | | GitHub Trending, HN 等 |
| P3 | 自定义关键词订阅/高亮 | | "transformer", "AGI" 等 |
| P4 | 趋势分析 / 热度图 | | 哪些话题在升温 |

---

## 5. 项目结构

```
AI Dynamics/
├── DESIGN.md
├── .env.example             # 环境变量模板 (GEMINI_API_KEY, OLLAMA 配置等)
├── .env                     # 本地环境变量 (不入 git)
├── .gitignore
├── backend/
│   ├── pyproject.toml       # Python 项目配置 + 依赖管理
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置 (端口、API Key 等，读取 .env)
│   ├── database.py          # SQLite 连接 + 初始化
│   ├── models.py            # Pydantic 模型
│   ├── fetcher/
│   │   ├── rss.py           # RSS 抓取器 (含 Reddit UA 处理)
│   │   ├── filter.py        # arXiv 等高量源的预筛过滤
│   │   ├── scraper.py       # 网页爬虫 (GitHub Trending 等)
│   │   ├── scheduler.py     # 定时调度 (10:00 + 17:00)
│   │   └── cleanup.py       # 月度数据清理 + 归档
│   ├── llm/
│   │   ├── engine.py        # LLM 多引擎管理 (Gemini → Groq → OpenRouter → Ollama)
│   │   ├── processor.py     # LLM 统一处理 (意译 + 分类 + 评分)
│   │   └── briefing.py      # LLM 简报生成器
│   ├── api/
│   │   ├── articles.py      # 文章 CRUD API
│   │   ├── sources.py       # 来源管理 API
│   │   └── briefings.py     # 每日简报 API
│   └── seed_sources.py      # 初始化数据来源
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Briefing.tsx  # 每日简报 (默认首页)
│   │   │   ├── Feed.tsx      # 信息流
│   │   │   ├── Category.tsx  # 按类别
│   │   │   └── Starred.tsx   # 收藏
│   │   └── components/
│   │       ├── ArticleCard.tsx
│   │       ├── Sidebar.tsx
│   │       ├── FilterBar.tsx
│   │       └── DateNavigator.tsx  # 7天日期选择器
│   └── tailwind.config.js
└── data/
    ├── ai_dynamics.db       # SQLite 数据库文件 (不入 git)
    └── archive/             # 月度归档 (不入 git)
        └── 2026-08.json.gz
```

---

## 6. 数据来源覆盖矩阵

```
                研究  产品  开源  新闻  投融资  社区
OpenAI           ·    ✓     ·    ·     ·      ·
DeepMind         ✓    ✓     ·    ·     ·      ·
Anthropic        ✓    ✓     ·    ·     ·      ·
Meta AI          ✓    ✓     ✓    ·     ·      ·
Microsoft AI     ·    ✓     ·    ·     ·      ·
arXiv            ✓    ·     ·    ·     ·      ·
Papers w/ Code   ✓    ·     ✓    ·     ·      ·
MarkTechPost     ✓    ✓     ·    ✓     ·      ·
The Rundown AI   ✓    ✓     ✓    ✓     ·      ·
Ben's Bites      ·    ✓     ✓    ✓     ·      ·
MIT Tech Review  ✓    ·     ·    ✓     ·      ·
WIRED AI         ·    ·     ·    ✓     ·      ·
Ars Technica     ✓    ·     ·    ✓     ·      ·
Hugging Face     ✓    ·     ✓    ·     ·      ·
GitHub Trending  ·    ·     ✓    ·     ·      ·
Reddit ML        ✓    ·     ✓    ·     ·      ✓
Reddit LocalLLaMA·    ·     ✓    ·     ·      ✓
Hacker News      ·    ✓     ✓    ✓     ·      ✓
CB Insights      ·    ·     ·    ·     ✓      ·
The Information  ·    ✓     ·    ✓     ✓      ·
机器之心          ✓    ✓     ✓    ✓     ✓      ·
量子位            ·    ✓     ·    ✓     ·      ·
```

---

## 7. MVP 实现计划

**MVP 目标：** 能抓取所有 RSS 源，LLM 自动意译+分类+评分，生成每日简报，Dashboard 可浏览+搜索。

### 阶段 1 — 后端基础 + 数据管线
1. 初始化 Python 项目（pyproject.toml、.env 配置）
2. 实现 SQLite 数据库初始化 + 全部数据模型（sources、articles、article_tags、briefings）
3. 实现 RSS 抓取器（feedparser）+ arXiv 预筛过滤器
4. 导入所有 RSS 来源种子数据（含 Newsletter 转 RSS）
5. 实现定时调度（APScheduler）

### 阶段 2 — LLM 处理
6. 接入 Claude API，实现统一处理器（意译 + 分类 + 重要性评分 + 媒体/链接提取）
7. 在抓取管线中集成 LLM 处理，抓取即处理

### 阶段 3 — 简报系统
8. 实现简报生成 API + LLM 简报生成器（选头条 Top 10 + 分类归档）
9. 实现简报查询接口（JOIN articles 返回完整数据）
10. 实现简报内搜索 API

### 阶段 4 — 前端 Dashboard
11. 初始化 React + TailwindCSS 项目
12. 实现每日简报页面（7天日期导航 + 生成按钮 + 头条 + 分类浏览 + 搜索）
13. 实现信息流页面（时间线 + 筛选）
14. 实现按类别/来源浏览

### 阶段 5 — 数据管理 + 完善
15. 实现月度自动清理 + 归档备份（cleanup.py + APScheduler 注册）
16. 已读/收藏状态管理
17. 非 RSS 来源接入（GitHub Trending、HN 等）
