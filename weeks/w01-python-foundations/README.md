# Week 01 — Python 工程地基

> 2026-09-07 ~ 2026-09-11 ｜ 对应 [LEARNING_PATH.md](../../LEARNING_PATH.md) 第 1 周

## 目标

把 agent 开发会反复用到的五个 Python 特性练成肌肉记忆：异步并发、重试与超时、pydantic 生成 JSON Schema、装饰器、配置加载。

这周不碰任何 agent 框架。**这五样不熟，后面每一周都会卡在语言本身而不是 agent 概念上。**

## 怎么用这个目录

五个练习文件的函数体都是 `NotImplementedError`，由我填。`test_exercises.py` 已经写好，**它就是本周的规格说明**：

```sh
uv run pytest weeks/w01-python-foundations -v   # 现在全红，这是任务清单
```

红变绿就是本周完成。看不懂某条测试在要求什么，那条测试的名字和断言就是提示。

## 自检标准

不看资料能独立做到才算过：

- [ ] 说清 `asyncio.gather` 和依次 `await` 的区别，以及为什么 agent 并行调工具必须用前者
- [ ] 手写一个带嵌套字段和字段描述的 `BaseModel`，并说出它生成的 JSON Schema 长什么样
- [ ] 说清装饰器如何在不改函数体的前提下给函数附加元数据——这是 `@tool` 的全部秘密
- [ ] 写出一个带指数退避的异步重试包装，并说明为什么超时必须和重试分开设置

## Build It — 手写版

| 文件 | 练什么 | 和 agent 开发的关系 |
|---|---|---|
| `ex1_async_basics.py` | `async/await`、`gather`、并发 vs 串行 | agent 一轮里可能要并行调 5 个工具，串行就是 5 倍延迟 |
| `ex2_retry.py` | 超时、指数退避重试、异常分类 | LLM API 超时和限流是常态不是异常；没有护栏的 agent 会挂 |
| `ex3_tool_schema.py` | pydantic → JSON Schema | 这段 JSON 就是工具定义传给模型的东西，模型只看得到它 |
| `ex4_tool_decorator.py` | 装饰器、`functools.wraps`、元数据附加 | 手写一个 `@tool`，第 3 周再看 LangChain 的版本 |
| `ex5_settings.py` | `.env` 加载、pydantic 校验、fail loud | 后面每一周都从这里读模型名、超时、轮次上限 |

## Use It — 对比版

练习跑通后，把手写版和现成库对比。**每行都要能说出那个库替我解决了什么问题**：

| 我手写的 | 现成的做法 | 差异说明了什么 |
|---|---|---|
| `ex2` 的 `with_retry` | `tenacity` 的 `@retry` | |
| `ex3` 的手工 schema | `model_json_schema()` | |
| `ex4` 的 `@tool` | `langchain.tools.tool`（第 3 周） | |
| `ex5` 的配置类 | `pydantic-settings` | |

对比结论写在这张表里，不要只是"库更方便"。

## Ship It — 带走的工件

`ex2` 的 `with_retry` 和 `ex5` 的 `Settings` 是后面每周都要用的。**本周先不提升到 `src/agentlab/`**——等第 2 周真的第二次用到它们，再按 [AGENTS.md](../../AGENTS.md) 的规则写决策记录提升。过早抽象是这周最容易犯的错。

## 运行

```sh
uv run pytest weeks/w01-python-foundations -v      # 规格说明
uv run python weeks/w01-python-foundations/ex1_async_basics.py   # 手动观察输出
```

`ex1` 和 `ex2` 的 `__main__` 会打印耗时对比，测试断言不了"快多少"，得自己看。

## 卡住的地方

（填）
