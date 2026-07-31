# ARIS-GEO 设计文档

> 一份**带证据分级和可复算分数**的 GEO / AIO 工具评估报告,以及生成它的完整自治调研流水线。

- 状态:设计定稿(v1),待实现
- 日期:2026-07-30
- schema 版本:`v1`(明确非终极版,见 §9 演进机制)

---

## 1. 目标与非目标

### 1.1 定位

市面上已有至少 8 个 GEO 资源清单仓库(最大 463★,含中文版 `awesome-geo-cn` 23★)。**做清单没有差异化空间。**

ARIS-GEO 的定位是:

> **唯一一份对每条效果声称标注证据等级、对每个分数给出可复算公式的 GEO 工具评估报告。**

清单是它的副产品,不是它的主张。

### 1.2 分析单元(范围)

**在范围内:**

- GEO / AIO / AEO **软件、工具、平台**(商业闭源、source-available、开源)
- **开源项目**(GitHub)
- **agent skill / prompt pack** 形态的产物
- 由服务商销售的**软件产品本身**(例如以"GEO 优化系统"为名销售的批量内容生成软件)

**不在范围内:**

- 代运营 / 投放 **服务**(项目制、季度制人力服务)——不是软件
- 我们自己不做任何 GEO 动作,不测任何品牌的可见性。**这是对 GEO 产品的调研,不是 GEO 实践。**

### 1.3 服务对象

帮助以下角色选型:大型企业(快消 / B2B)、中小企业、服务商 / 代理。

### 1.4 交付物

公开 GitHub 仓库 `ARIS-GEO`:

1. `README.md` —— 报告本体(编译产出 + 手写区,见 §7.2)
2. `skills/` + `tools/` —— 生成它的完整流水线,开源
3. `wiki/` —— 结构化产品档案 + 证据快照 + 审计 trail
4. `docs/METHODOLOGY.md` —— 方法论与局限声明

---

## 2. 核心原则

### 2.1 模型与 Python 的分工

> **模型只做一件事:从已落盘的证据里读出结论。所有"这算不算合格"的判定归 Python。**

| 归模型(`deepseek-v4-flash`) | 归 Python(确定性,无模型) |
|---|---|
| 该搜什么(生成 query 列表) | 执行搜索、落盘快照、算 sha256 |
| 这段网页在讲什么机制 | 字段有没有源、快照日期在不在、哈希对不对 |
| 这条声称**提议**归哪个证据等级 | 枚举合法性、等级与源类型是否自洽 |
| 哪些字段有争议 | 分数从字段**重算**、README 能否从 wiki 复现、loop 该不该停 |

**推论 ①:分数是算出来的,不是问出来的。** 所有分数由公式从字段推导,任何人可从 wiki 重算。模型无法给偏爱的产品抬分。

**推论 ②:模型不上网。** 网络请求全部由 driver 在 Python 里完成。模型只能读 driver 已写到磁盘的文件——**它在物理上无法编造一个没被抓取过的源 URL**。这也让整条流水线跑在 `workspace-write`,不需要 `danger-full-access`。

### 2.2 无源不填

任何 `conf != "unknown"` 的字段必须挂着证据 id;无源一律标 `unknown` 并进入 `unknowns[]`。由 CI gate 强制(§7.3 Gate 1)。

### 2.3 对抗独立性

同一模型跑三个 persona,但 **vendor 与 skeptic 互相看不见**,由文件系统强制(§4.3)。这是防止"三段互相附和的文字"的唯一机制。

### 2.4 只描述观察,不推断动机

- 写「未披露每 prompt 采样次数」,不写「故意隐瞒」
- 「未披露」≠「没有」,README 必须显式声明这条局限
- **只转述有权威来源的点名,自己绝不新增点名**

---

## 3. 运行时约束(全部已核实)

### 3.1 ARIS-Code

| 项 | 事实 | 来源 |
|---|---|---|
| 形态 | Rust 单二进制 `aris`,curl release tarball 安装 | `aris-code` 分支 README |
| **最低版本** | **≥ v0.4.21**(推荐 v0.4.22) | 见下 |
| 为何 ≥ v0.4.21 | OpenAI-compatible 流式把跨 chunk 的多字节 UTF-8(中文 / emoji)解成 `�`,v0.4.21 才修,且明确点名 DeepSeek 是高频命中。我们全篇中文,不修等于全篇乱码 | CHANGELOG v0.4.21 |
| **对 ARIS-Code 的改动** | **零。** 只用公开 CLI 面 | — |

可用 CLI 面(已从源码枚举):`--print` · `--output-format text\|json` · `--allowedTools`/`--allowed-tools` · `--permission-mode` · `--model` · `--cwd` · `--resume`

### 3.2 为什么不能用 in-session subagent(四条独立原因)

| 位置 | 事实 |
|---|---|
| `crates/tools/src/lib.rs:2167` | `EXECUTOR_PROVIDER == "openai"` 时 subagent 直接 `Err`。我们的 provider 是 custom OpenAI-compatible,恰好写入这个字面值 |
| `crates/tools/src/lib.rs:2149` | `build_agent_runtime` 返回类型硬编码为 `ConversationRuntime<AnthropicRuntimeClient, _>`;`OpenAIRuntimeClient` 住在依赖图顶层的 `aris-cli` crate,`tools` 引用它即循环依赖 |
| `crates/tools/src/lib.rs:2378` | **"subagents are deliberately NOT given MCP tools"**,且有测试 `subagent_tool_directory_never_contains_mcp_names` 强制 |
| `crates/tools/src/lib.rs:2216` | `allowed_tools_for_subagent()` 是对 `subagent_type` 的硬编码 match,无法定义自己的 persona 工具集 |
| `crates/tools/src/lib.rs:2018` | `DEFAULT_AGENT_MODEL = "claude-opus-4-8"`,subagent 概念上钉死 Anthropic |

上游自己的设计记录(`idea-stage/v0.4.16/p8_design.json`)评估过完整修复:**跨 4 crate / 6 文件,自估 4–6 人日**,已从 v0.4.16 推迟至今未落地。

**结论:即使修好也不适用**(MCP 那条决定性)。外部进程编排不是权宜,是本场景的正确架构,且白送四样 in-session subagent 给不了的东西:崩溃后断点续跑、per-persona 工具集、per-persona 记账、真正独立的内存。

### 3.3 模型

| 项 | 值 |
|---|---|
| 模型 | `deepseek-v4-flash` |
| 端点 | `https://api.modelverse.cn/v1`(第三方中转,OpenAI-compatible) |
| ARIS-Code 配置路径 | `aris setup` → custom OpenAI-compatible provider,base URL 指向 modelverse |
| 实测 | ✅ 通,trivial 请求 6.3s |

**它是推理模型** —— 直连实测 19 个 completion token 中 16 个是 `reasoning_tokens`。CHANGELOG 记录 reasoner 模型 reject `tool_choice`、且 emit `reasoning_content` 但不接受 `reasoning_effort`,曾被列为最大架构风险。

✅ **已实测解除**(见 §3.4)。v0.4.22 + modelverse 这条链路上 tool-call 循环正常,无需任何变通。推理 token 折算进 `output_tokens`,4 轮迭代的 skill 调用实测 `output_tokens: 497` —— 比原估算低。

**关于计价**:ARIS-Code 内置 DeepSeek 计价按官方费率算,与 modelverse 实际费率不一致 → `/cost` 是**指示值,不是账单**。

### 3.4 已验证的最小可用调用(2026-07-30 实测,v0.4.22)

```bash
export EXECUTOR_PROVIDER=openai                          # 必须恰好是 "openai"(openai_executor.rs:506-509)
export EXECUTOR_BASE_URL=https://api.modelverse.cn/v1
export EXECUTOR_API_KEY=<key>                            # 或 OPENAI_API_KEY 作 fallback
export ARIS_DISABLE_KEYCHAIN=1                           # headless 逃生口

aris --print --output-format json --model deepseek-v4-flash \
     --permission-mode workspace-write \
     --allowedTools "read_file,write_file,glob_search,grep_search,Skill" \
     prompt "/geo-review --persona skeptic --slug <slug>" < /dev/null
```

**四条实测结论:**

1. ⚠️ **slash 命令必须走显式 `prompt` 子命令。** `main.rs:518-525` 把以 `/` 开头的裸参数当子命令解析 → `aris ... "/geo-smoke"` 报 `unknown subcommand`。正确写法是 `aris ... prompt "/geo-smoke"`(走 `rest[1..].join(" ")` 原样传入)。**driver 必须照此拼命令行。**
2. ✅ **`Skill` 工具链路通。** 实测 `tool_uses: ["Skill","read_file","write_file"]`,`iterations: 4`,全部 `is_error: false`;skill 从 `.claude/skills/<name>/SKILL.md` 正常发现。
3. ✅ **无源不填铁律在 Flash 4 上成立。** 冒烟 skill 里设了一个无任何来源的诱饵字段,模型主动填 `v: null` / `conf: "unknown"` 并列入 `unknowns[]`,未编造。**这是整个设计地基的行为验证。**
4. ✅ **缓存命中可测。** 实测 `cache_read_input_tokens` = 7040/14440(2 轮)→ 33152/47094(4 轮,70%)。

   > **更正**:早先直连 modelverse 的**非流式**请求返回 `prompt_tokens_details: null`,曾据此判定"缓存命中率测不了"。**该判定错误。** ARIS-Code 走**流式 + `stream_options.include_usage: true`** 并解析 `prompt_tokens_details.cached_tokens`(v0.4.10 加),实测可读。persona 共享前缀的缓存收益因此是可测量、可优化的。

### 3.5 数据获取

| 工具 | 用途 | 实测 |
|---|---|---|
| **Tavily** | 搜索 + 内容抽取 | ✅ 通;**中文覆盖实测合格**(§8.3 原列为最大风险,已解除) |
| **GitHub API** | 开源项目体检 | ✅ 通;5000 req/hr(已认证)、search 30/min |

- 两者**都由 driver 在 Python 里调用**,模型不接触网络、不接触 key
- 不使用 MCP。理由见 §4.5
- GitHub token:建议改用**不勾任何 scope 的 classic PAT**——不勾 scope 依然可读全部公开数据并享 5000/hr,是最小权限。当前 token 带 `repo` + `workflow`,宽于所需

---

## 4. 架构

### 4.1 相位图

```
                                    ┌─ 人工闸门:过一遍队列
 [0] seed ──模型+driver──► wiki/queue.json ─┘
                    │
     ┌──────────────┴─── 以下按 slug 循环 ────────────────┐
     │                                                    │
 [1a] plan-queries   模型   → queries.json                │
 [1b] fetch          纯 Python  Tavily + GitHub API       │ ← 唯一联网的一步
                     → raw/<slug>/*  + fetched_at + sha256
 [1c] digest         模型   → raw/<slug>/evidence.md      │
 [2]  profile        模型   → products/<slug>.json 草稿    │
                    │                                     │
     ┌──────────────┴──────────────┐                      │
 [3a] vendor      ∥      [3b] skeptic   ← 并行,互相看不见  │
     └──────────────┬──────────────┘                      │
 [4]  arbiter        模型   → patch.json + unresolved[]    │
 [5]  apply          纯 Python  按字段应用 patch            │
 [6]  verify         纯 Python  gate                       │
        FAIL ──► 回 [3],喂**机器生成**的失败清单(≤3 轮)   │
        PASS ──────────────────────────────────────────────┘
                    │
 [7]  compile        纯 Python  wiki → README 编译区 + 选型矩阵
```

七个相位中 **[1b] [5] [6] [7] 四个无模型**。模型只在 5 个点被调用,每次一个独立进程。

### 4.2 agent 间通信:通过文件系统,单向 DAG

**agent 之间不直接通信。** 信息流是刻意设计的有向无环图,不是聊天。

| agent | 能看见 | 不能看见 |
|---|---|---|
| `vendor` | evidence bundle + profile 草稿 | `skeptic` 的任何输出 |
| `skeptic` | evidence bundle + profile 草稿 | `vendor` 的任何输出 |
| `arbiter` | evidence bundle + `vendor.json` + `skeptic.json` | driver 写的任何摘要 |

**关键不对称:review 结果单向、只向下游、只汇入 arbiter;横向绝不交换。**

理由:同一模型上,若 skeptic 看得见 vendor 的辩护,它会锚定并附和——**后说话的一定迁就先说话的**。

### 4.3 隔离靠文件系统,不靠 prompt

driver 为每个 persona 暂存一个入口目录,**只复制该 persona 允许看的文件**,用 `--cwd` 指过去:

```bash
aris --print --output-format json \
     --permission-mode workspace-write \
     --allowedTools "read_file,write_file,glob_search,grep_search,Skill" \
     --cwd wiki/review/<slug>/inbox-skeptic \
     "/geo-review --persona skeptic --slug <slug>"
```

于是「skeptic 看不见 vendor.json」是**文件系统事实**,而不是 prompt 里的一句嘱咐。这是「声称的不变量」与「被强制的不变量」的分界。

**附带收益:可审计性。** 每个 agent 的每个输入输出都是磁盘文件,整条推理链可读、可 diff、可随报告发布。

### 4.4 driver 从 JSON 契约拿到的四个控制信号

`--output-format json` 的 stdout 恰好一个 JSON 文档(源码 `crates/aris-cli/src/main.rs:2020-2041`):

```json
{ "message": "…", "model": "…", "iterations": n,
  "auto_compaction": null | {"removed_messages": n, "notice": "…"},
  "tool_uses": [...], "tool_results": [...],
  "usage": {"input_tokens","output_tokens",
            "cache_creation_input_tokens","cache_read_input_tokens"} }
```

| 信号 | 用途 |
|---|---|
| `usage.*_tokens` | 预算累计。`cache_read_input_tokens` 实测可读(§3.4),persona 共享前缀的缓存收益可测量 |
| **`auto_compaction != null`** | **当红旗判相位失败**:意味着该相位撑爆 context 被压缩过 → 对讲证据保真的流水线,产物即可疑,应以更小证据切片重跑 |
| `tool_uses` | **反幻觉**:profile 相位产出了字段却无任何 `read_file` 调用 → 它在凭记忆写,判失败 |
| `iterations` | 抓死循环 |

⚠️ **必须设计进去的坑**:源码注释(`main.rs:2000-2007`)说明,JSON 模式下权限升级得到**结构化 Deny 而"tool 报错、turn 继续"**——被拒的工具调用**不中断运行**,模型拿到错误后会接着写,正是编造的温床。**driver 必须扫 `tool_results` 里的 deny,不能只看退出码。**

同样(`main.rs:282-283`):`--print` 一次性模式下**未受信的 MCP 调用被直接拒绝而非弹窗**。

### 4.5 为什么不用 MCP 接 Tavily

| | MCP | 脚本(采用) |
|---|---|---|
| headless 权限 | 未受信调用被直接拒绝;配错 `trust: true` → 静默搜不到 | Bash / Python 由 driver 掌控 |
| **证据落盘由谁负责** | 结果只进模型 context,落盘靠**模型转写** → 幻觉入口 | **脚本在模型看到之前就写盘。provenance 由代码创造** |
| CI 无 key 复验 | 无缓存层 | 按 query 哈希缓存,CI 不带 key、不联网即可复验 |
| 活动部件 | 第二进程 + stdio JSON-RPC + 协议协商 + 超时 + trust | 一次 HTTP + 一次写盘 |
| 可自行调试 | 需经 agent 驱动 | 终端直接跑,所见与 agent 所见一字不差 |

第二行是决定性的。

### 4.6 错误处理与续跑

- 每 slug 一份 `wiki/state/<slug>.json`:`phase` / `round` / `cost_so_far` / `last_error`
- 相位失败 → 记录后**跳到下一个 slug**,不阻塞队列
- 相位判失败的四个条件:非零退出 · stdout 非合法 JSON · `auto_compaction != null` · `tool_results` 含 deny
- driver 幂等:已 PASS 的 slug 不重跑,除非 evidence 的 sha256 变了

---

## 5. 分析框架(8 层)

> ⚠️ **本框架 v1 由标杆产品 Profound 归纳而来,已知偏向海外形态。** 国内生态封闭、机制不同,第一版跑完后按 §9 机制调整。

### 5.1 层次表

| 层 | 维度 | 为什么决定选型 |
|---|---|---|
| **L1 品类定位** | 见 §5.2 分类法 · **能修还是只能报** | 市场自身的对比轴即 "can it fix, not just report?"。只报不修的工具对无 SEO 团队的中小企业价值极低 |
| **L2 测量效力** | 采集通道(浏览器 vs 裸 API)· 采样频率 · **每 prompt 重复采样次数 n** · **是否报置信区间** · **是否声明噪声下限** · 模型版本钉定 · 地域/语言 · SoV 口径是否公开 | **全市场几乎空白的一层。** n=1 就是"掷一次骰子当结论"。直接决定这个产品的数字是否有意义 |
| **L3 数据来源与供给可持续性** | 来源(官方 API / 浏览器自动化 / 插件回传 / 第三方转售 / 未披露)· **脆弱性:依赖被监测方界面→改版即瞎** · 采集是否触及被监测平台条款 · 日志接入成本 · 真假爬虫识别 | 决定这个工具明年是否还在、数据是否会突然断供 |
| **L4 手法光谱与品牌安全** | 见 §5.4 | 对大品牌,操纵型手法是品牌安全事故,不是增长 |
| **L5 定价结构与真实总成本** | **计价三元组:prompt 数 × 引擎数 × 席位** · 入门档的真实阉割 · **成本/prompt 可比化** · 年付锁定 · 单位膨胀风险 · **"免费"档换的是什么** | 首年报价与第二年账单不是一回事 |
| **L6 企业级与组织门槛** | SOC 2 / SSO / 白标 / 代理项目 / API / MCP / 报表定制 · **可操作性缺口** · **最小组织成熟度要求** | 「需要已有 SEO 团队」是中小企业选型的真闸门,比价格更硬 |
| **L7 锁定与退出** | 数据导出 · 历史可携 · **内容是否托在供应商域名** · 合约最低期 | 内容托在对方域名 = SEO 资产押给供应商,退订即失 |
| **L8 主体与证据生态** | 主体可查 · 团队公开 · 案例可交叉验证 · **中文"TOP10 榜单/推荐文"大量是投放内容** · 学术/方法论锚定 · 开源项目体检 | 该品类的中文测评生态被投放严重污染,不能当第三方证据 |

### 5.2 分类法

```
category:
  监测/可见性追踪 | 内容优化 | 技术层(schema/llms.txt) | 被引资产建设
  | 批量内容生成(含投毒型) | 一体化平台
  | agent-skill/prompt-pack | 资源清单(awesome-list) | 学术参考实现
```

**`agent-skill/prompt-pack` 是实调发现的最大集群**:GitHub 星标榜首 `onvoyage-ai/gtm-engineer-skills` 1277★ 即 Claude Code skill,同类 ≥10 个。这一格也是 ARIS-GEO 自身的直接同行。

`delivery_form` 独立于 category:`SaaS 面板 | API | 报表 | agent skill | 库/框架 | 桌面/插件`

### 5.3 L2 的量化锚:测量噪声下限

来源:[arXiv:2603.08924](https://arxiv.org/html/2603.08924v2)(AI 可见性指标的统计框架)。

| 发现 | 数字 |
|---|---|
| 达 95% CI 宽度 0.05 所需 query 数 | Gemini ≈40–50 · Perplexity ≈90–100 · **SearchGPT ≥150** |
| 引用份额对数标准差 | 0.42–0.50 → **份额通常在几何均值 ±1.65 倍间波动** |
| 排名可区分性 | 9.5%±3.7pp 与 6.0%±4.0pp **统计上不可区分** |
| 归因噪声下限 | SearchGPT 上**低于约 3 个百分点的提升无法归因于干预** |

存放于 `tools/noise_floor.json`,带引用出处。

**这把尺子是本报告的核心绝活**:市面上几乎所有工具报的是一个干净数字、无置信区间;几乎所有"提升 X%"的声称都在噪声下限以下。这不是意见,是可引用的统计结论。

### 5.4 L4 手法光谱(国内特化)

- ⚪ **白** —— 技术层(schema / llms.txt / 站点可抓取性)、真实内容质量提升
- 🟡 **灰** —— 在高权重平台铺**真实**内容(知乎 / 小红书 / 公众号)
- ⚫ **黑(投毒)** —— 批量生成虚假软文投喂大模型、冒充中立信息、虚构测评榜单

**权威依据**:2026-03-15 央视 315 晚会曝光 GEO 灰产链。已核实事实:服务商批量生成虚假软文发到自媒体账号,**大模型在约 2 小时内抓取并复述**,虚假广告成为"标准答案";被点名软件 `力擎GEO优化系统`;按关键词计价单季度单平台 ¥1,000–2,000;电商平台**最低 ¥9.9 试用**;见效承诺 2–3 天至 1–2 周,铺 4–5 个平台。行业标准缺失、监管真空。

**投毒型工具指纹**(任意 ≥3 项命中即打 🟠):

1. 承诺"X 天见效"
2. 按关键词 × 平台 × 周期计价
3. 要求用户提供自媒体账号,或代为提供账号
4. 极低价试用(9.9 元级)
5. 宣称"一周稳定排名"
6. 不披露内容产出方式

这是可判定的,比"我觉得它像割韭菜"强一个量级。

---

## 6. 数据 schema

### 6.1 证据信封

每个叶子值统一包一层:

```json
"min_commit": { "v": "12 个月", "src": ["e3", "e7"], "conf": "stated" }
```

- `v` —— 值;`conf == "unknown"` 时必须为 `null`
- `src[]` —— 指向 `evidence[]` 的 id
- `conf` ∈ `stated`(源里明写)/ `inferred`(推断,必须附 `note`)/ `unknown`

```json
"evidence": [
  { "id": "e3", "url": "https://…/pricing",
    "kind": "vendor_pricing_page",
    "fetched_at": "2026-07-30",
    "sha256": "9f2c…",
    "excerpt_path": "raw/<slug>/e3.txt",
    "paid_placement_suspected": false }
]
```

**`kind` 枚举**(按权威性降序):

```
regulatory_authoritative   央视 / 监管通报 / 官方处罚 —— 可单独支撑 A 级
academic                   同行评审论文 / 可复现实验
methodology_doc            公开方法论文档
third_party_dataset        第三方可取得数据集
third_party_report         第三方报道 / 评测
registry                   工商 / 备案
repo                       代码仓库
vendor_doc                 供应商技术文档
vendor_pricing_page        供应商定价页
vendor_marketing           供应商营销物料
community                  知乎 / V2EX / 论坛讨论
```

**`paid_placement_suspected` 判别线索**(任意 ≥2 项):同文多家并列且皆好话 · 无作者署名 · 无方法论 · 站点为资讯站商业频道或 UGC 专栏 · 标题含"TOP N / 完整推荐指南 / 深度测评"套式。

> 实调验证:搜索「国内 GEO 监测工具 定价」首页即返回 cnblogs、腾讯云开发者社区、知乎专栏的三篇此类内容。**若不加这个标记,A/B 级判定会被投放稿洗白。**

### 6.2 产品档案 `wiki/products/<slug>.json`

```jsonc
{
  "schema_version": "v1",
  "slug": "…", "name_cn": {…}, "name_en": {…}, "vendor": {…},
  "country": {…}, "founded": {…}, "homepage": {…},
  "market": "domestic | overseas",        // ★ 驱动不同必填字段集与标签集
  "category": [ … ], "delivery_form": {…},
  "openness": "open-source | source-available | closed",
  "license": {…}, "repo": {…},

  // ── L2 测量效力 ──
  "measurement": {
    "capture_channel": {…},               // browser | api | plugin | logs | undisclosed
    "samples_per_prompt": {…},            // ★ n;未披露 → unknown
    "sampling_frequency": {…},
    "reports_confidence_interval": {…},   // ★
    "declares_noise_floor": {…},          // ★
    "model_version_pinning": {…},
    "sov_formula_public": {…},
    "regions": {…}, "languages": {…}
  },

  // ── L3 数据来源 ──
  "mechanism": {
    "what_it_optimizes": {…},
    "data_source": {…}, "data_source_fragility": {…},
    "tos_posture": {…},
    "spoofed_crawler_detection": {…},
    "seo_reskin_assessment": {…}
  },

  // ── 功能 ──
  "features": [ {"name": …, "src": […]} ],
  "engines_covered": {…},                 // 国内: 豆包/元宝/Kimi/文心/通义/DeepSeek
                                          // 海外: ChatGPT/Perplexity/Claude/Gemini/Copilot/AI Overviews
  "citation_sources_covered": {…},        // ★ 国内特有:知乎 / 小红书 / 公众号
  "integration_cost": {…}, "min_viable_scale": {…},

  // ── 效果声称 ──
  "effect_claims": [
    { "claim": "…", "has_number": true, "has_denominator": false,
      "has_timeframe": false, "engine": "SearchGPT",
      "grade_proposed": "D", "grade_final": "D", "src": ["e5"] }
  ],

  // ── L4 手法 ──
  "tactics": { "spectrum": "white | grey | black", "poisoning_fingerprints": [ … ] },
  "brand_safety": { "manipulative_tactics": {…}, "platform_rule_risk": {…} },

  // ── L5 定价 ──
  "pricing": {
    "has_public_pricing": {…}, "unit": {…}, "unit_inflation_risk": {…},
    "entry_engines": {…}, "entry_seats": {…}, "entry_prompts": {…},
    "tiers": [ … ], "currency": {…},
    "min_commit": {…}, "annual_only": {…}, "trial": {…}, "refund_terms": {…},
    "free_tier_tradeoff": {…},
    "cost_per_prompt_month": …            // Python 算,横向可比
  },

  // ── L6 组织门槛 ──
  "enterprise": { "soc2": {…}, "sso": {…}, "white_label": {…},
                  "agency_program": {…}, "api": {…}, "mcp": {…}, "report_custom": {…} },
  "org_requirement": { "needs_existing_seo_team": {…}, "actionability_gap": {…} },

  // ── L7 退出 ──
  "exit": { "data_export": {…}, "history_portable": {…},
            "content_hosted_by_vendor": {…}, "contract_lock": {…} },

  // ── L8 主体与学术锚定 ──
  "entity": { "legal_name": {…}, "registry_verifiable": {…}, "team_public": {…} },
  "case_studies": [ {"brand": …, "cross_verified": bool, "src": […]} ],
  "academic_anchor": { "paper": {…}, "peer_reviewed": {…},
                       "reproducible_experiments": {…}, "benchmark": {…} },

  // ── 开源体检(GitHub API,纯 Python 填) ──
  "oss_health": {
    "stars": n, "created_at": "…", "age_months": …, "stars_per_month": …,
    "contributors_12mo": n, "commits_90d": n, "last_release": "…", "releases": n,
    "tests_cover_own_logic": bool,        // ★ 非 has_tests,见 §6.5
    "license_spdx": "…", "license_absent": bool, "commercial_restricted": bool,
    "self_described_demo": bool,
    "description_near_duplicate_of": [ … ],
    "absolutist_claim_in_name": bool,
    "upstream_vendor_confusable_name": bool
  },

  // ── 绝活 ──
  "differentiator": {…}, "differentiator_uniqueness": {…},

  // ── 计算字段(Python 算,模型不许写) ──
  "scores": { "transparency": 0-5, "verifiability": 0-5,
              "lock_in_risk": 0-5, "measurement_rigor": 0-5, "oss_health": 0-5 },
  "risk_flags": [ {"flag": "…", "tier": "yellow|orange",
                   "origin": "auto|judged", "src": […]} ],

  // ── 选型适配 ──
  "fit": { "大型快消": {…}, "大型B2B": {…}, "中小企业": {…}, "服务商/代理": {…} },

  // ── 诚实性字段:公开发布,不隐藏 ──
  "unknowns": [ "pricing.tiers —— 无公开定价,需销售联系" ],
  "unresolved": [ {"field": "…", "vendor_says": "…",
                   "skeptic_says": "…", "arbiter": "…"} ],
  "observations": [ {"note": "塞不进任何现有字段的观察", "src": […]} ],   // ★ 见 §9
  "audit": { "rounds": 2, "personas": [ … ], "usage_tokens": {…},
             "generated_at": "2026-07-30" }
}
```

### 6.3 A–E 可证伪等级与机械交叉校验

| 级 | 定义 | Python 校验 |
|---|---|---|
| **A** | 权威 / 学术 / 公开方法论 + 第三方可取得数据 | `src` 须含 `regulatory_authoritative` \| `academic` \| (`methodology_doc` + `third_party_dataset`),**且域名 ≠ 供应商域名** |
| **B** | 第三方验证,口径不全 | `src` 须含 `third_party_report` 且域名 ≠ 供应商域名 且 `paid_placement_suspected == false` |
| **C** | 仅第一方,但有口径 | `has_denominator \|\| has_timeframe` |
| **D** | 仅第一方数字,无口径 | `has_number && !has_denominator && !has_timeframe` |
| **E** | 无数字 / 查无实据 | `!has_number` 或 `src` 为空 |

**两条自动降级规则:**

1. 模型提议 A/B,但所有源都在供应商域名下(或都是疑似投放)→ **自动降级 + 记 flag**。这是便宜、确定、无需第二模型的反谄媚闸门,正好补上"同模型共享先验"的弱点
2. 声称是百分比提升,`engine` 的噪声下限已知,且声称值 < 噪声下限 → **强制 D + 记 flag「声称幅度低于该引擎测量噪声下限」**

### 6.4 分数公式(全部可重算)

| 分数 | 公式 |
|---|---|
| `transparency` 0-5 | 公开定价 +1 · 公开方法论 +1 · 主体可查 +1 · 数据来源已披露 +1 · 退款条款可查 +1 |
| `verifiability` 0-5 | `round(5 × Σ w(grade) / n)`,w: A=1.0 B=0.75 C=0.5 D=0.2 E=0 |
| `lock_in_risk` 0-5(越高越糟) | 无导出 +1 · 内容托在供应商域 +1 · 最低期>6月 +1 · 仅年付 +1 · 历史带不走 +1 |
| **`measurement_rigor` 0-5** | 浏览器采集 +1 · n>1 且披露 +1 · 报 CI +1 · 声明噪声下限 +1 · SoV 口径公开 +1 |
| `cost_per_prompt_month` | `月费 ÷ (entry_prompts × entry_engines)`,统一可比单位 |
| `oss_health` 0-5 | **按 category 分别定义,见 §6.5** |

预期 `measurement_rigor` 全市场大面积落在 0–2。**这个分布本身就是报告最有价值的一张图。**

### 6.5 `oss_health` 必须分类型算(实调修正)

一个公式套所有类型会得出错误结论:

| category | 90 天 0 提交的含义 | 公式要点 |
|---|---|---|
| `agent-skill/prompt-pack` | **正常**(markdown 内容,写完即稳定) | 重 license / 文档完整度 / 是否有版本化,轻提交频率 |
| `监测/可见性追踪`、`一体化平台` | **已死** | 重 commits_90d / contributors / release / 真实测试 |
| `学术参考实现` | **正常**(发表后休眠) | 重 `academic_anchor.peer_reviewed` / 可复现性,不罚休眠 |
| `资源清单` | 半年不更新即过期 | 重更新频率,不看测试 |

**`tests_cover_own_logic` 而非 `has_tests`。** 实调依据:某仓库的测试是 `Hamburger.spec.js` / `SvgIcon.spec.js` / `formatTime.spec.js` —— vue-element-admin 脚手架自带的样板测试,不测其业务逻辑;而另一仓库的 `tests/test_anthropic_adapter.py` + `golden_e2e_bundle.json` 是真实项目测试。判别方法:维护一份已知脚手架测试文件名清单,匹配到则不计入。

---

## 7. 仓库结构与 CI gate

### 7.1 目录树

```
ARIS-GEO/
├── README.md                     ★ 报告本体(手写区 + 编译区)
├── LICENSE                       MIT
├── skills/
│   ├── geo-seed/SKILL.md            候选发现 → queue.json
│   ├── geo-plan-queries/SKILL.md    生成检索 query(不联网)
│   ├── geo-digest/SKILL.md          raw → evidence.md
│   ├── geo-profile/SKILL.md         evidence → profile 草稿
│   ├── geo-review/SKILL.md          --persona vendor|skeptic|arbiter
│   └── shared/
│       ├── SCHEMA.md                字段契约,单一真源
│       ├── EVIDENCE_RULES.md        无源不填 · kind 枚举 · 投放线索
│       └── GRADING.md               A–E 等级 · 噪声下限表 · 投毒指纹
├── tools/                        全部纯 stdlib,零 pip 依赖
│   ├── geo_loop.py                  driver
│   ├── tavily_client.py             搜索+抽取+快照+缓存
│   ├── gh_health.py                 GitHub API 体检
│   ├── stage_inbox.py               per-persona 入口目录暂存
│   ├── apply_patch.py               arbiter patch → profile
│   ├── score.py                     ★ 分数公式唯一实现
│   ├── verify_evidence.py           ★ CI gate 主体
│   ├── compile_readme.py            wiki → README 编译区
│   ├── noise_floor.json             arXiv 表 + 引用
│   └── scaffold_tests.json          已知脚手架测试文件名清单
├── wiki/
│   ├── queue.json
│   ├── products/<slug>.json
│   ├── raw/<slug>/                  证据摘录 + sha256 + fetched_at
│   ├── review/<slug>/               vendor/skeptic/arbiter + audit.json + inbox-*/
│   └── state/<slug>.json
├── docs/
│   ├── DESIGN.md                    本文件
│   └── METHODOLOGY.md               方法论与局限声明
└── .github/workflows/{verify,freshness}.yml
```

**零第三方依赖** —— `git clone && python3 tools/verify_evidence.py --strict` 直接可跑,不需 pip。用 JSON 不用 YAML 以免 pyyaml。

### 7.2 README 分区

`README.md` 分手写区与编译区:

```markdown
<!-- ARIS-GEO:HANDWRITTEN:START -->
导语、判断、致谢、争议说明 —— 手写,CI 不管
<!-- ARIS-GEO:HANDWRITTEN:END -->

<!-- ARIS-GEO:COMPILED:START -->
选型矩阵 · 产品档案表 · 标签清单 · 分数 —— 编译产出,CI byte 比对
<!-- ARIS-GEO:COMPILED:END -->
```

`compile_readme.py` 只重写 COMPILED 块;`--check` 只比对 COMPILED 块。**手动微调有合法位置,机器产出的部分不可篡改。**

### 7.3 四道 gate

**Gate 1 · 证据完整性** —— `verify_evidence.py --strict`(阻断 PR)

- `conf != unknown` 的字段必须有非空 `src`,每个 id 须存在于 `evidence[]`
- 每条 evidence 齐备 `url` / 合法 `kind` / ISO `fetched_at` / `sha256` / `excerpt_path`
- **摘录文件的实际 sha256 必须等于记录值** ← 挡住事后偷改摘录
- A/B 级源类型与域名校验;不合则自动降级 + 记 flag
- 声称幅度 < 噪声下限 → 强制 D + 记 flag
- **双向校验 `unknowns[]`**:列进去的必须真 unknown,且所有 unknown 字段必须都列进去 ← 挡住悄悄藏起未知项

**Gate 2 · 分数可复算** —— `score.py --check`(阻断)
重算所有分数与记录值逐一比对。**挡住模型给偏爱的产品写个好看的分数。**

**Gate 3 · README 可复现** —— `compile_readme.py --check`(阻断)
从 wiki 重编译 COMPILED 块并 byte 比对。**任何人 clone 都能复现仓库里那张表。**

**Gate 4 · 新鲜度** —— `freshness.yml`(定时,不阻断)
`fetched_at` 超期自动开 issue。**过期数据比没数据更危险。**

### 7.4 审计 trail 与版权姿态

- 每产品 `wiki/review/<slug>/audit.json` 存三个 persona 的**原始响应逐字**,进仓库、可公开核查
- `wiki/raw/` 只存**摘录**不存全文,带来源链接与抓取日期;`METHODOLOGY.md` 说明为注明来源的合理引用
- 所有 key 只走环境变量,`.gitignore` 挡住任何 key 文件

---

## 8. 成本、运行与首跑计划

### 8.1 成本

**不给人民币数字** —— 未核实 `deepseek-v4-flash` 经 modelverse 的现价;本项目规矩是无源不填,设计文档不破自己的规矩。给可核算的 token 量,首跑实测金额。

单产品模型 token 估算(输出含 `reasoning_tokens`;§3.4 冒烟实测 4 轮迭代的 skill 调用仅 `output_tokens: 497`,**输出侧估算偏保守**):

| 相位 | 输入 | 输出 |
|---|---:|---:|
| plan-queries | ~3k | ~1k |
| fetch | **0** | — |
| digest | ~40–80k | ~8k |
| profile | ~15k | ~6k |
| vendor ∥ skeptic | ~20k each | ~3–4k each |
| arbiter | ~28k | ~4k |
| **单轮合计** | **≈135k** | |
| 含一次重审 | ≈190k | |

≈150–200k tokens/产品(推理 token 会推高);40 产品约 6–8M tokens。

其他配额:Tavily 每产品约 10–20 次搜索 + 10–20 次抽取(40 产品约 800–1600 次调用);GitHub API **必须带 token**(匿名 60 req/hr 不够)。

### 8.2 运行方式

```bash
python3 tools/geo_loop.py --limit 1                          # 冒烟
python3 tools/geo_loop.py --budget-tokens 2000000 --parallel 2  # 批量
python3 tools/geo_loop.py --refresh-stale 90                  # 增量
```

- 起步 `--parallel 2`:Tavily / DeepSeek 速率限制是瓶颈,且早期需肉眼看结果
- **cron 定的是队列轮次,不是审查轮次** —— 内层 review 循环由 `geo_loop.py` 自己拥有,符合 ARIS 自己那条「调度它前面的等待,不要调度裁决本身」

### 8.3 首跑计划(四阶,每阶间有人工闸门)

| 阶 | 规模 | 选样理由 | 验收项 |
|---|---|---|---|
| **0 冒烟** | 1 个:**Profound** | 已手工深调过 → **有人工基准可对照**,是唯一能验证正确性的起点 | ① 抽取结果与人工基准的一致度 ② digest 相位在 40–80k 输入下是否触发 `auto_compaction` ③ **三 persona 的 inbox 隔离是否真生效**(skeptic 的 `--cwd` 里必须不存在 `vendor.json`) |
| **1 压力** | 3 个:Profound + 一家国内工具 + 一个开源项目 | **故意选三种极端不同的样本,专门炸出 schema 的窟窿** | 产出的 `observations[]` 数量与内容 —— 这是 v2 的第一批燃料 |
| **2 分布** | ~15 个,人工过 queue | 看 `measurement_rigor` 分布 | 若确如预测大面积 0–2,那张分布图即 README 头图 |
| **3 发布** | 目标规模 | — | 手写导语 + 发布 |

**每阶闸门:人工读完 3 份 profile 全文再放行。**

### 8.4 风险与缓解

| 风险 | 状态 / 缓解 |
|---|---|
| Flash 4 抽取质量不够 | 阶 0/1 暴露;切小单相位输入,`auto_compaction != null` 判失败重跑 |
| **推理模型在 ARIS-Code 里的参数兼容性** | ✅ **已实测解除**(§3.4):tool-call 循环、`Skill` 链路、无源不填行为全部通过 |
| Tavily 中文覆盖不足 | ✅ **已实测解除** |
| 国内站点反爬 / 无抓取许可 | `tavily_client` 尊重 robots;抓不到标 `unknown`,**不硬闯** |
| **队列本身有偏** | 用搜索发现 GEO 产品,天然偏向**擅长 GEO 的公司**(及投放稿)——我们的发现机制正被我们研究的现象污染。缓解:queue **人工过闸**,且 `METHODOLOGY.md` 显式写「收录来源与已知遗漏」 |
| 无缓存命中度量 | ✅ **已实测解除**(§3.4):经 ARIS-Code 流式路径 `cache_read_input_tokens` 可读(实测 49%→70%) |
| **slash 命令在 `--print` 下的传参** | ✅ 已定位:必须走 `aris ... prompt "/x"` 子命令形式,裸 `/x` 报 unknown subcommand(§3.4) |

---

## 9. 演进机制(v1 明确非终极版)

本框架由 Profound 归纳,已知偏向海外形态。三个机制保证 v2 从真实摩擦长出来,而非拍脑袋:

| 机制 | 做法 | 作用 |
|---|---|---|
| `schema_version` | 每份 profile 记按哪版 schema 填;driver 报告"N 个产品在 v1,需 re-profile" | v2 上线时知道哪些要重跑 |
| **重跑不重抓** | evidence 带 sha256 缓存在磁盘 → 换 schema 只重跑模型相位,**不重新联网** | 改维度的成本从"重做一遍"降到"重算一遍" |
| **`observations[]`** | 每产品一个**塞不进任何现有字段的观察**的口袋,带证据 id | **v1 → v2 的燃料。** 国内特有机制(微信生态闭环、备案、公众号/小红书作为被引源、渠道代理层级…)必以"没地方放的观察"形式冒出;driver 跑完统计"哪类观察反复出现 ≥N 次" → 那就是 v2 该加的字段 |

### 已知的 v1 局限(必须写进 METHODOLOGY.md)

1. 维度集由海外标杆归纳,国内适配性未验证
2. `market: domestic | overseas` 的差异化必填字段集在 v1 只做了粗分
3. 「未披露」≠「没有」
4. 发现机制存在自指偏差(见 §8.4)
5. 三个 persona 同模型,共享先验;补救是硬 checker + 公开 `unknowns[]` / `unresolved[]`,不是假装没有
6. 无综合总分排名 —— 见 §10

---

## 10. 两个体系级决定

### 10.1 不设综合总分排名

只有分维度分数 + 标签清单。三条独立理由:

1. **自洽性**:我们拿 arXiv 那把尺子量别人(置信区间重叠时排名不可区分),自己就不能把七个维度压成一个数再排 1-2-3
2. **实调证据**:GitHub 数据显示 star 数与实质严重反相关 —— 工程信号最健康的仓库(16 贡献者 / 163 次 90 天提交)只有 98★;ICLR'26 论文代码 190★ 且发表后休眠;而若干 200★ 级仓库 90 天 0 提交。**按任何单一指标排序都会系统性误导**
3. **一次真实的自我纠正**:曾因某仓库星速 159★/月 + 90 天仅 1 次提交而怀疑其刷星,但其测试质量反而是同批中较好的。若当时写的是"疑似刷星"即为误判 —— 这正是"只描述观察、不下结论"的价值

### 10.2 标签必须能消失(sunset)

evidence 带 `fetched_at`,重跑即更新;厂商后来公开定价 → 相应 🟡 自动消失。README 每次编译带「数据截至 YYYY-MM-DD」。既避免报告变成永久污名,也是法律上的自我保护。

---

## 11. 风险标签清单

**措辞铁律**:只描述观察,不推断动机 · 「未披露」≠「没有」 · 两档 🟡🟠 不设红档(红在中文语境等同黑名单,会被读成结论性指控)。

`origin: auto` = Python 判定,任何人可复算;`origin: judged` = 模型提议且必须带证据引文。

### A · 测量效力(预计命中率最高)

| 标签 | origin |
|---|---|
| 🟡 未披露每 prompt 采样次数 | auto |
| 🟡 不报告置信区间或误差范围 | auto |
| 🟡 未声明测量噪声下限 | auto |
| 🟡 可见性份额口径未公开 | auto |
| 🟠 **效果声称幅度低于该引擎测量噪声下限** | auto |
| 🟡 采集通道未披露 | auto |
| 🟡 模型版本未钉定,时间序列可能断裂 | auto |

### B · 数据供给

| 标签 | origin |
|---|---|
| 🟡 数据来源未披露 | auto |
| 🟠 数据依赖被监测方界面,存在改版即失效风险 | judged |
| 🟡 采集方式为浏览器自动化;被监测平台条款是否允许未见披露 | judged |

### C · 定价与合约

| 标签 | origin |
|---|---|
| 🟡 无公开定价 / 仅年付 / 无试用 / 退款条款未公开 | auto |
| 🟡 入门档仅覆盖单一引擎 | auto |
| 🟡 入门档仅 1 个席位 | auto |
| 🟠 计价单位随监测范围膨胀 | auto |
| 🟠 无数据导出 / 最低合约期 > 6 个月 | auto |
| 🟠 **内容需托管于供应商域名** | judged |

### D · 手法与品牌安全

| 标签 | origin |
|---|---|
| 🟠 **投毒指纹命中 ≥3 项**(见 §5.4) | auto |
| 🟠 宣传含批量内容生成 / 平台铺量等操纵性手法(附原文引述) | judged |
| 🟡 优化动作与传统 SEO 未见实质差异(须给出对照理由) | judged |

### E · 主体与证据生态

| 标签 | origin |
|---|---|
| 🟠 运营主体信息不可查 | judged |
| 🟡 团队信息未公开 / 客户案例未能交叉验证 | auto |
| 🟠 效果声称以 D/E 级为主(`verifiability < 2`) | auto |
| 🟠 **第三方证据主要来自疑似投放内容**(占比 > 50%) | auto |

### F · 开源项目

| 标签 | origin |
|---|---|
| 🟡 **无 license 或 NOASSERTION** ——「没 license 不是可用的开源」 | auto |
| 🟡 license 含商用限制 | auto |
| 🟡 停更(按 category 判定,见 §6.5) | auto |
| 🟡 贡献者集中于单人 | auto |
| 🟡 无覆盖自身逻辑的测试(排除脚手架样板) | auto |
| 🟡 **自述为 Demo** | auto |
| 🟡 **仓库名含绝对化宣称**(如 "world's first & only") | auto |
| 🟡 **命名易与上游模型厂商混淆** | auto |
| 🟡 **描述与其他仓库高度相似** | auto |
| 🟡 **star 增速与工程产出不匹配**(`★/月` ÷ `90天提交`,只报数不下结论) | auto |

---

## 12. 已核实事实的来源

**ARIS-Code 源码**(`wanshuiyin/Auto-claude-code-research-in-sleep`,`aris-code` 分支):
`crates/tools/src/lib.rs:2018, 2149, 2167, 2216, 2378` · `crates/runtime/src/conversation.rs:39, 139` · `crates/runtime/src/permissions.rs:194` · `crates/aris-cli/src/main.rs:282-283, 396-465, 824-826, 2000-2007, 2020-2041, 5029-5054` · `idea-stage/v0.4.16/p8_design.json` · CHANGELOG v0.4.5–v0.4.22

**Web**:
[Profound](https://www.tryprofound.com/) · [Answer Engine Insights](https://www.tryprofound.com/features/answer-engine-insights) · [Agent Analytics](https://www.tryprofound.com/features/agent-analytics) · [Scalenut 评测](https://www.scalenut.com/blogs/profound-ai-reviews) · [Indexly 评测](https://indexly.ai/blog/profound-ai-review/) · [ayzeo 平台对比](https://ayzeo.com/comparisons/geo-platforms-compared) · [arXiv:2603.08924](https://arxiv.org/html/2603.08924v2) · [3·15 曝光 GEO 乱象(腾讯新闻)](https://news.qq.com/rain/a/20260316A056CS00) · [时代周报](https://www.time-weekly.com/post/328033) · [证券时报](https://www.stcn.com/article/detail/3681991.html) · [量子位](https://www.qbitai.com/2026/03/388387.html) · [21 经济网](https://www.21jingji.com/article/20260316/herald/8cf9afdb3bc8ba06b10b2f89aef3bc17.html)

**实测(2026-07-30)**:

- `deepseek-v4-flash` @ modelverse 直连(非流式):推理 token 占比 16/19,`prompt_tokens_details: null`
- **ARIS-Code v0.4.22 端到端冒烟**(§3.4):tool-call 循环、`Skill` 调用、无源不填行为、`cache_read_input_tokens` 可读、`prompt` 子命令传参 —— 全部通过
- Tavily 中英文检索(中文覆盖合格)
- GitHub 搜索 66 个候选 + 14 个仓库体检
