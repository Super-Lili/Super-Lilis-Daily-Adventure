# 🌸 Super-Lili 运行结构（2026-05 版）

> 工程说明文档 — 记录系统整体架构、数据流与关键文件职责。

---

## 触发层：GitHub Actions

| Workflow | 触发时间（北京时间） | 触发条件 |
|----------|-------------------|---------|
| `lili_daily.yml` | 周一~周六 × 08:05 / 14:05 / 20:05 | 当日日记不存在时运行 |
| `lili_weekly_evolution.yml` | 周日 × 08:05 / 14:05 / 20:05 | 当周进化日记不存在时运行 |
| `lili_issues.yml` | Issue 事件实时触发 + 每日兜底 | 有未回复 Issue 时运行 |

每个任务设置 3 个备用时间槽，防止单次 API 临时不可用。

---

## 三条主线

### 1. 每日工作 — `super_lili_brain.py`

```
读取灵魂文件
  lili_soul.py          ← 价值观 + 人格
  lili_engineering.py   ← 工程规范（每周进化更新）
  lili_blindspot.py     ← 本周方向（每周进化更新）
  lili_memory.py        ← 已建工具 + 已写话题（防重复）
       │
       ▼
构建 Prompt → Gemini API（含 Google Search 实时信源）
       │
       ▼
生成今日工具 + 日记
  02_Toolbox/<Category>/<date>_<ToolName>/main.py
  01_Work_Log/<date>-Diary.md
       │
       ▼
两维质量评分
  Engineering (1-5) + Warmth (1-5)
  combined = (eng + warm) / 2 ≥ 3.0 → passed
       │
       ▼
追加到 tool_quality_ledger.jsonl
       │
       ▼
generate_site.py → 重建 docs/index.html → GitHub Pages
```

### 2. 每周进化 — `super_lili_weekly_evolution.py`

```
读取本周输入
  7 天日记 (01_Work_Log/)
  已建工具列表
  tool_quality_ledger.jsonl (最近 14 条评分)
  lili_soul.py
  GitHub Issues（用户反馈）
  top 工具源码
       │
       ▼
构建进化 Prompt → Gemini API
       │
       ▼
生成 4 个进化文件
  src/lili_soul.py          ← 灵魂升级
  src/lili_engineering.py   ← 工程规范更新
  src/lili_blindspot.py     ← 下周盲点 + 方向
  docs/EVOLUTION_LOG.md     ← 进化日志追加
       │
       ▼
generate_site.py → 重建 docs/index.html → GitHub Pages
```

### 3. Issue 回复 — `lili_responds.py`

```
扫描无 lili-responded 标签的 open Issues
       │
       ▼
分类 Issue 类型
  bug_report / feature_request / question / appreciation / general
       │
       ▼
构建回复 Prompt（含 lili_soul + lili_memory 上下文）→ Gemini
       │
       ▼
发布双语评论（英文 + 中文）
添加 lili-responded 标签
```

---

## 质量闭环

```
每日 brain.py
  → 工具质量评分 → tool_quality_ledger.jsonl
                              │
每周 weekly_evolution.py      │
  ← 读取最近 14 条评分 ←──────┘
  → 生成 lili_engineering.py（针对性工程规范）
                              │
次周 brain.py ←───────────────┘
  读取新规范 → 工程能力提升
```

---

## 关键文件职责

| 文件 | 性质 | 更新方式 |
|------|------|---------|
| `src/lili_soul.py` | 莉莉的价值观 + 人格核心 | 每周进化自动更新 |
| `src/lili_engineering.py` | 工程规范 + 反模式清单 | 每周进化自动更新 |
| `src/lili_blindspot.py` | 本周盲点分析 + 下周方向 | 每周进化自动更新 |
| `src/lili_memory.py` | 已建工具 + 已写话题（防重复逻辑） | 每次 brain.py 运行后更新 |
| `src/lili_responds.py` | Issue 回复引擎 | 静态代码 |
| `data/tool_quality_ledger.jsonl` | 每个工具的质量评分历史 | 每次 brain.py 运行后追加 |
| `docs/EVOLUTION_LOG.md` | 每周进化日志 | 每次 weekly_evolution.py 追加 |
| `docs/generate_site.py` | 静态站点生成器 | 每次运行后自动调用 |
| `docs/index.html` | GitHub Pages 首页 | 自动生成，不手动编辑 |

---

## Gemini API 使用说明

- **模型优先级**：`gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.0-flash-lite`
- **重试策略**：每个模型最多 3 次，退避间隔 15s / 30s / 60s
- **Google Search**：brain.py 使用 grounding，为工具提供实时信源
- **免费额度**：每日 1-2 次调用，远低于配额上限，不存在耗尽风险

---

*本文档由开发者手动维护，如系统结构有重大变更请同步更新。*
