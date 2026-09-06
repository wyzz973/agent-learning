# Week 01 — Python 工程地基

> 2026-09-07 ~ 2026-09-11 ｜ 对应 [LEARNING_PATH.md](../../LEARNING_PATH.md) 第 1 周

## 目标

把 agent 开发会反复用到的五个 Python 特性练成肌肉记忆：异步并发、重试与超时、pydantic 生成 JSON Schema、装饰器、配置加载。

这周不碰任何 agent 框架。**这五样不熟，后面每一周都会卡在语言本身而不是 agent 概念上。**

## 不知道从哪下手？按这个来

每个练习文件都是**三段坡道**，从上往下难度递增：

| 段 | 标记 | 你要做什么 |
|---|---|---|
| 第 1 段 | 「已实现，先读懂」 | 只读和跑，别改。能用自己的话说出每行在干什么 |
| 第 2 段 | 「轮到你」+ `TODO` | 结构给好了，填掉 TODO 那几行 |
| 第 3 段 | 只有签名和思路 | 照着第 1、2 段的模式自己写 |

**第一天的具体动作**，照着敲就行：

```sh
# 1. 先看一眼现在有多少红的（这是任务清单，不是失败）
uv run pytest weeks/w01-python-foundations -q

# 2. 打开 ex1_async_basics.py，只读第 1 段的 run_sequential，读到懂为止

# 3. 直接跑这个文件，看它打印什么（第 2、3 段没实现会报错，正常）
uv run python weeks/w01-python-foundations/ex1_async_basics.py

# 4. 改一下第 1 段：把 slow_double 的 delay 改成 0.5，再跑，看耗时怎么变
#    改坏了就 git checkout weeks/w01-python-foundations/ex1_async_basics.py 还原

# 5. 现在做第 2 段的 TODO，只让一个测试变绿：
uv run pytest weeks/w01-python-foundations -q -k concurrent_preserves
```

**一次只攻一个测试。** `-k 关键词` 只跑名字匹配的那条。绿了再下一条，不要想着一口气写完。

报错看不懂？**traceback 从下往上读**：最后一行是错误类型和原因，倒数第二段是出错的代码行。中间那一大堆通常不用管。

## 完成标准

```sh
uv run pytest weeks/w01-python-foundations -q   # 27 条全绿
```

进行中提交用 `./check.sh --wip`（跳过测试），周五全绿了再跑完整的 `./check.sh` 并打 tag。

同时练到的 Python 特性见 [PYTHON_TRACK.md](../../PYTHON_TRACK.md)。

## 自检标准

不看资料能独立做到才算过：

- [ ] 说清 `asyncio.gather` 和依次 `await` 的区别，以及为什么 agent 并行调工具必须用前者
- [ ] 手写一个带嵌套字段和字段描述的 `BaseModel`，并说出它生成的 JSON Schema 长什么样
- [ ] 说清装饰器如何在不改函数体的前提下给函数附加元数据——这是 `@tool` 的全部秘密
- [ ] 写出一个带指数退避的异步重试包装，并说明为什么超时必须和重试分开设置

## Build It — 手写版

每个文件的第 1 段我已写完，你从第 2 段开始动手。

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
