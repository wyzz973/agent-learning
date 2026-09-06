# 12 周 Agent 开发学习路线（每天 1 小时版）

## 怎么用这份计划

- **每周 5 天，周一至周四学 + 写，周五只做两件事**：把这周的代码跑通一遍、在 `notes/weekXX.md` 写 200 字复盘（学了什么 / 卡在哪 / 下周要补什么）。周五的复盘不能省，它是每天 1 小时节奏下唯一能防止"学完就忘"的机制。
- **每天 1 小时的正确用法**：前 10 分钟看资料，后 50 分钟写代码。**不要反过来。** 每天 1 小时的时间预算里，看视频是最低效的投入方式——视频适合周末补，工作日只写代码。
- **每周的"自检"必须能不看资料独立完成**，做不到就把这周顺延，不要赶进度。12 周是参考值，不是 KPI。
- **允许跳过**：如果你的目标是内部工具而不是求职，Week 10（MCP）和 Week 11（部署）可以往后放。

---

## 阶段一：地基（Week 1-2）——不碰任何框架

### Week 1｜Python 工程能力补课

这是整份计划里唯一"不好玩但绝对不能跳"的一周。你说 Python 基础一般，那么 agent 开发会在这几个点上反复卡你：

| 主题 | 为什么 agent 开发必须会 |
|---|---|
| `async` / `await` / `asyncio.gather` | 所有 LLM 调用都是 IO 密集型，并行调 5 个工具和串行调，差 5 倍时间 |
| 类型注解 + `pydantic` `BaseModel` | 工具的参数 schema、结构化输出全靠它，这是 agent 开发里最高频的 Python 特性 |
| 装饰器原理 | `@tool` 到底做了什么，不懂装饰器就只能背 API |
| `uv` / venv / `.env` 管理 | 依赖地狱是新手 80% 的挫败来源 |
| `try/except` + 重试 + 超时 | LLM API 会超时、会限流、会返回畸形 JSON，这是常态不是异常 |

**产出**：`week01_python_basics/` 下 5 个小脚本，其中必须有一个是"用 asyncio 并发请求 3 个 URL 并合并结果，带超时和重试"。

**自检**：能说清 `pydantic.BaseModel` 生成的 JSON Schema 长什么样，并手写一个带嵌套字段和描述的 model。

---

### Week 2｜手写一个裸 agent（不用任何框架）

本周目标：**用 100 行以内的纯 Python + LLM SDK，写出一个能调用工具的 ReAct agent。**

要自己实现的东西：
1. 维护一个 `messages` 列表（system / user / assistant / tool 四种角色）
2. 把 Python 函数转成 tool schema（手写 JSON Schema，感受一下痛苦，之后你才知道 `@tool` 帮你省了什么）
3. 循环：调模型 → 如果返回 `tool_calls` 就执行 → 把结果作为 `tool` 消息追加 → 再调模型 → 直到没有 tool_call
4. 加上最大循环次数保护（防止无限循环烧钱）

给 agent 两个工具就够：`get_weather(city)`（假数据）和 `calculator(expr)`。

**周四额外任务**：接入 LangSmith。只需在 `.env` 里设 `LANGSMITH_TRACING=true` 并用 `@traceable` 装饰你的主循环，就能在网页上看到每一步。**很多人把 LangSmith 放到最后学，这是错的**——它是你唯一的调试手段，越早接越省时间。

**自检**：把 `max_iterations` 设成 2，问一个需要 3 步的问题，看会发生什么，并解释清楚。能画出 agent loop 的流程图。

> 这两周结束时，你已经懂了 agent 的全部本质。后面 10 周学的都是"如何不重复造轮子"和"如何让它在生产环境别崩"。

---

## 阶段二：LangChain 1.0（Week 3-5）

### Week 3｜LangChain 1.0 核心 API

**警告**：只看 v1 文档（docs.langchain.com），任何提到 `LLMChain` / `initialize_agent` / `AgentExecutor` 的教程一律跳过——那是 0.x 时代的，2025 年 10 月的 1.0 已把它们移到 `langchain-classic` 包里。

本周只需掌握 5 个入口：

```python
from langchain.chat_models import init_chat_model  # 一行切换任意模型厂商
from langchain.tools import tool  # 装饰器定义工具
from langchain.agents import create_agent  # 标准 agent 构造器
from langchain.messages import HumanMessage  # 统一消息类型
# content_blocks：跨厂商统一读取 reasoning / text / tool_call
```

用 `create_agent` 重写 Week 2 的裸 agent，然后对比两份代码——你会非常清楚框架到底替你做了什么。

**自检**：不看文档写出一个带 3 个工具的 `create_agent`，并用 `init_chat_model` 在两个不同厂商模型间切换而不改其他代码。

---

### Week 4｜结构化输出 + 工具设计

Agent 能不能用，一半取决于工具设计得好不好。本周重点：

- `response_format` / 结构化输出：让 agent 返回可被下游代码消费的对象，而不是一段文字
- 工具的 docstring 就是 prompt——写清楚参数含义、边界、失败时返回什么
- 工具返回值要"给模型看"而不是"给人看"：返回结构化的少量字段，别把整个 API 响应糊进去（这直接决定 token 成本）
- 工具报错时不要抛异常中断 agent，要把错误信息作为 tool 结果返回，让模型自己重试

**产出（第一个作品）**：一个「个人信息助手」——3～4 个真实工具（读取本地文件 / 调一个公开 API / 写入 SQLite），能回答"帮我把这周的 xx 汇总成表格"这类问题。

---

### Week 5｜RAG（够用就好，别陷进去）

RAG 是 agent 的一个工具，不是一门独立学科。每天 1 小时的预算下，**这周只学到"能用"，不要去深挖 GraphRAG、rerank 调优、chunk 策略对比**——那是有真实数据和真实痛点之后才该做的事。

必须搞懂的最小集：
- embedding 是什么、相似度检索为什么会失败（同义不同词 / 反义高相似）
- 一个本地向量库（Chroma 或 FAISS）的读写
- 分块的基本权衡（太大噪声多，太小丢上下文）
- **把检索包装成一个 tool 交给 agent**，而不是写固定的"检索→拼prompt→回答"流水线。后者是 2023 年的 RAG，前者才是 agentic RAG

**产出**：把你自己的一批文档（笔记、PDF、公司文档）灌进去，让 Week 4 的 agent 多一个 `search_my_docs` 工具。

---

## 阶段三：LangGraph（Week 6-8）——核心中的核心

> 这三周是整份计划的重心。**求职和生产环境真正看重的是 LangGraph 的状态与控制能力**，而不是 LangChain 的 API 熟练度。

### Week 6｜Graph 基本功

- `StateGraph`、`State`（TypedDict + `Annotated` reducer，比如消息用 `add_messages` 累加）
- `add_node` / `add_edge` / `add_conditional_edges`
- 四种基本控制流：顺序、条件分支、循环、并行
- **理解 "为什么需要图"**：`create_agent` 是一个固定循环，当你需要"先分类再走不同分支""某步失败回退重试""两个子任务并行再汇合"时，循环表达不了，图可以

**自检**：手写一个带条件分支和一个循环的 graph，不用 `create_agent`，用原始 `StateGraph` 复刻出 ReAct agent。做到这一点，LangGraph 就算入门了。

---

### Week 7｜持久化、记忆、人机协同、流式

这周的四个能力是"玩具 demo"和"能给别人用的产品"之间的全部差距：

| 能力 | 关键点 |
|---|---|
| Checkpointer（`InMemorySaver` → `SqliteSaver`） | 状态存盘，agent 可以中断后恢复；`thread_id` 就是会话 ID |
| 短期 vs 长期记忆 | 短期＝当前 thread 的消息；长期＝跨会话的 store。**先想清楚"记什么"，再想"存哪"** |
| Human-in-the-loop（`interrupt`） | 危险操作（发邮件、删数据、付钱）前暂停等人批准。这是 agent 落地的合规刚需 |
| Streaming | 用户不能盯着转圈 30 秒，要流式输出 token 和中间步骤 |

**产出**：给 Week 4 的助手加上多轮会话记忆 + "写数据库前需要我确认"。

---

### Week 8｜Middleware 与多智能体

**Middleware 是 LangChain 1.0 最重要的新东西**，六个钩子把 agent 循环切开让你插手：
`before_agent` → `before_model` → `wrap_model_call` → `wrap_tool_call` → `after_model` → `after_agent`

先用内置的三个，理解它们各自解决什么问题：
- `SummarizationMiddleware`：对话变长后自动压缩历史（这就是 context engineering 的最基础形态）
- `HumanInTheLoopMiddleware`：比手写 `interrupt` 更省事
- `PIIMiddleware`：脱敏

然后写一个自定义 middleware，比如"记录每次调用的 token 成本并在超预算时中断"。

多智能体只需理解两种模式，不要贪多：
- **Supervisor**：一个主管把任务分派给专家 agent
- **Handoff**：agent 之间直接移交控制权

> 重要判断：**多智能体不是越多越好。** 业界共识是能用单 agent + 好工具解决的，绝不上多 agent——每多一个 agent，出错面和调试成本都指数上升。这一周学它是为了知道什么时候**不**用它。

---

## 阶段四：工程化（Week 9-12）——2026 的真正分水岭

### Week 9｜Evals（评估）—— 最被低估、最值钱的一周

调研数据：**89% 有生产 agent 的团队做了可观测，但只有 52% 建了 evals**。这 37 个百分点的缺口，就是"demo 能跑"和"敢上线"的差距，也是 2026 年 AI 工程师简历上最稀缺的能力。

本周学：
1. 在 LangSmith 里建 **Golden Dataset**：20～30 条你自己整理的输入 + 期望输出
2. 三类评估器：精确匹配（工具是否被正确调用）、启发式（是否包含关键字段）、**LLM-as-a-Judge**（回答质量打分）
3. 改一次 prompt / 换一次模型 → 跑一次评估 → 看分数变化。**建立"改动必须被量化"的习惯**
4. Trace 分析：从 LangSmith 里找出最慢的一步、最贵的一步

**自检**：能说出你的 agent 在你自己的数据集上的准确率是多少，以及最常见的失败模式是什么。这句话能说出口，你就超过大多数只会写 demo 的人。

---

### Week 10｜MCP（Model Context Protocol）

MCP 已经是 2026 年工具接入的事实标准——一次实现，任何兼容客户端（Claude Code、Claude Desktop、各类 IDE）都能用。

- 第 1-2 天：**用**现成 MCP server（文件系统、GitHub、数据库），并在 LangChain agent 里通过 MCP adapter 接入
- 第 3-4 天：**写**一个自己的 MCP server（Python SDK，暴露 2～3 个工具）
- 理解 MCP 和普通函数工具的区别：进程隔离、跨应用复用、标准化的 JSON-RPC 协议

**产出**：把 Week 5 的 `search_my_docs` 改造成一个 MCP server，然后在 Claude Code 里直接用上它。

---

### Week 11｜部署与生产工程

- 用 FastAPI 把 agent 包成流式 HTTP 接口（SSE）
- 部署选择：LangGraph Platform（省事）vs 自托管（可控）
- 生产必须处理的四件事：**超时、限流/重试、成本上限、日志脱敏**
- 环境隔离与 key 管理（别把 key 提交进 git，`.gitignore` 早就写好了）

---

### Week 12｜综合项目 + 作品集

把前 11 周的东西收成一个能演示的项目。选题标准：**解决你上班时真实遇到的一个重复劳动**（比周报生成器、代码审查助手这类"教程题"有价值得多）。

必须包含：
- [ ] LangGraph 图结构（有条件分支或循环）
- [ ] 持久化 + 多轮会话
- [ ] 至少一个危险操作走 human-in-the-loop
- [ ] LangSmith 追踪 + 一个 20 条以上的评估数据集，并附上评估分数
- [ ] README 里画出架构图、写明失败模式和成本

最后一条是关键：**带评估分数和失败模式分析的项目，和"我做了个 agent demo"，在别人眼里完全不是一个量级。**

---

## 每周节奏模板

| | 内容 |
|---|---|
| 周一 | 读官方文档对应章节 + 跑通官方示例（10 分钟读，50 分钟敲） |
| 周二 | 改造示例：换模型 / 加工具 / 故意弄坏它看报什么错 |
| 周三 | 写自己的版本，不看文档，卡住了再查 |
| 周四 | 把本周成果接到上一周的项目上（**保持代码是连续演进的，不要每周从零开始**） |
| 周五 | 全量跑一遍 + 写 200 字复盘 + 更新 `notes/weekXX.md` |
| 周末（可选） | 看视频课补理论、逛别人的开源 agent 项目源码 |

## 12 周之后

- 读源码：`langgraph` 的 `pregel` 执行引擎、`create_agent` 的实现
- 深入 context engineering：上下文压缩、子 agent 隔离上下文、知识外置
- 关注长时运行 agent（long-running agents）和 agent 的容错/恢复
- 参与一个开源 agent 项目，或者把 Week 12 的项目真的推给同事用起来——**有真实用户是最快的进阶方式**
