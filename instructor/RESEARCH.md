# 雾岛图书馆的Agent技术依据

核查日期：**2026-09-13**。本文件是教师选材与任务设计依据，学习者仍从根 README 的当前 Notebook 进入。

选材核查包含官方文档、部分实现源码、论文摘要与本地依赖版本。**调研不等于已经实现、安装或运行。** 下文的实验设计是教学建议，不登记本人完成，也不替代各任务的真实结果。

## 先把不同层次放对位置

| 层次 | 解决的问题 | 在同一个研究助手中的作用 |
|---|---|---|
| 模型与模型训练 | 模型是否具备理解、生成、选择动作的能力 | 选择支持所需接口的模型；应用调用不会自动训练模型 |
| 工具与反馈循环 | 怎样获取外部事实、执行动作，并利用结果继续 | 搜索、读原文、核验；实际结果进入下一次模型调用 |
| 状态与控制 | 当前做到哪里，下一步走哪里，何时停止 | 保存问题、资料、报告、计数和路由条件；state 不只是 messages |
| 记忆 | 哪些信息需要跨轮、跨任务保留 | 区分任务检查点、已确认偏好、失败经验和资料库 |
| 上下文工程 | 本轮模型应该看到哪些信息与工具 | 选择证据、限制工具、压缩历史、保留原始资料位置 |
| 规划与委派 | 怎样组织较大的任务 | 子问题、完成条件、独立研究上下文；收益需要实验验证 |
| MCP | 不同程序怎样发现并调用能力 | 同一资料工具可以由独立客户端调用，通信协议不替代工具实现 |
| Skills | 怎样在需要时提供任务方法 | 读取适用说明，再按需加载步骤与参考资料；文件本身不授予执行权限 |
| 评估与交付 | 如何知道结果可用、能否重复运行 | 证据支持、任务覆盖、故障恢复、服务入口和回归实验 |

这些机制可以共存。MCP 不是工具调用的替代品，Skills 不是 MCP 的下一代，记忆不是 RAG 的替代品，多 agent 也不天然优于单 agent。课程按作品遇到的局限引入机制，不编排一条“旧技术被新技术淘汰”的故事。

## 论文：解释方法来源，分清运行时与训练

| 原始来源 | 本轮核实的主张与边界 | 怎样影响任务设计 |
|---|---|---|
| [ReAct](https://arxiv.org/abs/2210.03629)，2022/2023 | 把推理过程与任务动作交替组织，通过外部观察支持后续决策。这是方法范式，不是所有供应商都实现同一套 Thought/Action 文本字段。 | 在已有研究助手中断开、恢复工具反馈，检查动作与观察的因果关系；不要求输出模型隐藏推理。 |
| [Toolformer](https://arxiv.org/abs/2302.04761)，2023 | 用自监督训练让模型学习调用哪些 API、何时调用、如何提供参数及利用结果。 | 区分“训练模型学会用工具”和“应用注册工具让现有模型调用”；给函数加 `@tool` 不能称为复现 Toolformer。 |
| [Reflexion](https://arxiv.org/abs/2303.11366)，2023 | 把任务反馈变成反思文本，存入情节记忆，影响之后的尝试，不更新模型权重。 | 保留一次失败的检查结果，让本人写出可用经验并用于新尝试；只有一句“再反思一下”或重复调用不能证明实现了该方法。 |

这里借鉴机制，不复述论文排行榜，也不把课程中的缩小实验当作论文复现。

## 当前框架与本地版本

本地版本由 `importlib.metadata.version` 读取；远端版本由 PyPI JSON API 核查。文档可能跟随主分支更新，编写 Notebook 时仍需以本地签名和实际行为验证。

| 包 | 本地环境 | 本轮远端核查 | 使用边界 |
|---|---|---|---|
| `langchain` | 1.4.0 | [PyPI：1.4.0](https://pypi.org/pypi/langchain/json)，2026-09-03 上传 | 当前主线的模型、消息、工具与 agent 接口 |
| `langgraph` | 1.2.11 | [PyPI：1.2.11](https://pypi.org/pypi/langgraph/json)，2026-08-11 上传 | 状态、控制、检查点与恢复 |
| `langchain-core` | 1.6.2 | 未另查最新版本 | 共享消息、工具和 Runnable 类型，不能忽略其兼容性 |
| `langchain-deepseek` | 1.1.0 | 未另查最新版本 | 已配置模型的提供方适配包；参数与异常行为仍需单独核对 |
| `langchain-mcp-adapters` | 0.3.2 | 核查了官方客户端实现，未另查最新版本 | 把 MCP 能力转换为 LangChain 工具，会话生命周期仍重要 |
| `mcp` | 1.30.0 | 核查 1.x 文档和本地支持的协议版本 | 锁定 `mcp<2` 的维护线，不能照抄 2.x API |
| `deepagents` | **未安装** | [PyPI：0.7.13](https://pypi.org/pypi/deepagents/json)，2026-09-02 上传 | 目前只完成资料核查，不能称为本地集成通过 |

### LangChain、LangGraph 与 Deep Agents 的关系

[LangChain middleware 文档](https://docs.langchain.com/oss/python/langchain/middleware/overview)说明：`create_agent` 返回编译后的 LangGraph；middleware 的钩子在其中运行，整个 agent 还可以放入更大的图中。因而学习 LangGraph 是进一步掌控状态和拓扑，不是把 LangChain 丢掉重做。

[自定义 middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)提供模型/工具调用前后的切入点。本人可在一次工具故障中验证错误如何回传、调用怎样停止；只在 prompt 中说“请重试”不能替代这些程序控制。

[上下文工程文档](https://docs.langchain.com/oss/python/langchain/context-engineering)区分本轮模型输入、工具可访问的信息和运行过程中的状态变化。`request.override(messages=...)` 可以只改变本轮输入，而状态更新需要明确的更新机制。任务应同时展示“模型本轮看到的内容”和“实际保存的状态”，避免把删掉上下文等同于删掉记录。

[Deep Agents 实现](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/graph.py)围绕这些组件组装运行设施：配置 `skills` 时接入 Skills middleware，配置 `memory` 时接入 Memory middleware，并组合文件系统、子 agent 等能力。它是集成参照，不是替代上述机制的新模型。

## 记忆、上下文与规划怎样教到真实机制

| 官方来源 | 核实后的区分 | 对 task 的影响 |
|---|---|---|
| [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | Checkpointer 保存特定 thread 的图状态；Store 保存跨 thread 的应用数据。`InMemorySaver` 与 `InMemoryStore` 都不会因为名字含 memory/store 就跨进程存活。 | 先恢复同一任务，再用另一任务读取确认过的偏好；声称跨进程持久化时必须结束进程再验证磁盘后端。 |
| [Deep Agents Memory](https://docs.langchain.com/oss/python/deepagents/memory) | 可通过 `memory=` 加载文件中的长期指令；底层 backend 和 namespace 决定保存在哪里、谁可访问。文字记忆不等于模型权重更新。 | 用用户 A/B 与新 thread 检查作用域；原始网页不能未经选择就变成长期可信指令。 |
| [Deep Agents Context Engineering](https://docs.langchain.com/oss/python/deepagents/context-engineering) | 选择、压缩、外置大结果与子 agent 上下文隔离处理不同问题，原始资料仍需可追溯。 | 在同一研究问题中增加长正文，比较删原文、保留摘要和保存可重读原文的结果；检查关键事实是否丢失。 |
| [Deep Agents Skills](https://docs.langchain.com/oss/python/deepagents/skills) | 读取配置路径的元数据供发现，相关任务再通过文件读取取得完整方法；方法与工具能力是不同层。 | 查看真实读取轨迹，确认只看过 description 还是读过完整 SKILL；Python 关键词判断实验只代表手动加载，不代表完整框架行为。 |
| [Deep Agents Subagents](https://docs.langchain.com/oss/python/deepagents/subagents) | 常规同步委派为子任务建立独立上下文，主任务等待最终结果。异步委派与动态编排另有接口。 | 用两个来源方向独立研究，再检查父任务究竟得到摘要还是完整过程；隔离可能减少干扰，也可能漏失证据，不能预设一定更好。 |

### Deep Agents 的版本与 Beta 边界

**从 v0.7 起，任务规划需要显式启用** `TodoListMiddleware`；不能写成“当前默认提供 write_todos”。待办列表记录任务状态，不能证明实际工作已经完成。[官方 Task planning](https://docs.langchain.com/oss/python/deepagents/overview#task-planning)

本轮将公开、常规使用的模型/工具接口、状态图、检查点、Store 和 middleware 作为教学核心。这里的“核心”是选材判断，不是对未来所有版本不变的保证。

以下接口单独标为仍在演进的材料，不作为基础能力验收的隐含依赖：

- [Dynamic subagents](https://docs.langchain.com/oss/python/deepagents/dynamic-subagents)：正文明确依赖 Beta interpreter，API 与生命周期可能随版本改变；动态代码分发不等同于普通 `subagents=` 配置。
- [Profiles](https://docs.langchain.com/oss/python/deepagents/profiles)：官方导航标 Beta，用于模型/提供方对应的运行配置；需要时按锁定版本验证。
- [Grading rubrics](https://docs.langchain.com/oss/python/deepagents/rubric)：`RubricMiddleware` 明确为 Beta；模型评分可以驱动修订，但不是客观正确性的保证，也不代替本仓库固定评估样本。

## MCP：规范版本、SDK 版本与协商结果分别记录

本轮访问 [MCP latest](https://modelcontextprotocol.io/specification/latest) 重定向到 **[2026-07-28 规范](https://modelcontextprotocol.io/specification/2026-07-28)**。该版本的基础页面强调无状态、自包含请求与逐请求能力协商；变化见[官方变更说明](https://modelcontextprotocol.io/specification/2026-07-28/changelog)。

本地 `mcp==1.30.0` 的 `LATEST_PROTOCOL_VERSION` 是 **2025-11-25**，与2026-07-28最新规范不同。MCP委托编写时必须同时记录SDK、服务端和实际协议版本；连接成功后再检查真实工具请求和错误响应。当前雾岛MCP关卡尚未执行，不能以本地安装版本推断完成了新规范实验。Python接口参照[SDK 1.x客户端文档](https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/docs/client.md)。

[LangChain MCP Adapters 实现](https://github.com/langchain-ai/langchain-mcp-adapters/blob/main/langchain_mcp_adapters/client.py)提供显式 session，并负责把连接转换为可调用工具。教学验收需要分别观察发现、实际工具请求、错误响应和模型取得结果，而非只查看工具名称列表。

[Skills over MCP 工作组](https://modelcontextprotocol.io/community/working-groups/skills-over-mcp)是需要单独关注的协议扩展方向。工作组/扩展页面存在，不能证明当前 SDK、服务器和所有宿主都已经支持。普通 [Agent Skills 文件规范](https://agentskills.io/specification)与通过 MCP 分发 Skills 也不是同一项验收。

## 成熟课程与产品案例承担不同角色

| 来源 | 本轮确认的内容 | 采用方式与限制 |
|---|---|---|
| [LangChain Academy](https://github.com/langchain-ai/langchain-academy) | 配套 Notebook 用连续的状态、路由、循环和持久化案例展开框架。 | 借鉴机制的前后联系；正文讲授仍需在本仓库 Notebook 内补齐，不只复制短代码。 |
| [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch) 与 [Academy 项目课程](https://academy.langchain.com/courses/deep-research-with-langgraph) | 配套五本 Notebook 覆盖范围、研究 agent、MCP、supervisor、完整研究系统；课程页列约 1.5 小时视频。 | 采用同一研究系统的演进结构；视频长度不等于独立实现时长，五本官方 Notebook 也不机械等同于五个适合初学者的 task。 |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | [GitHub API](https://api.github.com/repos/langchain-ai/open_deep_research) 本轮返回 `archived=true`。配套 from-scratch 仓库[未归档](https://api.github.com/repos/langchain-ai/deep_research_from_scratch)。 | 前者只作完整历史实现和评估设计参照，不能称持续维护的生产依赖；后者未归档也不等于本地运行已验证。 |
| [DeerFlow 2.0](https://github.com/bytedance/deer-flow/blob/main/README.md) | 当前产品主线建立在 LangChain/LangGraph 上，整合文件系统、记忆、Skills、沙箱与子 agent；原研究框架在独立 1.x 分支。 | 用作后期产品行为和系统边界对照，不要求入门时读完整工程；本轮未部署、未运行它，不把产品功能表当成本仓库已有能力。 |

## 把资料转成同一个 agent 的实验

下面是已有八个 module 内可采用的机制任务，不是新增日历、目录或完成清单。每项先保留基线，再由本人改关键机制，以同一批输入对照，并用新输入迁移。

| 当前助手的局限 | 引入机制 | 本人负责的实验 | 迁移与验收 |
|---|---|---|---|
| 工具失败后直接中断或反复尝试 | 错误观察与 middleware 控制 | 注入一次检索失败，自己实现错误回传、次数限制与终止，观察下一次模型请求 | 换成空结果与非法参数，分别检查恢复和明确失败；不能吞错报成功 |
| 审核或中断后丢失任务 | Checkpointer + interrupt | 恢复同一份研究草稿，对照新 thread、同 thread 和新内存后端 | 使用磁盘后端后再做跨进程实验；不能靠同一内核变量宣称持久化 |
| 新任务忘记已确认的偏好 | Store / namespace | 自己选择值得保存的研究偏好，让新任务读取；检查不同用户隔离 | 更正一项偏好并验证新任务使用新值；不要把旧报告当通用事实 |
| 长资料挤掉问题、来源或最新反馈 | 上下文选择、压缩、外置结果 | 自己控制本轮输入，记录保存状态与模型输入的区别，并保留原文定位 | 换长资料，核对核心事实与引用；比较输入缩小是否损害正确性 |
| 多要求问题只答其中一项 | 显式计划与完成条件 | 用同一任务对照有无计划，定义子问题与可核验产物；分析失败后修订计划 | 更换要求顺序或取消一项，检查实际覆盖；待办“完成”不等于结果合格 |
| 多方向研究互相干扰 | 子 agent 上下文隔离与结果契约 | 选择可独立的子问题，设计证据回传，比较单 agent 与委派方案 | 用存在冲突来源的任务比较覆盖与错误；不只比较速度或 agent 数量 |
| 工具只能在一个进程内用 | MCP 发现、调用与适配 | 保留同一检索逻辑，通过协议使用，并记录实际协商版本与错误 | 用另一客户端完成同一查询；底层函数成功不替代完整协议链路 |
| 同类核查每次都要重复解释方法 | Skills 按需加载 | 本人编写方法、适用说明和加载策略，检查实际正文读取与结果变化 | 换同类问题及无关问题，观察方法是否有效、是否不必要地进入上下文 |

### M07 的 Deep Agents 集成对照

在本人已理解工具、状态、记忆、上下文和规划后，用 `create_deep_agent` 重新组装**同一个资料研究助手**，复用 M06 的输入与评估规则，比较完成覆盖、来源支持、错误恢复、调用次数和上下文记录。规划显式启用；需要的 Skills/记忆后端和子 agent 配置都在实验中列明。

本人要回答“框架接手了哪些原有职责、哪些依然由我定义”，而非只看新工厂函数能否运行。当前 Deep Agents 未安装，该集成仍是设计；真正完成需要锁定依赖、执行模型、检查工具轨迹和结果后再登记。

## 记录证据的界限

- 本文件记录技术选材与环境版本；雾岛各关是否实际运行以当前课程validation记录为准。
- 实验设计由本仓库根据学习目标推导；引用说明机制来自哪里，不代表作者认可本课程或保证学习效果。
- 开课时再次核对会变化的 API、默认行为和能力边界；正文应保留失败现象、关键数据表示与本人控制点，避免退回“API 名称 + 简单填空”。
