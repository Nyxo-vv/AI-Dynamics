# AI Dynamics — 全球 AI 行业动态追踪工具

> 设计文档 v0.6 | 2026-03-20

## 1. 项目目标

构建一个个人工具，自动聚合全球 AI 行业的关键信息源，帮助用户高效掌握行业动态，包括：研究突破、产品发布、开源进展、投融资、政策法规等。

---

## 2. 数据来源

### 2.1 实验室 / 公司官方

| 来源 | RSS / 地址 | 状态 | 说明 |
|------|-----------|------|------|
| OpenAI | `https://openai.com/news/rss.xml` | ✅ 已接入 | 新模型、o 系列、API 更新 |
| Google DeepMind | `https://deepmind.google/blog/rss.xml` | ✅ 已接入 | Gemini、AlphaFold 等研究进展 |
| Google AI Blog | `https://blog.google/technology/ai/rss/` | ✅ 已接入 | Google 产品层面的 AI 动态 |
| Anthropic | `https://www.anthropic.com/news/rss` | ⏸ 待接入 | 官方 RSS 已下线，需自建 RSSHub |
| Engineering at Meta | `https://engineering.fb.com/feed/` | ✅ 已接入 | Meta 工程博客（含 AI 内容） |
| Microsoft AI | `https://blogs.microsoft.com/ai/feed/` | ✅ 已接入 | Copilot、Azure AI |

### 2.2 学术 / 论文

| 来源 | RSS / 地址 | 状态 | 说明 |
|------|-----------|------|------|
| arXiv cs.AI | `https://arxiv.org/rss/cs.AI` | ✅ 已接入 | 突破性论文第一现场，量大需过滤 |
| Papers with Code | `https://paperswithcode.com/latest` | ⏸ 待接入 | 论文 + 代码配对，可看 trending |
| MarkTechPost | `https://www.marktechpost.com/feed/` | ✅ 已接入 | 论文 + 新模型快讯，摘要质量不错 |

> **arXiv 量控策略：** arXiv cs.AI 日均 50-100+ 篇，全量调 LLM 成本过高。采用两阶段过滤：
> 1. **预筛**：仅对标题 + 摘要做轻量关键词匹配（LLM、transformer、agent、reasoning 等高价值关键词），过滤掉明显无关的论文
> 2. **LLM 处理**：仅对通过预筛的论文（预计日均 10-20 篇）调用 Claude 做意译 + 分类 + 评分

### 2.3 Newsletter / 快讯聚合

| 来源 | 获取方式 | 状态 | 说明 |
|------|---------|------|------|
| The Rundown AI | 邮件订阅 → 转 RSS | ⏸ 待接入 | 日更质量最高的 AI 快讯 |
| Ben's Bites | 邮件 / RSS | ⏸ 待接入 | 工具 + 产品 + 小突破汇总 |

> **邮件 Newsletter 接入方案：** 对于仅支持邮件订阅的来源，使用 [kill-the-newsletter](https://kill-the-newsletter.com) 等服务将邮件订阅转为 RSS feed，统一走 RSS 抓取管线。

### 2.4 科技媒体

| 来源 | RSS / 地址 | 状态 | 说明 |
|------|-----------|------|------|
| MIT Technology Review (AI) | `https://www.technologyreview.com/topic/artificial-intelligence/feed/` | ✅ 已接入 | 深度报道 |
| WIRED AI | `https://www.wired.com/feed/tag/ai/latest/rss` | ✅ 已接入 | 科技文化视角 |
| Ars Technica (AI) | `https://arstechnica.com/tag/artificial-intelligence/feed/` | ✅ 已接入 | 技术深度分析 |

### 2.5 开源社区

| 来源 | RSS / 地址 | 状态 | 说明 |
|------|-----------|------|------|
| Hugging Face Blog | `https://huggingface.co/blog/feed.xml` | ✅ 已接入 | 开源模型、数据集、工具 |
| GitHub Trending (ML) | `https://github.com/trending?since=daily` | ⏸ 待接入 | 无 RSS，需爬取并过滤 ML 相关 |

### 2.6 社区讨论 / 信号源

| 来源 | RSS / 地址 | 状态 | 说明 |
|------|-----------|------|------|
| Reddit r/MachineLearning | `https://www.reddit.com/r/MachineLearning/.rss` | ✅ 已接入 | 一线研究者讨论，需自定义 User-Agent |
| Reddit r/LocalLLaMA | `https://www.reddit.com/r/LocalLLaMA/.rss` | ✅ 已接入 | 开源模型社区风向标，需自定义 User-Agent |
| Hacker News | 需通过 API 过滤 AI 相关 | ⏸ 待接入 | 技术社区早期信号 |

### 2.7 投融资 / 商业

| 来源 | 获取方式 | 状态 | 说明 |
|------|---------|------|------|
| CB Insights AI Newsletter | 邮件订阅 | ⏸ 待接入 | AI 投融资、市场格局 |
| The Information (AI) | 付费订阅 | ⏸ 待接入 | 信息密度极高，业内必读 |

### 2.8 中文来源

| 来源 | RSS / 地址 | 状态 | 说明 |
|------|-----------|------|------|
| 机器之心 | `https://www.jiqizhixin.com/rss` | ⏸ 待接入 | RSS 已停用，待替代方案 |
| 量子位 | 需爬取或关注公众号 | ⏸ 待接入 | 国内 AI 快讯 |

> **当前已接入来源统计：** 13 个 RSS 源（5 实验室 + 2 学术 + 3 媒体 + 1 开源 + 2 社区），覆盖英文主流 AI 信息源。中文来源、Newsletter、非 RSS 来源待后续接入。

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
| 前端 | Vite 8 + React 19 + TailwindCSS 4 + shadcn/ui | Vite 构建快，shadcn/ui 提供高质量基础组件 |
| 数据库 | SQLite | 零配置，单文件，个人工具足够 |
| 定时任务 | APScheduler | Python 原生，无需外部 cron |
| RSS 解析 | feedparser | Python RSS 解析标准库 |
| LLM (主) | OpenRouter (多 Key × 多模型轮换) | 聚合平台，免费模型丰富，Key+模型双重轮换最大化吞吐 |
| LLM (次) | Groq (llama-3.3-70b-versatile) | 免费额度，响应极快 |
| LLM (兜底) | Ollama (本地) | 所有云端额度耗尽时本地兜底 |
| 后端端口 | 9100 | `http://localhost:9100` |
| 前端端口 | 5173 | `http://localhost:5173`（Vite 默认） |

#### 4.2.1 LLM 多引擎策略

```
请求 → OpenRouter (Key × Model 轮换)
         │
         │  Key #1 + Model A → 429? → Key #2 + Model A → 429?
         │  → Key #1 + Model B → ... 遍历所有组合
         │
         ├─ 成功 → 返回结果
         │
         └─ 全部组合失败
              │
              └─ Groq API (自动重试 429)
                   │
                   ├─ 成功 → 返回结果
                   │
                   └─ 失败
                        │
                        └─ Ollama (本地兜底)
                             │
                             └─ 返回结果
```

**OpenRouter 多 Key × 多模型轮换：**
- 支持配置多个 API Key（逗号分隔），每个 Key 的速率限制独立
- 支持配置多个免费模型（逗号分隔），不同模型的限额独立
- 请求时轮换使用所有 (Key, Model) 组合（round-robin），某个组合 429 自动切换下一个
- 例：2 Key × 3 模型 = 6 种组合，大幅提高免费额度利用率

**批量合并 Prompt：** 10 篇文章合并为一次 API 调用，返回 JSON 数组，大幅减少 API 调用次数。批量失败时自动降级为逐篇处理。

**速率控制：**
- 并发数：1（串行处理，避免免费账户并发限制）
- 批次间隔：10 秒
- Key 切换间隔：2 秒
- 429 重试：最多 5 次，每次等待 15 秒
- 日额度耗尽检测：自动标记引擎为当日耗尽，跳过后续调用

**处理优先级：**
- 今天的文章优先处理，积压文章按时间由近到远
- 手动 fetch 运行时，积压处理自动暂停让路

**配置方式（.env）：**
```env
# OpenRouter API (主引擎，多 Key 逗号分隔)
OPENROUTER_API_KEYS=sk-or-v1-key1,sk-or-v1-key2
# 多模型逗号分隔，429 时自动轮换
OPENROUTER_MODELS=meta-llama/llama-3.3-70b-instruct:free,mistralai/mistral-small-3.1-24b-instruct:free,google/gemma-3-27b-it:free

# Groq API (次引擎，留空则跳过)
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# Gemini API (当前已禁用，留空则跳过)
GEMINI_API_KEY=

# Ollama (兜底引擎，本地运行)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

- 各引擎 API Key 为空时自动跳过，不报错
- 429 限流时自动解析 `retryDelay` 重试（最多 5 次），超限后降级到下一引擎
- 所有引擎使用统一的 prompt 模板，输出格式一致
- 成功日志记录使用的引擎和模型，便于追踪
- 启动时自动检测积压文章并在后台处理（最新优先）

**任务优先级（高 → 低）：**
1. **简报生成/更新** — 用户点击「生成/更新简报」时，积压处理自动暂停让路
2. **手动抓取** — 用户点击「立即刷新」时，积压处理自动暂停让路
3. **积压文章处理** — 后台自动进行，按时间由近到远处理，完成后前端自动停止轮询积压状态

### 4.3 抓取策略

| 触发方式 | 时间 | 说明 |
|---------|------|------|
| 定时抓取 | 每天 **06:00**、**10:00** 和 **17:00** | APScheduler 定时任务，06:00 早鸟抓取确保早起即看，10:00 + 17:00 覆盖日间信息高峰 |
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
│  ┌────────────────┬────────────────┬────────────────────┐ │
│  │    每日简报     │     信息流     │       收藏          │ │
│  └────────────────┴────────────────┴────────────────────┘ │
└────────────────────────────┬──────────────────────────────┘
                             │ HTTP API
┌────────────────────────────┴──────────────────────────────┐
│                   FastAPI 后端 (:9100)                      │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ REST API   │  │ 抓取调度器    │  │ LLM 多引擎         │  │
│  │ /api/*     │  │ 06+10:00+17  │  │ OpenRouter(轮换)→  │  │
│  │            │  │ + 手动刷新    │  │ Groq→Ollama        │  │
│  └─────┬──────┘  └──────┬───────┘  └──────┬────────────┘  │
│        │                │                 │               │
│  ┌─────┴────────────────┴─────────────────┴─────────────┐ │
│  │              SQLite 数据库 (WAL 模式)                  │ │
│  │  articles │ sources │ article_tags │ briefings │       │ │
│  │  seen_urls                                            │ │
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

-- URL 去重表 (独立于 articles，清理文章后仍保留，防止重复抓取)
CREATE TABLE seen_urls (
    url     TEXT PRIMARY KEY,
    seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**索引：**
```sql
CREATE INDEX idx_articles_url ON articles(url);
CREATE INDEX idx_articles_published ON articles(published_at);
CREATE INDEX idx_articles_source ON articles(source_id);
CREATE INDEX idx_briefings_date ON briefings(date);
```

### 4.6 内容处理策略

#### 4.6.1 HTML 清洗

RSS 原始内容含大量 HTML 噪声（script/style/svg/nav 等），直接送 LLM 浪费 Token。抓取入库时自动清洗：

- **白名单提取**：仅保留 `h1-h6`、`p`、`li` 标签的纯文本
- **噪声剔除**：`decompose()` 删除 script/style/svg/form/footer/nav/aside
- **链接保留**：`<a href>` 转为 Markdown `[text](url)` 格式，确保 LLM 能提取 `related_links`
- **嵌套去重**：跳过被父级白名单标签包含的子标签（如 `<li><p>` 不重复提取）
- **结构标记**：标题转 `#`/`##`，列表项转 `- `，辅助 LLM 理解文章层级
- **兜底机制**：白名单提取结果为空时回退到 `get_text()`，避免非标准 HTML 内容丢失

#### 4.6.2 中文意译

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

#### 4.6.3 媒体与链接提取

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
font-family: 'Geist Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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

1. **自动触发**：每次定时抓取（06:00/10:00/17:00）+ LLM 处理完成后，自动生成/更新当日简报；也可在页面手动点击 **「生成今日简报」**
2. 后端收集时间窗口内所有已处理文章（`title_zh IS NOT NULL AND importance > 0`）
3. 调用 LLM 选出 **头条 Top 10**，选取维度：
   - **技术突破性**：新架构、SOTA 结果、重大能力飞跃
   - **源头权威性**：官方实验室博客 > 主流媒体 > 社区帖子
   - **实操价值**：开源模型/代码 > 只有论文没有代码的研究
   - **行业影响力**：重要产品发布、重大融资、影响 AI 发展的政策变化
   - **破圈效应**：对非 AI 领域（医疗、法律、科学）产生重大影响的突破加分
   - **负向信号**：旧闻冗余（同一事件保留最权威来源）、低信息量、话题重复（优先多样性）
4. 剩余文章按 research / product / opensource / news 等 **分类归档**，无文章的分类不生成
5. 构建统计数据：各类别文章数量、来源分布
6. 简报存入数据库，后续可直接查看无需重新生成

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

| 优先级 | 功能 | 状态 | 说明 |
|--------|------|------|------|
| P0 | RSS 抓取 + 存储 + URL 去重 | ✅ 已完成 | 核心数据管线，含 seen_urls 持久去重 |
| P0 | LLM 多引擎意译 + 分类 + 评分 | ✅ 已完成 | OpenRouter 多 Key×模型轮换 + Groq + Ollama 兜底 |
| P0 | 每日简报生成 + 7天日期导航 | ✅ 已完成 | 核心阅读体验 |
| P0 | Dashboard 简报 + 信息流 + 收藏 | ✅ 已完成 | 3 Tab 布局 |
| P0 | 积压文章自动处理 | ✅ 已完成 | 启动时自动检测，后台批量处理，7天窗口 |
| P1 | 简报内搜索 + 分类筛选 | ✅ 已完成 | 关键词精筛已生成简报 |
| P1 | 已读/收藏管理 | ✅ 已完成 | 个人阅读状态 |
| P1 | 抓取进度实时显示 | ✅ 已完成 | FetchProgress 组件，实时反馈 |
| P1 | 月度自动清理 + 归档 | ✅ 已完成 | 启动时自检触发 |
| P2 | 云服务器部署 | 🔧 进行中 | 阿里云部署方案 |
| P3 | 非 RSS 来源抓取 | ⏸ 待开发 | GitHub Trending, HN 等 |
| P3 | 自定义关键词订阅/高亮 | ⏸ 待开发 | "transformer", "AGI" 等 |
| P4 | 趋势分析 / 热度图 | ⏸ 待开发 | 哪些话题在升温 |

---

## 5. 项目结构

```
AI Dynamics/
├── DESIGN.md                # 本文档
├── README.md                # 项目说明
├── API.md                   # REST API 文档
├── start.sh                 # 一键启动脚本 (Ollama + 后端 + 前端)
├── .env.example             # 环境变量模板
├── .env                     # 本地环境变量 (不入 git)
├── .gitignore
├── backend/
│   ├── pyproject.toml       # Python 项目配置 + 依赖管理
│   ├── main.py              # FastAPI 入口，生命周期管理
│   ├── config.py            # 配置 (端口、API Key、LLM 引擎设置，读取 .env)
│   ├── database.py          # SQLite 连接 + 初始化 (5 表 + WAL 模式)
│   ├── models.py            # Pydantic 响应模型
│   ├── seed_sources.py      # RSS 来源种子数据 (13 源)
│   ├── fetcher/
│   │   ├── __init__.py      # 抓取管线编排 (fetch → dedup → LLM → 入库)
│   │   ├── rss.py           # RSS 抓取器 (含 Reddit UA、图片提取、URL 去重)
│   │   ├── filter.py        # arXiv 关键词预筛过滤
│   │   ├── scheduler.py     # APScheduler 定时调度 (10:00 + 17:00)
│   │   └── cleanup.py       # 月度数据清理 + gzip 归档
│   ├── llm/
│   │   ├── engine.py        # LLM 多引擎管理 (OpenRouter→Groq→Ollama)
│   │   ├── processor.py     # LLM 统一处理 (意译 + 分类 + 评分 + 链接提取)
│   │   └── briefing.py      # LLM 简报生成器 (Top 10 + 分类)
│   └── api/
│       ├── articles.py      # 文章列表、筛选、搜索、已读/收藏
│       ├── sources.py       # RSS 来源管理
│       ├── briefings.py     # 简报生成、查询、最近状态
│       └── fetch.py         # 手动抓取触发 + 状态轮询
├── frontend/
│   ├── package.json
│   ├── vite.config.ts       # Vite 配置 (含路径别名)
│   ├── tsconfig.json        # TypeScript 配置
│   ├── src/
│   │   ├── App.tsx          # 主布局 (Header + 3 Tab 导航)
│   │   ├── pages/
│   │   │   ├── Briefing.tsx  # 每日简报 (默认首页)
│   │   │   ├── Feed.tsx      # 信息流 (分页 + 筛选 + 搜索)
│   │   │   └── Starred.tsx   # 收藏
│   │   ├── components/
│   │   │   ├── ArticleCard.tsx    # 文章卡片 (含封面图)
│   │   │   ├── CategoryBadge.tsx  # 分类标签 (7 种配色)
│   │   │   ├── DateNavigator.tsx  # 7天日期选择器
│   │   │   ├── SearchBar.tsx      # 搜索输入框
│   │   │   ├── FetchProgress.tsx  # 实时抓取/LLM 处理进度
│   │   │   ├── Toast.tsx          # Toast 通知
│   │   │   ├── ErrorBoundary.tsx  # 错误边界
│   │   │   ├── Skeleton.tsx       # 加载骨架屏
│   │   │   └── ui/button.tsx      # shadcn/ui 按钮组件
│   │   └── lib/
│   │       ├── api.ts        # API 客户端 (fetch, articles, briefings)
│   │       ├── types.ts      # TypeScript 类型定义
│   │       ├── constants.ts  # 分类映射、颜色常量
│   │       └── utils.ts      # 工具函数
│   └── ...
└── data/
    ├── ai_dynamics.db       # SQLite 数据库文件 (不入 git)
    └── archive/             # 月度归档 (不入 git)
        └── 2026-08.json.gz
```

---

## 6. 数据来源覆盖矩阵

已接入来源（✅）与待接入来源（⏸）：

```
                    研究  产品  开源  新闻  投融资  社区   状态
OpenAI               ·    ✓     ·    ·     ·      ·     ✅
DeepMind             ✓    ✓     ·    ·     ·      ·     ✅
Google AI Blog       ·    ✓     ·    ·     ·      ·     ✅
Eng. at Meta         ✓    ✓     ✓    ·     ·      ·     ✅
Microsoft AI         ·    ✓     ·    ·     ·      ·     ✅
arXiv                ✓    ·     ·    ·     ·      ·     ✅
MarkTechPost         ✓    ✓     ·    ✓     ·      ·     ✅
MIT Tech Review      ✓    ·     ·    ✓     ·      ·     ✅
WIRED AI             ·    ·     ·    ✓     ·      ·     ✅
Ars Technica         ✓    ·     ·    ✓     ·      ·     ✅
Hugging Face         ✓    ·     ✓    ·     ·      ·     ✅
Reddit ML            ✓    ·     ✓    ·     ·      ✓     ✅
Reddit LocalLLaMA    ·    ·     ✓    ·     ·      ✓     ✅
─────────────────────────────────────────────────────────────
Anthropic            ✓    ✓     ·    ·     ·      ·     ⏸
Papers w/ Code       ✓    ·     ✓    ·     ·      ·     ⏸
The Rundown AI       ✓    ✓     ✓    ✓     ·      ·     ⏸
Ben's Bites          ·    ✓     ✓    ✓     ·      ·     ⏸
GitHub Trending      ·    ·     ✓    ·     ·      ·     ⏸
Hacker News          ·    ✓     ✓    ✓     ·      ✓     ⏸
CB Insights          ·    ·     ·    ·     ✓      ·     ⏸
The Information      ·    ✓     ·    ✓     ✓      ·     ⏸
机器之心              ✓    ✓     ✓    ✓     ✓      ·     ⏸
量子位                ·    ✓     ·    ✓     ·      ·     ⏸
```

---

## 7. 实现计划

### 阶段 1 — 后端基础 + 数据管线 ✅
1. ✅ 初始化 Python 项目（pyproject.toml、.env 配置）
2. ✅ 实现 SQLite 数据库初始化 + 全部数据模型（sources、articles、article_tags、briefings、seen_urls）
3. ✅ 实现 RSS 抓取器（feedparser + httpx）+ arXiv 预筛过滤器
4. ✅ 导入 13 个 RSS 来源种子数据
5. ✅ 实现定时调度（APScheduler，10:00 + 17:00）

### 阶段 2 — LLM 处理 ✅
6. ✅ 实现多引擎 LLM 处理器（OpenRouter 多 Key×模型轮换 → Groq → Ollama）
7. ✅ 批量合并处理（10 篇/批次）+ 速率控制 + 日额度耗尽检测
8. ✅ 积压文章自动处理（启动时检测，后台批量，7天窗口）

### 阶段 3 — 简报系统 ✅
9. ✅ 实现简报生成 API + LLM 简报生成器（选头条 Top 10 + 分类归档）
10. ✅ 实现简报查询接口（JOIN articles 返回完整数据）
11. ✅ 实现简报内搜索 API

### 阶段 4 — 前端 Dashboard ✅
12. ✅ 初始化 React 19 + TailwindCSS 4 + shadcn/ui 项目
13. ✅ 实现每日简报页面（7天日期导航 + 生成按钮 + 头条 + 分类浏览 + 搜索）
14. ✅ 实现信息流页面（时间线 + 分页 + 分类筛选 + 搜索）
15. ✅ 实现收藏页面 + 已读/收藏管理
16. ✅ 实现抓取进度实时显示（FetchProgress 组件）

### 阶段 5 — 数据管理 + 部署 ✅ / 🔧
17. ✅ 实现月度自动清理 + 归档备份（cleanup.py，启动时自检）
18. ✅ 一键启动脚本（start.sh）
19. 🔧 云服务器部署（阿里云）

### 后续规划
20. ⏸ 接入更多数据来源（Anthropic、Newsletter、中文来源等）
21. ⏸ 非 RSS 来源抓取（GitHub Trending、HN 等）
22. ⏸ 自定义关键词订阅/高亮
23. ⏸ 趋势分析 / 热度图
24. ⏸ LLM 调用质量监控（记录各引擎/模型的成功率、乱码率、429 频次，为模型池优化提供数据，等模型池扩大或使用付费模型时实施）
25. ⏸ 数据库实时备份（Litestream → 阿里云 OSS，当数据变为不可重建时实施；当前数据可重新抓取，简单 cron + scp 即可满足备份需求）
