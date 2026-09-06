# 资源清单与避坑指南

## 一、必读（优先级最高，总共不到 3 小时，但决定你的品味）

| 资源 | 为什么读 |
|---|---|
| [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Agent 领域最重要的一篇文章。核心观点：**先问"这该是 workflow 还是 agent"**，大部分场景 workflow 就够了。五种工作流模式（prompt chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer）是行业通用语言 |
| [Anthropic: Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 2026 年 agent 工程的核心命题。prompt 措辞早就不是瓶颈了，"每一轮给模型看什么"才是 |
| [LangChain v1 发布说明](https://docs.langchain.com/oss/python/releases/langchain-v1) | 一次读完，避免踩 0.x 老教程的坑 |
| [LangChain & LangGraph 1.0 官方博客](https://www.langchain.com/blog/langchain-langgraph-1dot0) | 理解两个库的定位分工 |

## 二、官方动手资源（主力）

| 资源 | 说明 |
|---|---|
| [langchain-ai/langchain-academy](https://github.com/langchain-ai/langchain-academy) | **官方免费课程，本计划 Week 6-8 的主线教材。** Module 0 环境，Module 1-5 由浅入深讲 LangGraph（状态、记忆、human-in-the-loop），Module 6 讲部署。全是可运行 notebook，配 LangGraph Studio |
| [docs.langchain.com](https://docs.langchain.com/) | 唯一可信的 API 参考。**只看 v1/Python 版本** |
| [LangSmith](https://smith.langchain.com) | 免费额度够学习用。Week 2 就接上 |
| [AI Agents in LangGraph (DeepLearning.AI)](https://www.deeplearning.ai/courses/ai-agents-in-langgraph) | 免费旁听，1.5 小时短课，适合周末看。注意：部分内容基于旧版 API，看思路别抄代码 |

## 三、中文资源（适合周末补课，别当主线）

- [黑马程序员 LangChain+LangGraph 开发实战](https://www.bilibili.com/video/BV178w1z7EHQ/) — 覆盖到 LangSmith 监控调试评估，体系较全
- [LangGraph 保姆级教程](https://www.bilibili.com/video/BV1WqLi6mEgp/) — 组件级讲解
- [编程导航：AI Agent 应用开发学习路线](https://www.codefather.cn/course/1789189862986850306/section/1990748661016997890) — 中文体系化路线参考
- [知乎：2026 年 AI Agent 学习计划](https://zhuanlan.zhihu.com/p/1990404048021652655)

> 中文视频课的通病是版本滞后和"跟着敲一遍"的假学习感。**工作日 1 小时不要看视频**，留到周末，且看完必须自己复现一遍才算数。

## 四、进阶/参考

- [O'Reilly: The AI Agents Stack (2026)](https://www.oreilly.com/radar/the-ai-agents-stack-2026-edition/) — 全景技术栈地图
- [Sourcegraph: Context Engineering 实践指南](https://sourcegraph.com/blog/context-engineering)
- [awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) — evals / memory / MCP / 可观测的资源汇总
- [30+ LangChain & LangGraph 项目点子](https://www.codersarts.com/post/30-langchain-langgraph-project-ideas-to-build-in-2026-beginner-to-advanced) — Week 12 选题时翻一翻

---

## 五、七个最容易踩的坑

**1. 跟着 0.x 教程写 1.0 代码**
看到 `LLMChain`、`initialize_agent`、`AgentExecutor`、`ConversationBufferMemory`、`from langchain.chains import ...` —— 立刻关掉。这些在 1.0 里已迁移到 `langchain-classic`。新写法是 `create_agent` + middleware。

**2. 把 LangChain 当成一门要"学完"的框架**
LangChain 的 API 面积极大，但你实际只需要 5 个入口（`init_chat_model` / `@tool` / `create_agent` / messages / middleware）。剩下的用到再查。**背 API 是最没价值的投入。**

**3. 跳过裸手写直接上框架**
最常见的失败模式。结果是：能跑通教程，一改需求就懵，报错完全看不懂。Week 2 的 100 行代码是整份计划性价比最高的部分。

**4. 在 RAG 上陷太深**
RAG 是 agent 的一个工具。很多人花 6 周调 chunk size 和 rerank，却从没做过一次 eval。够用就走。

**5. 太晚接 LangSmith**
不接可观测就调 agent，等于闭着眼睛调试分布式系统。**Week 2 就接**，成本是 3 行配置。

**6. 一上来就搞多智能体**
"5 个 agent 协作"听起来很酷，实际上大部分场景单 agent + 设计良好的工具更稳、更便宜、更好调。多 agent 的正确用法是**用子 agent 隔离上下文**（各自干净的上下文窗口，只把浓缩结论返回主 agent），而不是为了拟人化分工。

**7. 不做 evals**
只有 52% 的生产团队有 evals。没有评估集，你所有的"我改进了 prompt"都只是感觉。这也是 12 周后你和其他人最大的差距点。

---

## 六、框架选型：为什么是 LangGraph

你的选择（LangChain + LangGraph + LangSmith）是对的，理由是**这一套的"学习价值"最高**：它逼你显式处理状态、控制流、持久化、评估——这些概念换到任何框架都通用。

其他框架，知道定位即可，不用现在学：

| 框架 | 定位 | 什么时候看 |
|---|---|---|
| **LangGraph** | 有状态、可控、生产级编排。样板代码多但控制力最强 | 你的主线 |
| **Pydantic AI** | 类型安全、抽象轻。Python 团队喜欢 | 觉得 LangChain 太重时的替代品 |
| **OpenAI Agents SDK** | 厂商原生，handoff 模型简洁 | 绑定 OpenAI 生态时 |
| **Claude Agent SDK** | 内置文件系统/shell 工具，做编码类和长任务 agent 省事 | 做偏 coding agent 时 |
| **CrewAI / AutoGen** | 角色扮演式多智能体，上手快、可控性弱 | 快速原型、demo |

选型的三个判断依据：语言（Python/TS）、是否需要跨厂商可移植、控制流有多复杂。**框架和场景的匹配度，比框架本身的好坏更重要。**

---

## 七、关于你现有基础的一个实话

你懂 Transformer 和 CNN，这在 agent 开发里的直接用处比你想象的小——你不会训练模型，你在**编排**模型。它真正帮到你的地方只有三个：理解 context window 为什么是硬约束、理解 temperature/top-p 在调什么、理解为什么模型会"忘记"中间的内容（lost in the middle）。

真正需要补的是工程侧：async、pydantic、类型、依赖管理、错误处理、可观测、评估。所以 Week 1 别跳。

## 八、12 周后你应该能说出这三句话

1. "我这个 agent 在 30 条测试集上的工具调用准确率是 X%，最常见的失败是 Y。"
2. "这个场景我用的是 workflow 不是 agent，因为控制流是确定的，能省 60% 的 token。"
3. "上下文超了我用 summarization middleware 压缩，关键事实写进长期 store，不靠模型记。"

能自然说出这三句，你就已经在行业里前 20% 了。
