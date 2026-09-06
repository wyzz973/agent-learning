# Week 02 — 手写一个裸 agent

> 2026-09-14 ~ 2026-09-18 ｜ 对应 [LEARNING_PATH.md](../../LEARNING_PATH.md) 第 2 周

## 目标

**不用任何框架，写出一个能调用工具的 agent。**

写完这周，LangChain 的 `create_agent`、LangGraph 的 ReAct 对你就不再是黑盒——你会知道它们底下就是你写的这个循环。

## agent 是什么（一句话）

```
把消息历史发给模型
  → 模型要么说话（结束），要么说"我要调这几个工具"
  → 你执行工具，把结果追加进历史
  → 再发一次
  → 直到模型不再要求调工具，或撞上轮次上限
```

就这些。**模型本身什么都不记得**，看起来"记得"是因为你每次都把完整历史又发了一遍。

## 先跑语法热身

```sh
uv run python weeks/w02-bare-agent/00_warmup.py
```

本周重点从"异步"转到"数据结构和类"：类与 `self`、`TypedDict`、嵌套字典取值、JSON 互转、列表复制的坑、可变默认参数的坑、`match`、`Protocol`。约 15 分钟，只读只跑。

**练习里不会出现这里没讲过的语法。**

## 自检标准

不看资料能独立做到才算过：

- [ ] 画出 agent loop 的流程图，说清楚每一步谁在做什么
- [ ] 说清为什么模型"记得"上文，而模型本身不存任何状态
- [ ] 说清为什么工具执行失败要返回错误字符串，而不是抛异常
- [ ] 把 `max_iterations` 设成 2，问一个需要 3 步的问题，解释会发生什么

## Build It — 手写版

| 文件 | 练什么 | 为什么重要 |
|---|---|---|
| `00_warmup.py` | 本周全部新语法 | 先跑它，只读不写 |
| `ex1_messages.py` | 消息历史：四种角色、tool_call_id 对应 | agent 的全部记忆就是这个列表 |
| `ex2_tool_registry.py` | 工具注册、schema 导出、执行与错误处理 | 模型只看得到 schema，错误信息决定它能否自愈 |
| `ex3_agent_loop.py` | **核心循环** + 轮次护栏 | 整个 12 周最重要的一个文件 |
| `ex4_real_agent.py` | 接真实模型（裸 HTTP）+ LangSmith | 看清 wire format，接上可观测 |

## 关于测试：为什么用假模型

真实模型每次回答都不一样，没法写确定的测试。所以定义一个 `LLM` Protocol，让真模型和**照剧本演的 `FakeLLM`** 都满足它。测试全部用假的——离线、免费、结果确定。

```sh
uv run pytest weeks/w02-bare-agent -q      # 22 条规格，现在 17 红
uv run pytest weeks/w02-bare-agent -q -k TestConversation   # 一次只攻一组
```

这是测试一切不确定系统的通用手法，第 9 周做 evals 时还会用到。**不可测的东西隔离在边缘（`ex4`），核心逻辑必须可测。**

建议顺序 `ex1 → ex2 → ex3 → ex4`，它们互相依赖，跳着做会卡。

## Use It — 对比版

四个练习跑通后填这张表。**每行都要能说出框架替你解决了什么**：

| 我手写的 | LangChain 1.0 的做法 | 差异说明了什么 |
|---|---|---|
| `Conversation` 消息列表 | `langchain.messages` + `add_messages` | |
| `ToolRegistry` + 手工 schema | `@tool` 装饰器 | |
| `Agent.run` 的 while 循环 | `create_agent` | |
| `max_iterations` 护栏 | middleware / recursion_limit | |

第 3 周会正式学右边这一列，那时候回来填。

## Ship It — 带走的工件

`ex3` 的 agent loop 是后面所有周的地基。但**本周先不提升到 `src/agentlab/`**——第 3 周会用框架重写一遍，到那时才知道哪部分值得留。

## 运行

```sh
uv run pytest weeks/w02-bare-agent -v
uv run python weeks/w02-bare-agent/ex3_agent_loop.py       # 照剧本演，不联网
uv run python weeks/w02-bare-agent/ex4_real_agent.py "上海天气怎么样"   # 需要 API key
```

## 接上 LangSmith

`ex4` 的第 3 段。去 [smith.langchain.com](https://smith.langchain.com) 申请免费 key，填进 `.env`：

```
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agent-learning
```

然后用 `@traceable` 装饰 `chat` 函数。跑完去网页上看，能一层层点开每一轮的输入输出、工具调用、耗时。

**这周就接上，别拖。** 后面调 agent 全靠它，不接等于闭着眼睛调试。

## 卡住的地方

（填）
