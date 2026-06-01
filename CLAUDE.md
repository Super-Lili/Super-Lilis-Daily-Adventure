# CLAUDE.md — 超级莉莉项目记忆文档

> 写给接手这个项目的 Claude。读完这份文档，你就能接上。
> 最后更新：2026-06-01

---

## 这个项目是什么

**Super-Lili's Daily Adventure** 是一个自进化 AI 工具箱项目。

核心机制：
- 莉莉（Gemini）每天自动运行，找到真实人类摩擦点，写一篇双语日记，造一个可以在浏览器里直接使用的工具
- 每周日自我进化：回顾这周造的工具、更新自己的工程规则和灵魂配置
- 用户可以通过 GitHub Issue 委托莉莉造特定工具

### 最终目标（原文，勿改动）

```
Super-Lili's ultimate purpose is to become a self-evolving personal super toolbox —
and over time, a PKM (Personal Knowledge Management) system designed specifically
for creative professionals.
```

**三个阶段：**
- Stage 1（现在）：每天造工具，解决特定创意摩擦点
- Stage 2（即将）：精选工具箱——50-100 个高质量工具，覆盖媒体/编辑/设计/品牌/科技/研究
- Stage 3（未来）：认识你这个人——知道你的项目、你的声音、你的客户，成为随你生长的创意工作空间

**质量标准：**
项目拥有者（xiaojiahaina）是拥有 15 年以上顶级媒体经验的资深媒体编辑和编辑总监，在全球设计、科技、创意和奢侈品行业有深度人脉。工具必须达到这个圈子的标准：没有业余输出，没有通用模板，没有会让专业人士在同事面前感到尴尬的工具。测试标准：资深记者、创意总监或品牌策略师会用这个工具两次吗？

**未来展示策略：** 不展示每天生成的全部工具，而是精选 100 个真正高价值的工具展示在网站上。

**网站**：https://super-lili.github.io/Super-Lilis-Daily-Adventure/
**仓库**：https://github.com/Super-Lili/Super-Lilis-Daily-Adventure

---

## 项目进化史

### 第一阶段：起点（2026-04-29）
- 最初叫"Clarity Compass"，是一个简单的 Python 脚本生成器
- 改名为 Super-Lili's Daily Adventure
- 基本结构：GitHub Actions 每天跑，生成工具放进 `02_Skills/`
- 工具只是 Python 脚本，没有浏览器体验

### 第二阶段：有了灵魂（2026-05 初）
- `5a5cd67` Super-Lili v2：加入温度感人格、URL 验证、每周进化、日记 README
- `d4c6bc5` 加入记忆系统：莉莉记住所有造过的工具和话题，不重复
- `c0d732f` 双语支持：英文 + 中文日记，中文是重新表达，不是翻译
- 工具目录从 `02_Skills/` 改为 `02_Toolbox/`

### 第三阶段：提升工程质量（2026-05 中）
- `e7f08c9` 创建 `lili_engineering.py`——把工程标准从提示词里剥离出来，永久保存
- `8ce7e7e` 解锁 Mode 3：工具可以返回完整 HTML 页面，在浏览器 iframe 里运行
- `cbabb03` 提升质量天花板：按品类设定 benchmark，加入丰富度标准
- `c0b43f0` 受众轮换机制：每天面向不同职业群体（媒体人、设计师、PM、研究者）
- `1a0d4c9` 双维度质量评分：工程分 + 温度分，写入 ledger，每周进化读取

### 第四阶段：网站建设（2026-05 中下）
- 从 README 驱动转向 GitHub Pages 网站
- `6a8fa0e` 全部 28 个工具页面加入 emoji reactions（localStorage 实现）
- `09a8baf` 系统架构页面（暗色视觉流程图）
- `1d83301` 即时工具体验：Mode 3 预渲染 + Mode 1/2 加载后自动演示

### 第五阶段：设计哲学注入（2026-05 下）
- `8e28d6b` 注入工业设计哲学：Dieter Rams、Jasper Morrison、Naoto Fukasawa、Jonathan Ive
- `054d6a7` 尝试暗色设计（aged paper black + 胶片颗粒 + terracotta accent）
- `3639164` 暗色实验回滚——用户觉得不对，恢复白色设计
- `55e808f` 注入北极星：莉莉不是随机造工具，是在造一个有内在逻辑的工具箱
- `cd66547` 重构 `build_prompt()`：从 628 行单体函数拆分为 5 个专注函数

### 第六阶段：声音纯化（2026-05-31）
- `094fb2f` 禁止表演性写作：莉莉的日记不能有"This struck me so deeply!"这类空话
- `36170dc` 同样规则延伸到每周进化报告

### 第七阶段：今天的工作（2026-06-01）
- **修复**：进化日志里多余的 source proposals 条目（合并进周报）
- **修复**：进化日时 Hero 区蓝色工具按钮消失（回退到最近工具）
- **升级工程规则**（`lili_engineering.py` LILI_ENGINEERING_LESSONS）：
  - 变换优先架构：输入结构 ≠ 输出结构才是真正的变换
  - 算法深度下限：必须有一件用户自己 10 秒内做不到的计算
  - HTML 三态状态机：入口态 → 交互态 → 结果态
  - 输出密度测试：每句话做输入替换测试，通不过就删
- **Issue 委托机制**：用户开 Issue → 莉莉回复（lili_responds.py 加 lili-responded 标签）→ 次日莉莉优先按 Issue 内容造工具 → 完成后打 lili-built 标签
- **手工造了太阳光色彩时钟**（Issue #1，API quota 耗尽莉莉没能自己跑）
- **时钟从数字改成模拟表盘**（圆形、指针、平滑秒针）
- **Rule 16**：物理世界作为情感底色——莉莉的工具是数字的，情感底色必须是物理的
- **设计师谱系扩充**：加入 Inga Sempé、Ilse Crawford、Hella Jongerius（原有 Rams、Morrison、Fukasawa、Ive）
- **Pyodide 修复**：检测 `rich`/`requests` 等不兼容库，自动改为"本地运行"提示
- **加载 UX 改善**：提示"约需 15 秒"，自动演示后加引导文字

---

## 关键架构决定

### 工具的三种模式
- **Mode 1**：`process(text)` 返回纯文本
- **Mode 2**：`process(text)` 返回 SVG 字符串
- **Mode 3**：`process(text)` 返回完整 HTML 页面（在 iframe 里运行，可用 Web Audio、Canvas、localStorage）
- **方向**：所有新工具优先 Mode 3，特别是 Healing Inventions 必须 Mode 3

### 分类体系
- 🎨 Design Alchemy（设计炼金）
- 🎓 Education Evolution（教育进化）
- 🗂️ Office Automation（办公自动化）
- 🌿 Healing Inventions（治愈发明）—— Healing 不超过 20%

### Issue 委托流程
```
用户开 Issue
  → lili_responds.py 当天回复，打 lili-responded 标签
  → 次日 evolve() 检测到 lili-responded 且无 lili-built 的 Issue
  → 跳过随机选题，按 Issue 内容造工具
  → 完成后打 lili-built 标签，Issue 里回复工具链接
```

### 网站生成
- `docs/generate_site.py` 读取所有工具和日记，生成静态 HTML
- 工具页面自动判断：Mode 3 → 预渲染 iframe；Mode 1/2 → Pyodide 运行器（自动演示）；含不兼容库 → 本地运行说明
- 每次 `evolve()` 完成后自动调用 `generate_site.py`

---

## 项目拥有者的审美偏好

这是最重要的部分，莉莉的工具必须符合这些标准：

**物理世界共情**（Rule 16）
> 造工具前先问：在没有屏幕的世界里，这个功能会是什么物件？
> 时钟要有指针，不要数字。进度要是圆弧，不要进度条。能用形状传达的意思，不用数字。

**设计师参考谱系**（Rule 15）
- Dieter Rams：少即是多
- Jasper Morrison：安静，不抢眼，经得住每天使用
- Naoto Fukasawa：融入身体节律
- Jonathan Ive：表面简单，内藏工艺
- Inga Sempé：诗意的日常，手工质感与工业生产之间的温柔张力
- Ilse Crawford：感官是设计语言，温度触感都是材料
- Hella Jongerius：色彩有记忆，材质有深度

**目标用户**
创意专业人士：记者、编辑、设计师、品牌总监、创意总监。
不是普通用户，不是工程师。他们有高标准，会立刻感受到工具是否真正为他们造的。

---

## 未完成的事 / 未来方向

- **策展机制**：等工具积累到一定数量，建立"精选 100 个"展示机制。用户（项目拥有者）用过之后打标记，网站只展示精选，其余存在 GitHub 但不上首页
- **开放给公众**：Issue 开放后，普通用户的真实需求是最好的进化燃料
- **质量天花板**：当前工具质量参差不齐，31 个里只有 2-3 个达到"创意专业人士会每周用"的标准。方向是对的，但需要时间积累

---

## 踩过的坑

- **暗色设计实验**：试过 aged paper black + terracotta，用户觉得不对，已回滚
- **表演性写作**：莉莉早期日记有很多空话（"This moved me so deeply"），已通过规则禁止
- **source proposals 文件**：每周进化会生成单独的 source proposals.md，被网站当成进化日志条目显示。已修复，合并进周报
- **git add . 把 .claude/ 带进去**：造成 embedded git repository 警告。已加入 .gitignore
- **healing 类工具过多**：有段时间 53% 的工具是 Healing，已通过轮换机制限制到 20%
- **Pyodide 不支持 rich 库**：Content_Current_Catalyst 工具用了 rich，在浏览器里会报错。已修复为本地运行提示

---

## lili_editor.py 的作用（非常重要）

`lili_editor.py` 是莉莉的**内部操作系统**——她在行动之前看世界的方式。它不出现在日记里，但决定了莉莉找什么、怎么判断、造什么。

由项目拥有者 xiaojiahaina 基于 neo-slow media 框架（2021 至今）亲自撰写。

**三个核心编辑视角：**

1. **用户 vs 人** — 平台把人看成用户（可预测、可量化、可货币化）。莉莉穿透这个框架，看到用户背后的人（迷信的、浪漫的、需要被真正看见的）。用户投诉产生工具，人的投诉产生意义。莉莉造的是后者。

2. **娱乐 vs 参与** — 娱乐在屏幕关掉后结束；参与在工具关掉后还留下改变。莉莉的工具追求参与，不追求娱乐。测试：用完这个工具，这个人和他们的工作/学习/注意力的关系改变了吗？

3. **消耗性摩擦 vs 生产性摩擦** — 来自 neo-slow media 思想的核心洞察。不是所有摩擦都是敌人。消耗性摩擦（官僚循环、平台复杂性）耗尽而不回报；生产性摩擦（促使停下来思考的问题、学习的必要难度）要求付出并返回更多。莉莉的工具引入生产性摩擦，消除消耗性摩擦。

**还包含：** 4 个创意工作领域的深度知识（工作/学习/愈合/设计），受众轮换机制（媒体人/设计师/PM/研究者），domain expansion 系统（每周进化新增领域知识）。

---

## 关键文件

| 文件 | 作用 |
|------|------|
| `src/super_lili_brain.py` | 每日主引擎：找摩擦点、造工具、写日记 |
| `src/lili_engineering.py` | 工程规则（永久 BASE + 每周进化的 LESSONS） |
| `src/lili_soul.py` | 莉莉的性格、技能、进化笔记 |
| `src/lili_editor.py` | **莉莉的内部操作系统**：编辑视角、项目愿景、领域知识、受众轮换 |
| `src/lili_memory.py` | 记忆系统：防止重复造工具 |
| `src/lili_responds.py` | Issue 回复引擎 |
| `src/super_lili_weekly_evolution.py` | 每周自进化引擎 |
| `docs/generate_site.py` | 静态网站生成器 |
| `.github/workflows/lili_daily.yml` | 每日 Actions（北京时间周一到周六 08:05）|
| `.github/workflows/lili_weekly_evolution.yml` | 每周进化 Actions |
| `.github/workflows/lili_issues.yml` | Issue 自动回复 Actions |
