# Python 速查卡

写代码时对着抄。按**"我想做什么"**查，不是按语法名查。

可运行的详细版在每周的 `00_warmup.py`，跑一遍看输出比读十遍管用。

## 异步

| 我想做 | 这样写 |
|---|---|
| 定义一个能等待的函数 | `async def f() -> int:` |
| 等一个 async 函数出结果 | `result = await f()` |
| 只是造一张"待办卡片"，先不跑 | `card = f()` ← 没有 await 就没执行 |
| 一堆协程一起跑 | `results = await asyncio.gather(a(), b(), c())` |
| 列表里的协程一起跑 | `await asyncio.gather(*我的列表)` |
| 让失败的返回异常而不是炸掉整批 | `await asyncio.gather(*任务, return_exceptions=True)` |
| 睡一会儿 | `await asyncio.sleep(0.5)` |
| 限制同时最多 N 个 | `sem = asyncio.Semaphore(N)` 然后 `async with sem:` |
| 给一段代码设超时 | `async with asyncio.timeout(5): ...`（超时抛 `TimeoutError`） |
| 跑一个 async 程序 | `asyncio.run(main())` |

## 异常

| 我想做 | 这样写 |
|---|---|
| 抛一个错 | `raise ValueError("说清楚哪里错了")` |
| 接住并读它 | `except ValueError as error:` 然后用 `error` |
| 接住好几种 | `except (TypeError, ValueError) as error:` |
| 接住一个变量里存的类型 | `except 我的元组变量 as error:`（元组可以是参数传进来的） |
| 自定义一个异常 | `class MyError(Exception):` 然后 `def __init__(self, ...)` 里 `super().__init__(消息)` |
| 在异常里存额外信息 | `self.code = code`，接住的人用 `error.code` 读 |
| 重新抛出刚接住的 | `raise`（光秃秃一个 raise，保留原始堆栈） |

⚠️ **函数走到末尾没 return 就返回 `None`**，不报错。循环里 `return` 了不代表所有路径都 `return` 了。

⚠️ **第三方库有自己的异常体系**：`httpx.ConnectError` 不是内置的 `ConnectionError`，`except ConnectionError` 接不住它。

## 列表与字典

| 我想做 | 这样写 |
|---|---|
| 对每个元素做处理，得到新列表 | `[f(x) for x in 列表]` |
| 再加个过滤 | `[x for x in 列表 if x > 0]` |
| 造字典 | `{k: f(k) for k in 键列表}` |
| 只保留字典里存在的键 | `{k: d[k] for k in 想要的 if k in d}` |
| 把列表摊成多个位置参数 | `f(*列表)` |
| 把字典摊成多个关键字参数 | `f(**字典)` |
| 两个列表配对遍历 | `for a, b in zip(x, y, strict=True):` |
| 遍历时要序号 | `for i, x in enumerate(列表):` |
| 拆开元组 | `for name, value in [("a", 1), ("b", 2)]:` |

## 函数

| 我想做 | 这样写 |
|---|---|
| 强制调用方写参数名 | `def f(a, *, b, c):` ← 星号后面必须 `b=1` 这样传 |
| 把函数当参数传 | 直接传函数名，不加括号：`g(f)` 而不是 `g(f())` |
| 把带参数的函数变成不带参数的 | `functools.partial(f, 那个参数)` |
| 同上，用 lambda | `lambda x=当前值: f(x)` ← **必须 `x=当前值`**，见下 |
| 在函数里定义函数并用到外面的变量 | 直接写内层 `def`，它能读到外层变量（闭包） |
| 在内层函数里改外层的变量 | 内层第一行写 `nonlocal 变量名` |

⚠️ **lambda 记的是变量不是值**。`[lambda: i for i in range(3)]` 三个都返回 `2`；要写 `[lambda i=i: i for i in range(3)]`。

## 装饰器

| 我想做 | 这样写 |
|---|---|
| 理解 `@foo` 是什么 | `@foo` 写在 `def bar` 上面 = `bar = foo(bar)` |
| 写一个改变行为的装饰器 | 内部定义 `wrapper(*args, **kwargs)`，调用 `fn(*args, **kwargs)`，`return wrapper` |
| 保住原函数的名字和文档 | 在 wrapper 上加 `@functools.wraps(fn)` |
| 写一个只加标记不改行为的装饰器 | 给 `fn` 挂属性然后 `return fn`，不要 wrapper |
| 给函数挂东西 | `fn.随便什么名 = 值`（函数是对象，可以挂） |
| 检查函数有没有挂过 | `hasattr(fn, "名")` / `getattr(fn, "名")` |
| 读函数的参数列表 | `inspect.signature(fn).parameters` |
| 读函数的 docstring | `fn.__doc__`（可能是 `None`） |

## 类型注解（会读就行，不用背）

| 写法 | 意思 |
|---|---|
| `list[int]` | 装 int 的列表 |
| `str \| None` | 字符串或者 None |
| `dict[str, Any]` | 键是 str、值随便 |
| `tuple[str, str]` | 恰好两个 str |
| `tuple[type[Exception], ...]` | 一串异常**类**，数量不限 |
| `Callable[[int], str]` | 收一个 int、返回 str 的函数 |
| `Callable[[], Awaitable[T]]` | 不收参数、await 后得到 T 的 async 函数 |
| `type[Foo]` | 类本身，传 `Foo` 不是 `Foo()` |
| `Literal["a", "b"]` | 只能是这两个值之一 |
| `T = TypeVar("T")` | 占位符：传进来什么类型，返回什么类型 |

注解写错程序照样跑，它不影响运行。

## pydantic

| 我想做 | 这样写 |
|---|---|
| 定义一个数据模型 | `class Foo(BaseModel):` 然后写带类型的类属性 |
| 给字段加说明和默认值 | `x: int = Field(default=1, description="给模型看的说明")` |
| 限制数值范围 | `Field(ge=1, le=7)`（>=1 且 <=7） |
| 拿到 JSON Schema | `Foo.model_json_schema()` |
| 用字典构造 | `Foo(**我的字典)` |

## 字符串

| 我想做 | 这样写 |
|---|---|
| 插值 | `f"你好 {name}"` |
| 补空格对齐到 12 列 | `f"{name:12}"` |
| 保留 3 位小数 | `f"{x:.3f}"` |
| 打印出引号和转义（调试用） | `f"{value!r}"` |
| 按分隔符切开 | `"a:b".split(":")` → `["a", "b"]` |
| 去掉首尾空白 | `s.strip()` |
| 按行切开 | `s.splitlines()` |
| 值可能是 None 时先兜底 | `(s or "").strip()` |
