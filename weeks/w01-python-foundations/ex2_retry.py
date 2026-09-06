"""练习 2：超时与重试。

LLM API 会超时、会 429 限流、会返回 500。这是常态不是异常。
没有重试的 agent 会在第一次网络抖动时整个挂掉。

关键区分：**超时管单次调用等多久，重试管失败后再试几次**。
两者必须分开——重试 3 次 × 每次超时 60 秒，最坏要等 180 秒。

练到的 Python：自定义异常类、try/except/else、for-else、TypeVar 泛型、
把函数当参数传（高阶函数）、asyncio.timeout 上下文管理器。

本文件三段坡道：
  1. retry_simple   我已写完 + 逐行注释。只重试，不超时不退避
  2. with_retry     在 retry_simple 基础上加超时和退避，骨架给你了
  3. fetch_all      独立完成
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

# TypeVar 是"类型占位符"：fn 返回什么类型，with_retry 就返回什么类型。
# 不写它也能跑，但写了之后编辑器才知道返回值的类型。
T = TypeVar("T")


class RetryExhausted(Exception):
    """重试次数用尽后抛出，携带最后一次的原始异常。

    自定义异常类的最小写法：继承 Exception，在 __init__ 里存下需要的信息。
    存 last_error 是为了让上层能看到"到底是什么错"，而不只是"重试失败了"。

    Args:
        attempts: 总共试了几次。
        last_error: 最后一次失败的原始异常，排查时真正有用的那个。
    """

    def __init__(self, attempts: int, last_error: Exception) -> None:
        super().__init__(f"重试 {attempts} 次后仍失败: {last_error!r}")
        self.attempts = attempts
        self.last_error = last_error


# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


async def retry_simple(fn: Callable[[], Awaitable[T]], attempts: int = 3) -> T:
    """调用 fn，失败就立刻重试，全失败抛 RetryExhausted。

    【已实现，先读懂】这是 with_retry 的骨架，只少了超时和退避。

    参数 fn 的类型 `Callable[[], Awaitable[T]]` 读作：
    一个不收参数、调用后返回一个可 await 之物的函数。也就是一个 async 函数。

    Args:
        fn: 要调用的 async 函数，不接收参数。需要传参时在外面用
            lambda 或 functools.partial 包一层，把参数固定住。
        attempts: 最多尝试几次（含第一次），默认 3。

    Returns:
        fn 成功时的返回值，类型由 fn 决定。

    Raises:
        RetryExhausted: attempts 次全部失败。
    """
    last_error: Exception | None = None  # 记住最后一次的错误，最后要塞进 RetryExhausted

    for attempt in range(attempts):  # attempt 从 0 数到 attempts-1
        try:
            return await fn()  # 成功就直接 return，函数到此结束，不会再循环
        except (TimeoutError, ConnectionError) as error:
            last_error = error  # 失败：记下来，让 for 继续下一轮
            print(f"  第 {attempt + 1} 次失败: {error!r}")

    # 能走到这里，说明 for 跑完了都没 return 过，即每次都失败了。
    assert last_error is not None  # 给类型检查器看的：这里 last_error 一定有值
    raise RetryExhausted(attempts, last_error)


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,  # 这个星号表示：后面的参数必须写成 name=value 的形式调用
    attempts: int = 3,
    timeout: float = 5.0,  # noqa: ASYNC109 — 超时作用于单次尝试，必须在重试循环内部
    backoff: float = 0.1,
    retry_on: tuple[type[Exception], ...] = (TimeoutError, ConnectionError),
) -> T:
    """retry_simple 加上超时、指数退避、可配置的重试异常类型。

    Args:
        fn: 要调用的 async 函数，不接收参数。
        attempts: 最多尝试几次（含第一次），默认 3。
        timeout: **单次**尝试的超时秒数，不是总时长。attempts=3 且
            timeout=5 时最坏要等 15 秒加上退避时间。
        backoff: 退避基数秒数。第 attempt 次失败后睡 backoff * (2 ** attempt) 秒，
            所以 0.1 会得到 0.1、0.2、0.4 这样的间隔。传 0 表示不等待，测试用它加速。
        retry_on: 哪些异常类型值得重试，默认网络超时和连接错误。
            不在这个元组里的异常直接向上抛——参数错误和认证失败重试多少次都不会好。

    Returns:
        fn 成功时的返回值。

    Raises:
        RetryExhausted: attempts 次全部失败，last_error 是最后一次的异常。
        Exception: retry_on 之外的任何异常，原样抛出且不重试。

    在 retry_simple 的基础上改三个地方，测试会逐条验证：

    改动 A — 超时：把 `await fn()` 包进 `async with asyncio.timeout(timeout):`。
        超时会抛 TimeoutError，正好被 except 接住，算一次失败。

    改动 B — 只重试指定类型：把 except 后面写死的 (TimeoutError, ConnectionError)
        换成参数 retry_on。这样 ValueError 之类的会直接向上抛，不浪费重试次数。
        为什么：参数错误、认证失败重试多少次都不会好，只会烧钱。

    改动 C — 指数退避：每次失败后睡一会儿再试，睡的时间逐次翻倍。
        第 attempt 次失败后睡 backoff * (2 ** attempt) 秒。
        但**最后一次失败后不要睡**——反正要抛异常了，睡了纯浪费。
        判断条件形如：if attempt < attempts - 1:
    """
    last_error: Exception | None = None  # 记住最后一次的错误，最后要塞进 RetryExhausted
    for attempt in range(attempts):
        try:
            async with asyncio.timeout(timeout):
                return await fn()
        except retry_on as error:
            print(f"  第 {attempt + 1} 次失败: {error!r}")
            if attempt < attempts - 1:
                await asyncio.sleep(backoff * (2**attempt))
            last_error = error
    assert last_error is not None
    raise RetryExhausted(attempts, last_error)


# ─────────────────── 第 3 段：独立完成，照着上面的模式写 ───────────────────


async def fetch_all(
    urls: list[str],
    *,
    timeout: float = 5.0,  # noqa: ASYNC109 — 同上，转交给 with_retry 作用于单次尝试
) -> list[str | Exception]:
    """并发抓取所有 URL，每个都带重试。

    失败的位置放 Exception 对象而不是抛出——**一个 URL 挂了不该拖垮整批**。
    这正是 agent 处理工具失败的方式：把错误当结果返回，让上层决定怎么办。

    Args:
        urls: 要抓取的地址列表。
        timeout: 单次请求的超时秒数，会原样转交给 with_retry。

    Returns:
        和 urls 等长、顺序一一对应的列表。成功的位置是响应正文字符串，
        失败的位置是异常对象本身——**调用方要用 isinstance 区分这两种情况**。

    思路：
      1. `async with httpx.AsyncClient() as client:` 开一个客户端。
      2. 对每个 url，写一个只抓这一个的 async 函数，用 with_retry 包住它。
      3. 用 ex1 学的 gather 并发跑，但这次加参数 return_exceptions=True
         ——它让失败的那个返回异常对象而不是炸掉整个 gather。

    这个函数没有测试覆盖，跑 __main__ 自己看输出对不对。
    """
    # 第 1 步（已给）：开一个 HTTP 客户端。
    #   async with 和文件的 with open(...) 是一回事：用完自动关掉连接池。
    async with httpx.AsyncClient() as client:
        # 第 2 步（已给）：只抓一个 url 的内部函数。
        #   写在 fetch_all 内部是为了直接用到外面的 client 和 timeout——这叫闭包。
        async def fetch_one(url: str) -> str:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()  # 4xx/5xx 抛异常，否则 500 也会被当成"成功"
            return response.text

        # 第 3 步（轮到你）：把每个 fetch_one(url) 包进 with_retry，凑成一个任务列表。
        #
        #   卡点在这：with_retry 要的是"不收参数的 async 函数"，而 fetch_one 收 url。
        #   所以要先把 url 固定进去，两种写法都行：
        #       functools.partial(fetch_one, url)
        #       lambda u=url: fetch_one(u)
        #
        #   ⚠️ 不能写 lambda: fetch_one(url)。lambda 记住的是**变量 url 本身**，
        #      不是当时的值；循环结束后 url 停在最后一个，所有 lambda 都会去抓同一个地址。
        #      这个坑叫 late binding，写错了不报错但结果全错，是最难查的那种 bug。
        #
        #   另外：httpx 的连接失败抛 httpx.ConnectError，超时抛 httpx.TimeoutException，
        #      都不是内置的 ConnectionError / TimeoutError，所以 with_retry 默认的
        #      retry_on 拦不住它们。要重试就得显式传：
        #      retry_on=(httpx.ConnectError, httpx.TimeoutException)
        tasks = [
            with_retry(
                lambda u=url: fetch_one(u),
                timeout=timeout,
                retry_on=(httpx.ConnectError, httpx.TimeoutException),
            )
            for url in urls
        ]

        # 第 4 步（轮到你）：并发跑完，让失败的位置返回异常对象而不是炸掉整批。
        #   提示：ex1 学的 gather，这次多加一个参数 return_exceptions=True。
        return await asyncio.gather(*tasks, return_exceptions=True)


async def main() -> None:
    urls = ["https://example.com", "https://httpbin.org/status/500", "https://invalid.invalid"]
    results = await fetch_all(urls, timeout=3.0)
    for url, result in zip(urls, results, strict=True):
        status = f"失败 {result!r}" if isinstance(result, Exception) else f"成功 {len(result)} 字节"
        print(f"{url:40} {status}")


if __name__ == "__main__":
    asyncio.run(main())
