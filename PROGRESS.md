# AI Dynamics 开发进度标注

> 最后更新：2026-03-18 09:20 | 供后续开发会话参考

## 实现计划

完整实现计划见：`~/.claude/plans/dapper-snacking-cerf.md`
设计文档：`DESIGN.md`（v0.3）

共 11 步（Step 0 - Step 10），按依赖顺序实现。

---

## 已完成

### Step 0: 项目初始化 ✅
- git init、`.gitignore`、`.env.example`、`.env`
- 目录骨架：`backend/fetcher/`、`backend/llm/`、`backend/api/`、`data/archive/`
- 各包的 `__init__.py`
- Ollama 已安装，`llama3.1` 模型已拉取（4.9GB）
- Commit: `30814da`

### Step 1: 后端骨架 ✅
- `backend/pyproject.toml` — 依赖声明
- `backend/config.py` — pydantic-settings 读取 .env（Gemini/Ollama 配置）
- `backend/database.py` — aiosqlite，4 张表（sources, articles, article_tags, briefings）+ 索引 + WAL 模式
- `backend/models.py` — 全部 Pydantic 模型
- `backend/main.py` — FastAPI 入口，CORS（localhost:5173），health 端点，port 9100
- Python 虚拟环境：`.venv/`（python3.12），依赖已安装
- 数据库已初始化：`data/ai_dynamics.db`（4 张表已验证）
- Commit: `92f1899`

---

### Step 2: 种子数据 + RSS 抓取器 ✅
- `backend/seed_sources.py` — 15 个 RSS 源定义，seed_sources() 函数，已测试通过
- `backend/fetcher/rss.py` — httpx + feedparser 抓取器
  - 自定义 User-Agent（Reddit 正常 200）
  - 提取 cover_image（media:content / enclosure / 正文首图）
  - 提取 images（BeautifulSoup 过滤 icon/logo/tracker）
  - 语言检测（CJK 字符比例启发式）
  - URL 去重（INSERT 前查询）
  - `fetch_single_source()` + `fetch_all_sources()` 两个入口
- `backend/fetcher/filter.py` — arXiv 关键词预筛（60+ 高价值关键词正则）
- 全量抓取测试：12/15 源成功，共 2530 篇文章入库
- **已知问题**：Anthropic、Meta AI、机器之心 RSS 已失效，暂时禁用（enabled=0）

---

### Step 3: LLM 三引擎 + 文章处理器 ✅
- `backend/llm/engine.py` — Gemini(主) → Groq(备) → Ollama(兜底) 三引擎，统一 `generate()` / `generate_json()` 接口，429 自动重试
- `backend/llm/processor.py` — 批量合并 Prompt（5 篇一组，API 调用减少 80%）+ 单篇处理两种模式
  - 低价值文章预筛（标题正则匹配跳过，不调用 LLM）
  - 相似文章去重（标题相似度 ≥ 0.8 复用已有结果）
  - 批量处理：`BATCH_PROMPT` 合并多篇文章到单次请求，返回 JSON 数组
  - 批量失败时自动降级为逐篇处理
- `backend/fetcher/__init__.py` — 完整管线 `run_pipeline()`：抓取 → 去重 → 预筛 → LLM 处理 → 入库
- 已测试：Groq llama-3.3-70b 批量处理 10 篇文章成功（2 batch × 5 篇，每批约 4 秒）

### Step 4: 调度 + API + 清理 ✅
- `backend/fetcher/scheduler.py` — APScheduler 10:00 + 17:00 定时抓取
- `backend/fetcher/cleanup.py` — 启动时自检月度清理 + JSON.gz 归档（已验证：自动归档 2026-02 数据）
- `backend/api/articles.py` — 文章列表/分页/筛选/搜索/已读/收藏
- `backend/api/sources.py` — 来源列表/启用禁用
- `backend/api/briefings.py` — 占位路由
- `backend/api/fetch.py` — `POST /api/fetch/run` + `GET /api/fetch/status`
- `backend/main.py` — 集成所有路由，启动时自动清理+调度器

### Step 5: 简报生成器 ✅
- `backend/llm/briefing.py` — 时间窗口查询（前日09:00~当日09:00）→ LLM 选 Top 10 头条 → 分类归档 → 存 briefings 表（upsert）
- `backend/llm/briefing.py:get_briefing_with_articles()` — 查询简报 + JOIN 完整文章数据
- `backend/api/briefings.py` — 4 个 API 端点：
  - `POST /api/briefings/generate` — 生成指定日期简报
  - `GET /api/briefings/recent?days=7` — 最近 N 天简报状态列表
  - `GET /api/briefings/search?q=&date=` — 搜索简报文章（支持跨日期）
  - `GET /api/briefings/{date}` — 获取完整简报（含文章详情）
- 已测试：3 篇已处理文章成功生成简报，headlines/sections/stats/articles 查询正常
- **注意**：修复了 published_at 时区格式（`T` + `+00:00`）与 SQLite 字符串比较的兼容问题

### Step 6: 前端项目初始化 ✅
- Vite 8 + React 19 + TypeScript，端口 5173
- TailwindCSS v4（PostCSS 模式，因 @tailwindcss/vite 不兼容 Vite 8）
- shadcn/ui 初始化（Button 组件 + cn() 工具函数）
- `src/lib/types.ts` — 全部 TypeScript 类型定义
- `src/lib/api.ts` — API 客户端（briefings/articles/sources/fetch）
- `src/lib/constants.ts` — 分类标签/颜色/排序常量
- `src/index.css` — DESIGN.md 色彩规范 + shadcn theme tokens
- `src/App.tsx` — Header（AI Daily + Tab 导航 + 立即刷新按钮）+ 3 个页面占位
- `tsconfig` + `vite.config.ts` — `@/` path alias
- 构建通过（tsc + vite build 零错误零警告）

### Step 7: 共享组件 ✅
- `src/components/CategoryBadge.tsx` — 分类标签 pill（7 种分类配色，支持 count/active/onClick）
- `src/components/ArticleCard.tsx` — 文章卡片（标准卡片模式 + compact 紧凑列表模式，收藏/外链按钮，hover 蓝色左边框）
- `src/components/DateNavigator.tsx` — 7 天日期导航（前后翻页，生成状态指示点，今天高亮）
- `src/components/SearchBar.tsx` — 搜索栏（回车搜索，一键清空）

### Step 8: 简报页面（默认首页）✅
- `src/pages/Briefing.tsx` — 完整简报页面：
  - DateNavigator 日期导航（7 天，状态指示点）
  - 生成按钮（未生成时显示，调用 POST /api/briefings/generate）
  - SearchBar 搜索（调用 /api/briefings/search，支持按日期筛选）
  - 头条 Top N 卡片 Grid（3 列响应式）
  - 分类浏览（CategoryBadge Tab 切换 + compact 文章列表，超 8 条折叠）
  - 数据统计面板（文章总数、头条数、分类数、来源数）
  - 空状态提示
- 已集成到 App.tsx，构建通过

### Step 9: 信息流 + 收藏页面 ✅
- `src/pages/Feed.tsx` — 信息流页面：
  - 搜索栏（标题、摘要全文搜索）
  - 7 种分类标签筛选（CategoryBadge Tab）
  - 文章卡片列表（标准模式，带收藏/外链按钮）
  - 分页导航（上一页/下一页，页码显示）
- `src/pages/Starred.tsx` — 收藏页面：
  - 搜索栏
  - 收藏文章列表，取消收藏时实时移除
  - 空状态提示（星标图标 + 引导文案）
- 修正 API 客户端参数名（`category` / `is_starred`），添加 `pages` 字段到返回类型
- 已集成到 App.tsx，构建通过

### Step 10: 收尾 ✅
- `src/components/ErrorBoundary.tsx` — 错误边界（捕获渲染错误，显示重试按钮）
- `src/components/Toast.tsx` — 轻量 Toast 通知系统（success/error/info，4 秒自动消失，Context API）
- `src/components/FetchProgress.tsx` — 抓取进度条（2 秒轮询 /api/fetch/status，进度百分比 + 新文章数）
- `src/components/Skeleton.tsx` — 骨架屏（CardSkeleton、CardGridSkeleton、ListSkeleton）
- App.tsx 集成：ToastProvider 包裹全局，ErrorBoundary 包裹页面内容，FetchProgress 在 header 下方显示
- 简报页面 / 信息流页面 loading 状态改用骨架屏替代 spinner
- 抓取按钮点击后触发 Toast 通知 + 进度条，完成后 Toast 提示
- 最终构建：tsc + vite build 零错误，JS 252KB (gzip 79KB)，CSS 35KB (gzip 7KB)

---

## 全部 Step 0-10 已完成 ✅

### 项目文件总览

**后端 (backend/):**
- `main.py` — FastAPI 入口，lifespan 管理
- `config.py` — 配置（Gemini/Ollama/DB）
- `database.py` — SQLite 初始化 + 4 张表
- `models.py` — Pydantic 模型
- `seed_sources.py` — 15 个 RSS 源
- `fetcher/rss.py` — RSS 抓取器
- `fetcher/filter.py` — arXiv 预筛
- `fetcher/scheduler.py` — APScheduler 定时
- `fetcher/cleanup.py` — 月度清理归档
- `fetcher/__init__.py` — 管线入口
- `llm/engine.py` — Gemini + Ollama 双引擎
- `llm/processor.py` — 文章 LLM 处理
- `llm/briefing.py` — 简报生成器
- `api/articles.py` — 文章 API
- `api/sources.py` — 来源 API
- `api/briefings.py` — 简报 API
- `api/fetch.py` — 抓取 API

**前端 (frontend/src/):**
- `App.tsx` — 主布局（Header + Tab + 3 页面）
- `pages/Briefing.tsx` — 简报页面
- `pages/Feed.tsx` — 信息流页面
- `pages/Starred.tsx` — 收藏页面
- `components/` — ArticleCard, CategoryBadge, DateNavigator, SearchBar, ErrorBoundary, Toast, FetchProgress, Skeleton
- `lib/` — api.ts, types.ts, constants.ts, utils.ts

---

## 已知问题

1. ~~残留文件 `backend/data/ai_dynamics.db`~~ — 已删除 ✅
2. **Step 2-4 文件均未 commit**：seed_sources.py、fetcher/*.py、llm/*.py、api/*.py、main.py 更新后均未加入 git。
3. ~~**Ollama serve 需手动启动**~~ — `start.sh` 一键启动已包含 Ollama。
4. **3 个 RSS 源失效**：Anthropic、Meta AI 的官方 RSS 已下线（RSSHub 公共实例也被限流）；机器之心 RSS 重定向到飞书登录页。这 3 个源已禁用（enabled=0），后续可自建 RSSHub 或找替代源。
5. ~~**数据库已有数据**~~ — 已处理约 730 篇文章，剩余约 1811 篇积压待处理（API 配额限制）。
6. **Gemini 免费额度已耗尽**：当前 Gemini Free Tier 日配额用完，自动降级到 Groq。Groq 日配额 100K tokens 也可能触顶。Ollama llama3.2:3b 中文翻译质量极差（乱码），不建议作为生产兜底。
7. **简报生成后页面不显示** — 已修复：`generateBriefing` 返回数据缺少 `articles` 字段，改为生成后自动调用 `getBriefing` 拉取完整数据。
8. **`_save_llm_result` importance=None 崩溃** — 已修复：`int(None)` → `int(importance or 0)`。

## 2026-03-18 本次会话变更

- **修复** `processor.py:_save_llm_result()` — `importance` 为 None 时 `int()` 崩溃
- **修复** `Briefing.tsx:handleGenerate()` — 生成后重新拉取完整简报数据（含 articles map）
- **清理** 6 篇 Ollama 乱码翻译，用 Groq 重新处理
- **重新生成** 3/13、3/14、3/15、3/16 四天简报
- **积压清理** 跑了 ~4.5 小时处理 397 篇，因 Gemini+Groq 配额耗尽停止
- **积压清理脚本** `backend/clear_backlog.py` — 配额恢复后可继续运行

## 环境信息

- Python: 3.12.13（`python3.12`，Homebrew 安装）
- 虚拟环境: `.venv/`（`source .venv/bin/activate`）
- Node.js: 20.20.1 / npm: 10.8.2
- Ollama: 已安装，llama3.2:3b 已拉取
- Gemini API Key: 已配置（免费版，日配额有限）
- Groq API Key: 已配置（on_demand tier，日 100K tokens）
- 后端端口: 9100，前端端口: 5173

## 启动命令

```bash
# 一键启动（Ollama + 后端 + 前端）
./start.sh

# 或分别启动：
# Terminal 1: Ollama
ollama serve

# Terminal 2: Backend
cd backend && source ../.venv/bin/activate && python3.12 main.py

# Terminal 3: Frontend
cd frontend && npm run dev

# 清理积压文章（API 配额恢复后运行）
cd backend && ../.venv/bin/python3.12 clear_backlog.py
```
