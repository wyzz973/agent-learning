"""语法热身：本周练习会用到的新写法，每个一个最小例子。

**做练习之前先跑这个文件**，从头看到尾，看每行代码打印出什么。
不用改、不用写，只要跑和读。大约 15 分钟。

    uv run python weeks/w01-python-foundations/00_warmup.py

卡在某个语法上时回来查对应的小节。速查版见 ../../SYNTAX_CARDS.md。
"""

from __future__ import annotations

import asyncio
import functools


def section(title: str) -> None:
    """打印分节标题，只为让输出好读。

    Args:
        title: 小节名。
    """
    print(f"\n{'=' * 8} {title} {'=' * 8}")


# ═══════════════ 1. async 函数：调用 ≠ 执行 ═══════════════


async def say(word: str) -> str:
    """一个最简单的 async 函数。

    Args:
        word: 要返回的词。

    Returns:
        原样返回 word。
    """
    await asyncio.sleep(0.01)  # 假装在等网络
    return word


async def demo_call_vs_await() -> None:
    """调用 async 函数得到的是"待办卡片"，await 才真的执行。"""
    section("1. 调用 ≠ 执行")

    card = say("hello")  # 没有 await：什么都没发生
    print(f"直接调用得到的是: {type(card).__name__}")  # coroutine

    result = await card  # 现在才执行
    print(f"await 之后拿到: {result!r}")


# ═══════════════ 2. gather：一起跑 ═══════════════


async def demo_gather() -> None:
    """gather 把多个协程一起跑完，返回顺序 = 传入顺序。"""
    section("2. gather 并发")

    results = await asyncio.gather(say("a"), say("b"), say("c"))
    print(f"三个一起跑，结果: {results}")

    # 有一堆协程在列表里时，用 * 展开成多个参数
    cards = [say(w) for w in ["x", "y", "z"]]  # 列表推导式：造一个列表
    print(f"列表里装着 {len(cards)} 张卡片，都还没跑")
    print(f"gather(*列表) 的结果: {await asyncio.gather(*cards)}")


# ═══════════════ 3. Semaphore：限制同时几个 ═══════════════


async def demo_semaphore() -> None:
    """信号量像一个只有 N 把钥匙的柜子，拿不到钥匙的排队等。"""
    section("3. Semaphore 限流")

    lock = asyncio.Semaphore(2)  # 只有 2 把钥匙
    running = 0

    async def worker(n: int) -> None:
        nonlocal running  # 声明：我要改外面那个 running，不是新建一个
        async with lock:  # 拿钥匙，用完自动还
            running += 1
            print(f"  worker {n} 开始，此刻同时在跑 {running} 个")
            await asyncio.sleep(0.05)
            running -= 1

    await asyncio.gather(*[worker(i) for i in range(5)])
    print("同时在跑的数字从没超过 2")


# ═══════════════ 4. try / except / as ═══════════════


class MyError(Exception):
    """自定义异常：继承 Exception 就行，可以存额外信息。"""

    def __init__(self, code: int) -> None:
        super().__init__(f"出错了，代码 {code}")
        self.code = code  # 存起来，让接住的人能读到


def demo_exceptions() -> None:
    """异常的抛出、捕获、读取。"""
    section("4. 异常")

    try:
        raise MyError(404)
    except MyError as error:  # as error：把异常对象绑给变量 error
        print(f"接住了: {error}")
        print(f"读它身上存的东西: error.code = {error.code}")

    # 只捕获指定类型，其他的会漏过去
    try:
        try:
            raise ValueError("我不是 MyError")
        except MyError:  # 类型对不上，捕获不到
            print("这行不会执行")
    except ValueError as error:
        print(f"漏到外层被接住: {error!r}")

    # 一个元组可以列多个类型
    for bad in [MyError(500), ValueError("v")]:
        try:
            raise bad
        except (MyError, ValueError) as error:
            print(f"元组匹配多种类型，接住: {type(error).__name__}")


# ═══════════════ 5. 函数走到末尾会返回 None ═══════════════


def forgot_return(x: int) -> int | None:
    """循环里没 return 成功，走到末尾就返回 None——最常见的隐蔽 bug。

    Args:
        x: 随便一个数。

    Returns:
        x 大于 100 时返回它，否则什么都不返回（即 None）。
    """
    if x > 100:
        return x
    # 这里什么都没写


def demo_implicit_none() -> None:
    """看看忘记 return 会发生什么。"""
    section("5. 忘记 return")

    print(f"forgot_return(200) = {forgot_return(200)}")
    print(f"forgot_return(1)   = {forgot_return(1)}   ← 没报错，但是 None")
    print("None 会一路传下去，直到某个地方用它做运算才炸——所以报错点通常不是出错点")


# ═══════════════ 6. 装饰器 ═══════════════


def shout(fn: functools.Callable[..., str]) -> functools.Callable[..., str]:
    """一个最小的装饰器：把返回值变成大写。

    Args:
        fn: 被装饰的函数。

    Returns:
        替身函数。调用它 = 调用原函数再加工。
    """

    @functools.wraps(fn)  # 把原函数的名字和文档复制给替身
    def wrapper(*args: object, **kwargs: object) -> str:
        return fn(*args, **kwargs).upper()

    return wrapper


@shout  # 等价于 greet = shout(greet)
def greet(name: str) -> str:
    """打招呼。

    Args:
        name: 名字。

    Returns:
        问候语。
    """
    return f"hello {name}"


def demo_decorator() -> None:
    """装饰器就是"拿走一个函数，还回来一个函数"。"""
    section("6. 装饰器")

    print(f"greet('bob') = {greet('bob')}   ← 被装饰器改成大写了")
    print(f"名字还是原来的: {greet.__name__}  ← 因为用了 functools.wraps")

    # 函数是对象，可以随便挂属性——这是 @tool 的全部机关
    def plain() -> None:
        pass

    plain.my_label = "我是挂上去的"  # type: ignore[attr-defined]
    print(f"给函数挂属性: plain.my_label = {plain.my_label}")  # type: ignore[attr-defined]


# ═══════════════ 7. 推导式与解包 ═══════════════


def demo_comprehension_and_unpacking() -> None:
    """列表推导式、字典推导式、* 和 ** 的展开。"""
    section("7. 推导式与解包")

    squares = [x * x for x in range(5)]  # 列表推导式
    print(f"[x * x for x in range(5)] = {squares}")

    evens = [x for x in range(10) if x % 2 == 0]  # 带条件
    print(f"带 if 过滤 = {evens}")

    lengths = {word: len(word) for word in ["a", "bb", "ccc"]}  # 字典推导式
    print(f"字典推导式 = {lengths}")

    def add3(a: int, b: int, c: int) -> int:
        return a + b + c

    nums = [1, 2, 3]
    print(f"* 展开列表当位置参数: add3(*{nums}) = {add3(*nums)}")

    kwargs = {"a": 10, "b": 20, "c": 30}
    print(f"** 展开字典当关键字参数: add3(**{kwargs}) = {add3(**kwargs)}")


# ═══════════════ 8. lambda 的坑 ═══════════════


def demo_lambda_late_binding() -> None:
    """lambda 记住的是变量，不是当时的值。这个坑不报错，但结果全错。"""
    section("8. lambda 的 late binding 坑")

    wrong = [lambda: i for i in range(3)]  # noqa: B023
    print(f"错的写法，三个都返回最后一个 i: {[f() for f in wrong]}")

    right = [lambda i=i: i for i in range(3)]  # i=i 把当时的值钉住
    print(f"对的写法 lambda i=i: {[f() for f in right]}")


# ═══════════════ 9. 只能用名字传的参数 ═══════════════


def configure(host: str, *, port: int = 80, debug: bool = False) -> str:
    """星号后面的参数必须写成 name=value 的形式。

    Args:
        host: 位置参数，可以直接传。
        port: 星号之后，必须写 port=8080。
        debug: 同上。

    Returns:
        拼好的描述字符串。
    """
    return f"{host}:{port} debug={debug}"


def demo_keyword_only() -> None:
    """为什么函数签名里会有一个孤零零的 *。"""
    section("9. 强制关键字参数")

    print(configure("localhost", port=8080, debug=True))
    print("configure('localhost', 8080) 会直接报错——星号后面的必须写名字")
    print("好处：调用处一眼看懂每个值是什么，不用回去查签名")


# ═══════════════ 10. 类型注解怎么读 ═══════════════


def demo_type_hints() -> None:
    """类型注解只是给人和编辑器看的，运行时不检查。"""
    section("10. 类型注解怎么读")

    print("list[int]                 一个装 int 的列表")
    print("str | None                字符串，或者 None")
    print("dict[str, Any]            键是 str、值随便的字典")
    print("tuple[str, str]           恰好两个 str 的元组")
    print("Callable[[], Awaitable[T]]  一个不收参数、await 后得到 T 的函数")
    print("type[BaseModel]           类本身，不是实例（传 Foo，不是 Foo()）")
    print("Literal['a', 'b']         只能是 'a' 或 'b' 这两个值之一")
    print("\n注解写错了程序照样跑——它不影响运行，只帮你和编辑器发现问题")


async def main() -> None:
    """按顺序跑完所有小节。"""
    await demo_call_vs_await()
    await demo_gather()
    await demo_semaphore()
    demo_exceptions()
    demo_implicit_none()
    demo_decorator()
    demo_comprehension_and_unpacking()
    demo_lambda_late_binding()
    demo_keyword_only()
    demo_type_hints()
    print("\n跑完了。回去做练习，卡住就回来查对应小节。")


if __name__ == "__main__":
    asyncio.run(main())
