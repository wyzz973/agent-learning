# Python 能力线

**不额外开一条 Python 学习线**——每天 1 小时不够分。做法是：每周的 agent 练习顺带把该周需要的 Python 特性练掉，学完就用上，用上就记住。

每个练习文件顶部都标了"练到的 Python"。这份清单是它们的汇总，学完一条勾一条。

## 每周会练到什么

| 周 | Python 特性 | 在 agent 开发里干什么用 |
|---|---|---|
| 01 | `async`/`await`、协程对象 vs 调用、`asyncio.gather`、`Semaphore`、`async with` | 并行调多个工具 |
| 01 | 自定义异常类、`try/except/else`、异常分类 | 区分"重试能好"和"重试也没用"的错误 |
| 01 | 类型注解、`TypeVar`、`Callable`、`Literal` | 让编辑器帮你查错，也是工具 schema 的来源 |
| 01 | pydantic `BaseModel`、`Field`、嵌套模型 | 工具参数定义，模型唯一看得到的东西 |
| 01 | 装饰器、`functools.wraps`、给函数挂属性、`inspect` | `@tool` 的全部原理 |
| 01 | `os.environ`、`Path`、字典推导式、`**` 解包 | 配置加载 |
| 02 | 列表与字典的深拷贝、`dict.setdefault`、循环护栏 | 维护 messages 历史 |
| 02 | `match` 语句或字典分发 | 按 tool 名字路由到对应函数 |
| 03 | 抽象基类、`Protocol`、依赖注入 | 换模型厂商不改业务代码 |
| 04 | `pydantic` 校验器、`model_validate` | 结构化输出解析 |
| 05 | 生成器与 `yield`、文件遍历、批处理 | 文档分块与灌库 |
| 06 | `TypedDict`、`Annotated`、`Enum` | LangGraph 的 State 定义 |
| 07 | 上下文管理器 `__enter__`/`__exit__`、`contextlib` | checkpointer 与资源管理 |
| 07 | `AsyncIterator`、`async for`、`yield` in async | 流式输出 |
| 08 | 高阶函数、闭包、`functools.partial` | middleware 的组合 |
| 09 | `pytest` 参数化、fixture、mock | evals 数据集与打分器 |
| 10 | 进程与 `subprocess`、JSON-RPC、`asyncio` 流 | MCP server |
| 11 | FastAPI、依赖注入、SSE、`BackgroundTasks` | 把 agent 包成服务 |

## 三条比语法更重要的习惯

**1. 先跑，再改，再理解。** 读十遍不如改一行看它怎么变。示范代码就是给你改的——把 `gather` 换成循环，把 `Semaphore(3)` 换成 `Semaphore(1)`，看输出怎么变。**改坏了 `git checkout` 就回来了**，不要怕。

**2. 报错信息从下往上读。** Python 的 traceback 最后一行是错误类型和原因，倒数第二段是出错的那一行代码。先看这两处，中间那一大堆通常不用管。

**3. 一次只让一个测试变绿。** 不要想着一口气写完。跑 `-k 某个测试名` 单独跑一条，绿了再下一条。

## 从 vibe coding 过渡的三步

你之前是描述需求、AI 生成、你验收。现在换成：

1. **读懂**示范代码，能用自己的话说出每一行在干什么
2. **改**示范代码的参数和逻辑，预测输出，再运行验证预测
3. **照着模式**写下一个函数，卡住了先看示范，还不行才问

第 3 步卡住超过 20 分钟再来找我，而且**先要方向不要代码**——直接要答案就退回第 1 步了。
