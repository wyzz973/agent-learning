"""练习 2：超时与重试。

LLM API 会超时、会 429 限流、会返回 500。这是常态不是异常。
没有重试的 agent 会在第一次网络抖动时整个挂掉。

关键区分：**超时管单次调用等多久，重试管失败后再试几次**。
两者必须分开设置——重试 3 次 × 每次超时 60 秒，最坏要等 180 秒。
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class RetryExhausted(Exception):
    """重试次数用尽后抛出，携带最后一次的原始异常。"""

    def __init__(self, attempts: int, last_error: Exception) -> None:
        super().__init__(f"重试 {attempts} 次后仍失败: {last_error!r}")
        self.attempts = attempts
        self.last_error = last_error


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    timeout: float = 5.0,  # noqa: ASYNC109 — 超时作用于单次尝试，必须在重试循环内部
    backoff: float = 0.1,
    retry_on: tuple[type[Exception], ...] = (TimeoutError, ConnectionError),
) -> T:
    """调用 fn，失败就重试，全部失败抛 RetryExhausted。

    要求（test_exercises.py 会逐条验证）：
    - 每次调用用 asyncio.timeout 限制在 timeout 秒内，超时算一次失败
    - 只重试 retry_on 里的异常类型；其他异常直接向上抛，不重试
    - 指数退避：第 n 次失败后睡 backoff * (2 ** n) 秒，最后一次失败后不睡
    - 成功就立刻返回，不再重试
    - attempts 次全失败，抛 RetryExhausted，last_error 是最后一次的异常

    为什么 retry_on 要限定类型：参数错误、认证失败重试多少次都不会好，
    只会浪费时间和钱。只重试那些"再试一次可能就好了"的错误。
    """
    raise NotImplementedError


async def fetch_all(
    urls: list[str],
    *,
    timeout: float = 5.0,  # noqa: ASYNC109 — 同上，转交给 with_retry 作用于单次尝试
) -> list[str | Exception]:
    """并发抓取所有 URL，每个都带重试。

    失败的位置放 Exception 对象而不是抛出——**一个 URL 挂了不该拖垮整批**。
    这正是 agent 处理工具失败的方式：把错误作为结果返回，让上层决定怎么办。

    提示：httpx.AsyncClient + asyncio.gather(..., return_exceptions=True)。
    """
    raise NotImplementedError


async def main() -> None:
    urls = ["https://example.com", "https://httpbin.org/status/500", "https://invalid.invalid"]
    results = await fetch_all(urls, timeout=3.0)
    for url, result in zip(urls, results, strict=True):
        status = f"失败 {result!r}" if isinstance(result, Exception) else f"成功 {len(result)} 字节"
        print(f"{url:40} {status}")


if __name__ == "__main__":
    asyncio.run(main())
