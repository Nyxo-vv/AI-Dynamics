# AI Dynamics

全球 AI 行业动态追踪工具 — 自动聚合关键信息源，高效掌握研究突破、产品发布、开源进展、投融资、政策法规等行业动态。

## 功能特性

- **RSS 自动抓取** — 聚合 OpenAI、DeepMind、arXiv、Hugging Face、Reddit 等 13 个信息源，每日三次定时抓取（06:00 / 10:00 / 17:00）或手动刷新
- **LLM 智能处理** — 多引擎策略（OpenRouter 多 Key×模型轮换 → Groq → Ollama），自动中文意译、分类（7 种标签）、重要性评分（1-5）
- **批量合并 Prompt** — 10 篇文章合并为一次 API 调用，大幅减少调用次数和 Token 消耗
- **HTML 清洗** — 白名单提取 h/p/li 纯文本，保留链接为 Markdown 格式，剔除 script/style/svg 等噪声
- **每日简报** — LLM 从当日文章中按技术突破性、源头权威性、实操价值等维度选出 Top 10 头条 + 分类浏览 + 数据统计
- **信息流浏览** — 按时间线查看全部文章，支持分类筛选和关键词搜索
- **收藏管理** — 星标感兴趣的文章
- **月度自动清理** — 超过一个月的数据自动归档压缩，数据库保持轻量

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12 + FastAPI + SQLite (aiosqlite) |
| 前端 | Vite + React 19 + TypeScript + TailwindCSS + shadcn/ui |
| LLM | OpenRouter (多 Key×模型轮换) / Groq (llama-3.3-70b) / Ollama |
| 定时任务 | APScheduler |
| RSS 解析 | feedparser + httpx + BeautifulSoup |

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 20+
- [Ollama](https://ollama.com)（可选，作为 LLM 兜底引擎）

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd "AI Dynamics"

# 后端依赖
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt  # 或 pip install -e backend/

# 前端依赖
cd frontend && npm install && cd ..

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key
```

### 配置 `.env`

```env
# OpenRouter API（主引擎，多 Key 逗号分隔）
OPENROUTER_API_KEYS=sk-or-v1-key1,sk-or-v1-key2
# 多模型逗号分隔，429 时自动轮换
OPENROUTER_MODELS=meta-llama/llama-3.3-70b-instruct:free,mistralai/mistral-small-3.1-24b-instruct:free,google/gemma-3-27b-it:free

# Groq API（次引擎，留空则跳过）
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Ollama（兜底引擎，本地运行，云服务器可留空）
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.2:3b
```

### 启动

```bash
# 一键启动（Ollama + 后端 + 前端）
./start.sh

# 或分别启动：
ollama serve                                          # Terminal 1
cd backend && source ../.venv/bin/activate && python3.12 main.py  # Terminal 2
cd frontend && npm run dev                            # Terminal 3
```

访问 http://localhost:5173 打开 Dashboard。

## 项目结构

```
AI Dynamics/
├── backend/
│   ├── main.py              # FastAPI 入口 (port 9100)
│   ├── config.py            # 环境配置
│   ├── database.py          # SQLite 初始化（5 张表 + WAL 模式）
│   ├── models.py            # Pydantic 模型
│   ├── seed_sources.py      # RSS 源种子数据
│   ├── fetcher/
│   │   ├── rss.py           # RSS 抓取器
│   │   ├── filter.py        # arXiv 关键词预筛
│   │   ├── scheduler.py     # 定时调度
│   │   └── cleanup.py       # 月度清理 + 归档
│   ├── llm/
│   │   ├── engine.py        # 多引擎 LLM（OpenRouter→Groq→Ollama）
│   │   ├── processor.py     # 文章处理（批量/单篇）
│   │   └── briefing.py      # 简报生成器
│   └── api/
│       ├── articles.py      # 文章 API
│       ├── sources.py       # 来源 API
│       ├── briefings.py     # 简报 API
│       └── fetch.py         # 抓取控制 API
├── frontend/
│   └── src/
│       ├── pages/           # Briefing / Feed / Starred
│       ├── components/      # ArticleCard, DateNavigator, etc.
│       └── lib/             # api.ts, types.ts, constants.ts
├── data/
│   ├── ai_dynamics.db       # SQLite 数据库
│   └── archive/             # 月度归档 (.json.gz)
├── start.sh                 # 一键启动脚本
├── DESIGN.md                # 设计文档
├── API.md                   # REST API 文档
└── .env                     # 环境变量（不入 git）
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/articles` | 文章列表（分页/筛选/搜索） |
| `PATCH` | `/api/articles/:id` | 更新已读/收藏状态 |
| `GET` | `/api/sources` | 来源列表 |
| `POST` | `/api/fetch/run` | 手动触发抓取 |
| `GET` | `/api/fetch/status` | 抓取进度 |
| `POST` | `/api/briefings/generate` | 生成简报 |
| `GET` | `/api/briefings/:date` | 获取简报 |
| `GET` | `/api/briefings/recent` | 最近 N 天简报状态 |
| `GET` | `/api/briefings/search` | 搜索简报文章 |

## 信息分类

| 标签 | 说明 | 典型来源 |
|------|------|---------|
| `research` | 研究突破 | arXiv, DeepMind, Papers with Code |
| `product` | 产品发布 | OpenAI, Google, Anthropic |
| `opensource` | 开源动态 | Hugging Face, GitHub, r/LocalLLaMA |
| `news` | 行业新闻 | MIT Tech Review, WIRED, Ars Technica |
| `funding` | 投融资 | CB Insights, The Information |
| `policy` | 政策法规 | 各媒体 |
| `community` | 社区讨论 | Reddit, Hacker News |

## Help Wanted

This is a personal side project and I'm running into a few issues I haven't been able to solve yet. If you have experience with any of these, I'd really appreciate your help!

### 1. Some RSS sources are dead

Two sources have broken RSS feeds and are currently disabled:

| Source | Issue |
|--------|-------|
| Anthropic (`anthropic.com/news/rss`) | RSS feed no longer exists |
| 机器之心 (`jiqizhixin.com/rss`) | Redirects to Feishu login page |

**What I need**: Alternative RSS feeds or reliable ways to get updates from these sources. Self-hosted RSSHub? Other aggregators?

### 2. No dark mode

The UI is currently light-only. Would love help implementing a proper dark mode with TailwindCSS + shadcn/ui theming.

### 3. No tests

Zero test coverage. The codebase could use:
- Unit tests for the LLM processor (especially batch prompt parsing and error handling)
- Integration tests for the fetch pipeline
- Frontend component tests

---

If any of these interest you, feel free to open an issue or PR. Thanks!

## License

MIT
