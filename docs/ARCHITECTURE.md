# 🌸 Super-Lili 运行结构（2026-07 版）

> 工程说明文档 — 记录系统整体架构、数据流与关键文件职责。
> 上次大改：2026-07-03/04（去 Gemini、Qwen+DeepSeek 双引擎、brain 拆模块、Mode 3 浏览器验证）。

---

## 触发层：GitHub Actions

| Workflow | 触发时间（北京时间） | 触发条件 |
|----------|-------------------|---------|
| `lili_daily.yml` | 周一~周六 × 08:30 / 14:30 / 20:30 | 当日 `02_Toolbox` 无当日工具目录时运行（任一时间槽成功后跳过余下） |
| `lili_weekly_evolution.yml` | 周日 | 当周进化未完成时运行 |
| `lili_issues.yml` | Issue 事件实时触发 + 每日兜底 | 有未回复 Issue 时运行 |

3 个备用时间槽防止单次 API 临时不可用。跳过判断读的是**工具目录**（不是日记），所以"休息日日记已存在"不会挡住后续时间槽重跑。

---

## 大模型分工（2026-07 起，Gemini 已彻底移除）

两个 API Key（`QWEN_API_KEY` + `DEEPSEEK_API_KEY`），四种模型，每个阶段用最合适的：

| 阶段 | 模型 | 为什么 |
|------|------|--------|
| **SCOUT 侦察** | `qwen-plus`（联网搜索） | DashScope 原生 web search，找真实摩擦点 |
| **SPEC 设计** | `deepseek-reasoner`（R1） | 架构设计需要推理链；失败自动降级 `deepseek-v4-pro` |
| **BUILD 构建** | `deepseek-v4-pro` | 当前最强代码生成 |
| **Critic 审查** | `qwen3.7-max` | **独立于 BUILD 模型**，打破自我评分回音壁 |
| **质量评分** | `deepseek-v4-pro` | 两维打分 |
| **周进化 / Issue 回复** | `deepseek-v4-pro` | 分析与写作 |

**跨厂商后备链**（`call_gemini_simple`）：`deepseek-reasoner → deepseek-v4-pro → qwen3.7-max`。
空响应会重试（DeepSeek 空响应是瞬时故障，不等于配额耗尽），单一厂商宕机不会导致 BUILD 全灭。

---

## 代码结构（2026-07-03 拆分：原 2700 行上帝文件 → 4 模块）

```
src/super_lili_brain.py   ← 薄入口层（49行），re-export 公共 API，Actions 入口不变
  ├── lili_llm.py         ← Qwen + DeepSeek 客户端和调用函数
  ├── lili_prompts.py     ← 上下文数据、轮换、情景记忆、三阶段 prompt 构建
  ├── lili_validators.py  ← validate_spec / validate_tool 检查链、解析器、浏览器验证、来源核验
  └── lili_pipeline.py    ← Issue 委托、工具/日记/README 持久化、evolve() 五阶段编排
```

修 bug 定位：搜索问题→`lili_llm.py`；prompt 规则→`lili_prompts.py`；验证门槛→`lili_validators.py`；流程编排→`lili_pipeline.py`。

---

## 主线 1 — 每日工作（ReAct 五阶段）

`lili_pipeline.py::evolve()` 编排：

```
读取灵魂文件
  lili_soul.py / lili_engineering.py / lili_blindspot.py / lili_editor.py / lili_memory.py
       │
       ▼
PHASE 1 SCOUT  — Qwen 联网搜索，找真实摩擦点 + 写日记（失败降级 DeepSeek）
       ▼
PHASE 2 SPEC   — DeepSeek-R1 设计工具架构 → validate_spec() 机械验证（先验证再建造）
       ▼
PHASE 3 BUILD  — DeepSeek-v4-pro 写代码，最多 5 次重试，每次带具体失败原因
       ▼
PHASE 4 EVALUATE — validate_tool() 在 BUILD 循环内运行（见下）
       ▼
PHASE 5 REFLECT — 存工具 + 双语日记 + add_tool() 记忆 + 追加质量账本 + 重建网站
```

5 次 BUILD 全失败 → 写"今天莉莉在休息"日记 + 失败原因，不发布半成品。

### validate_spec() — BUILD 前的机械门

- INPUT_MODEL 与 OUTPUT_MODEL 必须结构不同（真实转换）
- ALGORITHMIC_DEPTH 必须是**具体分步机械过程**（含 split/count/rank 等计算动词），不是愿景
- **自包含检查**：拒绝承诺外部语料库/数据库/预训练模型的 spec（工具是单文件，无外部数据）
- Q1/Q2/Q3、TEST_INPUT 长度门槛
- 失败原因精确回传给 R1 重试（最多 4 次）

### validate_tool() — BUILD 内的验证链

1. `ast.parse` 语法检查
2. 浏览器兼容（禁用库检测）
3. `from main import process` 导入检查（防崩溃）
4. 运行 `test_main.py`
5. 输出质量（Mode 1/2 判文本；Mode 3 判 HTML 长度 + 硬编码/未渲染模板检测）
6. **Mode 3 浏览器 ground-truth 验证**（见下）
7. 硬编码检测
8. 两维质量评分（Engineering + Warmth）
9. **Critic 审查**（qwen3.7-max，REJECT / MINOR / PASS 三档）
10. Win Rate 对比同类前作

---

## 三种工具模式与验证不对等（核心设计）

| 模式 | 返回 | 怎么验证 |
|------|------|---------|
| Mode 1 | `process(text)` → 纯文本 | **真实执行**，Critic 判真实输出 |
| Mode 2 | `process(text)` → SVG 字符串 | 真实执行 |
| Mode 3 | `process(text)` → 完整 HTML 页面 | **无头浏览器真实运行**（Playwright） |

**分流原则**（2026-07-03）：分析/计算型工具（粘贴文本→给洞察）走 Mode 1/2（可真实验证）；
Mode 3 只留给真正的交互/环境/生成型概念（实时画布、环境生成物、就地编辑器）。

**Mode 3 浏览器验证**（`_browser_interactivity_check`）：无头 Chromium 加载工具 HTML → 填入测试输入 →
触发 input/change/click 事件 → 断言 DOM 真的变了。这是对"静态假工具"的地面真值，取代"让 LLM 猜"。
**Fail-open**：Playwright 不可用/崩溃时回退 Critic，浏览器抖动绝不造成误判休息日；只有"跑通但 DOM 没变"才硬拒。

---

## 主线 2 — 每周进化 `super_lili_weekly_evolution.py`

```
读取本周输入（7 天日记 + 已建工具 + 质量账本最近 14 条 + soul + Issues + top 工具源码）
       │  DeepSeek-v4-pro
       ▼
生成进化文件
  lili_soul.py / lili_engineering.py / lili_blindspot.py / EVOLUTION_LOG.md
       ▼
generate_site.py → 重建网站
```

---

## 主线 3 — Issue 回复 `lili_responds.py`

```
扫描无 lili-responded 标签的 open Issue → 分类 → DeepSeek 生成双语回复 → 发布评论 + 打标签
次日 evolve() 检测 lili-responded 且无 lili-built → 优先从 Issue 建工具 → 打 lili-built 标签
```

---

## 质量闭环

```
每日 evolve() → 质量评分 → tool_quality_ledger.jsonl
                                      │
每周 weekly_evolution.py ← 读最近 14 条 ┘
  → 改写 lili_engineering.py（针对性工程规范）
                                      │
次周 evolve() ←───────────────────────┘  读新规范 → 工程能力提升
```

---

## 关键文件职责

| 文件 | 性质 | 更新方式 |
|------|------|---------|
| `src/super_lili_brain.py` | 入口薄壳，re-export | 静态 |
| `src/lili_llm.py` | Qwen + DeepSeek 客户端/调用 | 静态代码 |
| `src/lili_prompts.py` | 上下文 + 三阶段 prompt 构建 | 静态代码 |
| `src/lili_validators.py` | 验证链 + 解析 + 浏览器验证 | 静态代码 |
| `src/lili_pipeline.py` | evolve() 编排 + 持久化 | 静态代码 |
| `src/lili_soul.py` | 价值观 + 人格核心 | 每周进化自动更新 |
| `src/lili_engineering.py` | 工程规范 BASE（人工）+ LESSONS（每周进化） | 混合 |
| `src/lili_blindspot.py` | 本周盲点 + 下周方向 | 每周进化自动更新 |
| `src/lili_editor.py` | 编辑透镜 + 领域知识（莉莉的内部操作系统） | 人工 |
| `src/lili_memory.py` | 已建工具 + 话题（防重复） | 每次运行后更新 |
| `tool_quality_ledger.jsonl` | 每个工具的质量评分历史 | 每次运行后追加 |
| `docs/EVOLUTION_LOG.md` | 每周进化日志 | 每周追加 |
| `docs/generate_site.py` | 静态站点生成器 | 每次运行后自动调用 |
| `docs/index.html` | GitHub Pages 首页 | 自动生成，不手动编辑 |

---

## API 与依赖说明

- **Qwen（阿里云 DashScope）**：OpenAI 兼容接口，`base_url=https://dashscope.aliyuncs.com/compatible-mode/v1`。联网搜索经 `extra_body={"enable_search": True}`（不传 `tools=[]`，会冲突）。
- **DeepSeek**：`base_url=https://api.deepseek.com`。一个 key 切模型：`deepseek-v4-pro`（代码）/ `deepseek-reasoner`（R1 推理）。
- **Playwright**：CI 中 `playwright install --with-deps chromium`，仅 Mode 3 验证时懒加载。
- **重试**：每模型最多 3 次，退避 10s/20s；空响应也重试。
- **Unicode 限制**：`src/*.py` 字符串字面量禁用 em-dash/中文引号等非 ASCII（GitHub Actions Python 3.11 会 SyntaxError）。PostToolUse hook 每次编辑后自动 `ast.parse` 全部 `src/*.py`。
