# Week 03 — LangChain 1.0 核心

> 2026-09-21 ~ 2026-09-25 ｜ 对应 [LEARNING_PATH.md](../../LEARNING_PATH.md) 第 3 周
> 基于实测版本：langchain 1.4.0 / langchain-core 1.6.2 / langgraph 1.2.11

## 目标

**用 LangChain 1.0 重写你 w02 手写的一切，然后逐行对比。**

你已经知道 agent 是什么了。这周不是学新概念，是把手写的东西换成框架的五个入口，并搞清楚**框架替你做了什么、什么时候不该用它**。

## ⚠️ 先看这条

网上 90% 的 LangChain 教程是 0.x 的。看到这些立刻关掉：

```
LLMChain   initialize_agent   AgentExecutor   ConversationBufferMemory
from langchain.chains import ...
```

它们在 1.0 已经移到 `langchain-classic` 包。只认下面五个入口。

## 五个入口 ↔ 你 w02 写的东西

| LangChain 1.0 | 你 w02 手写的 |
|---|---|
| `langchain.messages` 的四个消息类 | `{"role": ..., "content": ...}` 字典 |
| `@tool` | 手写装饰器 + `__tool__` 属性 |
| `create_agent` | 那一百行 `Agent.run` 循环 |
| `init_chat_model("provider:model")` | `OpenAICompatLLM` + 双向格式转换 |
| `content_blocks` | `complete` 里的响应解析 |

## 先跑两个热身（顺序别反）

```sh
uv run python weeks/w03-langchain-core/00_warmup.py        # ① Python 语法
uv run python weeks/w03-langchain-core/01_langchain_api.py  # ② LangChain 五入口
```

**`00` 是这周练习用到的每一个 Python 写法**，十一节：`isinstance`、两层嵌套循环、
`eval`、`raise ... from`、嵌套 f-string 格式化、字典查重、继承与覆盖、负数下标、
`json.loads`、`match`、`lambda`。每节标题都标了「用在 exN」，练习卡住时按标题回来查。

**`01` 是五个 API 入口**的最小例子。它的第 3 节会打印 `create_agent` 产出的消息序列：

```
HumanMessage → AIMessage(tool_calls) → ToolMessage → AIMessage
```

**和你 w02 跑出来的四条一模一样。**这是本周最重要的一句话：`create_agent` 底下就是你写的那个循环。

## 自检标准

- [ ] 说出 `create_agent` 内部做了哪几件你 w02 手写过的事
- [ ] 不看文档写出一个带 3 个工具的 `create_agent`
- [ ] 用 `init_chat_model` 在两个厂商间切换，**除模型标识外不改任何代码**
- [ ] 说清工具抛异常时，`create_agent` 默认行为和你 w02 的实现差在哪、为什么

## Build It — 四个练习

| 文件 | 练什么 |
|---|---|
| `00_warmup.py` | 本周用到的十一个 Python 写法，先跑，只读不写 |
| `01_langchain_api.py` | 五个 API 入口的最小例子 |
| `ex1_messages.py` | 消息类型；把 w02 的字典格式迁移过来 |
| `ex2_tools.py` | `@tool`、pydantic 约束、工具重名检测 |
| `ex3_create_agent.py` | **核心**：`create_agent`、执行轨迹、错误中间件 |
| `ex4_switch_model.py` | `init_chat_model` 一行换厂商（无测试，手动跑） |

```sh
uv run pytest weeks/w03-langchain-core -q      # 19 条规格，现在 16 红
```

测试仍然完全离线：`ScriptedChatModel` 继承 `GenericFakeChatModel` 并补一个 `bind_tools`。你 w02 用 Protocol 造假模型的思路，这周变成"继承并覆盖一个方法"。

## 本周最反直觉的一件事

**`create_agent` 默认不接住工具异常。**工具抛 `ValueError`，整个 `invoke()` 就炸了。

而你 w02 手写的 `ToolRegistry.call` 是主动接住所有异常、把错误文本还给模型的——**这一点上你手写的版本比框架的默认行为更健壮**。

要恢复那个行为得显式加中间件：

```python
create_agent(..., middleware=[ToolErrorMiddleware(on_error=...)])
```

框架不是什么都替你想好了，它把这类决策留给你。这条纠正了"用了框架就万事大吉"的预期，是 `ex3` 第 3 段的练习内容。

## Use It — 对比表（练习跑通后填）

| 我 w02 手写的 | LangChain 的对应物 | 它多做了什么 / 少做了什么 |
|---|---|---|
| `Agent.run` 的 while 循环 | `create_agent` | |
| `max_iterations` 护栏 | `ModelCallLimitMiddleware` | |
| `ToolRegistry.call` 的异常处理 | `ToolErrorMiddleware`（**默认不启用**） | |
| `with_retry`（w01） | `ToolRetryMiddleware` | |
| `_to_wire_message` 格式转换 | `init_chat_model` 内置 | |

最后一列是重点。**不要只写"框架更方便"**，要写清它到底代劳了哪一步。

## Ship It

这周结束时，`src/agentlab/` 该收哪些东西开始有答案了——你会看到哪些是框架已经做好的（不必自己留），哪些是框架没做的（值得沉淀）。按 [AGENTS.md](../../AGENTS.md) 的规则，提升要写决策记录。

## 运行

```sh
uv run pytest weeks/w03-langchain-core -v
uv run python weeks/w03-langchain-core/ex3_create_agent.py          # 离线，照剧本演
uv run python weeks/w03-langchain-core/ex4_switch_model.py "上海天气？"  # 需要 key
```

## 卡住的地方

（填）
