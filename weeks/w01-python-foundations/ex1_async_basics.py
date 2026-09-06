"""练习 1：异步并发。

agent 的一轮里，模型可能一次返回 5 个 tool_call。串行执行是 5 倍延迟，
并发执行接近 1 倍。这是 agent 开发默认用 async 的唯一理由，也是最重要的理由。

跑 `uv run python weeks/w01-python-foundations/ex1_async_basics.py` 看耗时差异。
"""

from __future__ import annotations

import asyncio


async def slow_double(x: int, delay: float = 0.1) -> int:
    """把 x 翻倍，但先睡 delay 秒，模拟一次网络调用。

    这是唯一送给你的实现，照着它理解 async 函数的形状。
    """
    await asyncio.sleep(delay)
    return x * 2


async def run_sequential(values: list[int]) -> list[int]:
    """依次 await，前一个做完才开始下一个。

    实现它，然后在 __main__ 里观察：总耗时 ≈ len(values) * delay。
    """
    raise NotImplementedError


async def run_concurrent(values: list[int]) -> list[int]:
    """用 asyncio.gather 并发跑，返回顺序必须和 values 一致。

    实现它，然后观察：总耗时 ≈ 一个 delay，与 len(values) 几乎无关。
    gather 保证返回顺序等于入参顺序——这一点后面拼装工具结果时会依赖。
    """
    raise NotImplementedError


async def run_concurrent_limited(values: list[int], limit: int) -> list[int]:
    """并发跑，但同时最多 limit 个在飞。

    真实场景里模型厂商有速率限制，无限并发会直接被 429。
    提示：asyncio.Semaphore。返回顺序同样要和 values 一致。
    """
    raise NotImplementedError


async def main() -> None:
    values = list(range(8))

    for name, coro in [
        ("串行", run_sequential(values)),
        ("并发", run_concurrent(values)),
        ("并发限流 3", run_concurrent_limited(values, 3)),
    ]:
        start = asyncio.get_running_loop().time()
        result = await coro
        elapsed = asyncio.get_running_loop().time() - start
        print(f"{name:12} 耗时 {elapsed:.3f}s  结果 {result}")


if __name__ == "__main__":
    asyncio.run(main())
