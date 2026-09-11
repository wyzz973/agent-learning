# 定制课程的调研依据

核查日期：2026-09-11。依据为官方项目、官方文档与教学机构资料；不是热度榜。实现环境实测 langchain 1.4.0、langchain-core 1.6.2、langgraph 1.2.11、pydantic 2.13.5，精确依赖由 uv.lock 管理。

## 调研怎样影响安排

- 采用 PRIMM 的预测、运行、观察、修改、独立创作结构；按你的基础缩小每次新语法量，增加隔天重写。这是教学设计判断，不把面向学校教学的研究直接当成你的效果保证。
- 单 agent、工具与状态先形成可观察闭环；多 agent 用同一评估集证明收益，不能因为前沿就默认增加。
- 知识来源、结构化数据、评估与失败路径贯穿项目。Schema 合法不等于事实正确，节点测试不等于用户流程完成。
- 借鉴长任务 harness 的进度工件与恢复思路：规则、实际学习状态、任务卡、Git 和验证记录分开保存，减少换模型后重新猜测。
- “最新”按可核查的稳定实践与项目当前材料选取：上下文管理、持久化执行、Skills、MCP、规划协作、权限隔离和评估。未来具体接口在开周时再核查，课程不绑定某个最强模型。

## 来源与阅读范围

### python

[Python 官方教程](https://docs.python.org/3/tutorial/controlflow.html)。基础写法按需查，不把整本教程塞进每日作业。

### primm

[Raspberry Pi Foundation：PRIMM](https://www.raspberrypi.org/blog/using-primm-to-teach-programming-a-new-short-course-for-educators/)。2026-02-25；支持先读与预测、逐步独立的教学安排，不能据此保证成人学习者的具体完成时间。

### tools

[LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)。核查工具描述、参数 schema 与对象返回。

### patterns

[Anthropic：Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)。2024-12-19；用于稳定范式分类，页面提示部分工具信息已有变化，不照抄旧 API。

### graph

[LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)。官方文档 MCP 已读 State、Nodes、Edges 与 compile。

### persistence

[LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)。内存检查点与持久化存储要分开证明。

### interrupts

[LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)。核查 interrupt/Command(resume=...) 与同一 thread 恢复语义。

### structured

[LangChain Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)。工具对象返回与 agent 最终结构化输出不同；能力和策略依实际模型支持而定。

### evals

[Anthropic：Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)。2026 年工程文章；任务、评分与完整运行轨迹分开。

### context

[Anthropic：Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)。上下文选择与外部证据管理，不把更长上下文等同于更可靠。

### harness

[Anthropic：Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)。2025-11-26；跨会话进度与验证工件启发本仓库的交接文件。

### retrieval

[LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)。开周核查具体向量库/embedding 接口，再与关键词基线比较。

### mcp

[MCP 官方架构](https://modelcontextprotocol.io/docs/learn/architecture)。本次链接跳转到 2026-07-28 版本架构页；具体协议和 SDK 开周再次核查兼容性。

### mcp-sdk

[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)。D32 开周按实际 SDK 版本实现并测试 stdio，不把工具 schema 测试当调用成功。

### skills

[Agent Skills 官方说明](https://agentskills.io/home)。按需加载流程说明与参考材料；不等同于执行工具，也不授予系统权限。

### multiagent

[LangChain 多 agent 文档](https://docs.langchain.com/oss/python/langchain/multi-agent)。按具体任务选择协作方式，开周核查当前 API。

### langsmith

[LangSmith Observability](https://docs.langchain.com/langsmith/observability)。本地日志为基础；外部追踪可选，先确认数据内容与账号配置。

### fastapi

[FastAPI 官方教程](https://fastapi.tiangolo.com/tutorial/)。服务课程按当前依赖核查请求、校验、异步与部署行为。

### streaming

[LangGraph Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)。区分事件、节点更新、模型文本与最终产物。

### pi

[Pi 官方仓库](https://github.com/earendil-works/pi)。本次已查看；用于 coding agent、runtime、工具和状态的能力对照，不照搬整个工程。

### deerflow

[DeerFlow 官方仓库](https://github.com/bytedance/deer-flow)。本次已查看；用于应用目标参考，不把完整上游功能当一个月作业。

## 两种核查状态

本次已读取的核心内容：PRIMM、Python 控制流、LangChain 工具/结构化输出、LangGraph 图与中断相关文档、Anthropic 范式/上下文/harness/评估、MCP 架构、Skills、Pi、DeerFlow、Codex 与 Claude 规则发现。RAG、具体持久化驱动、服务部署等后续接口作为开周必须再次核查的来源，不宣称已运行其示例。

## 规则加载依据

[Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 与 [Claude Code Memory](https://code.claude.com/docs/en/memory) 支持本仓库显式读取目标模块规则、共享文本、共享状态的做法。文件存在/链接正确属于本机结构验证，不代表已启动全部第三方 harness 做过验收。
