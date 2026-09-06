"""练习 1：异步并发。

agent 的一轮里，模型可能一次返回 5 个 tool_call。串行执行是 5 倍延迟，
并发执行接近 1 倍。这是 agent 开发默认用 async 的最重要理由。

本文件三段坡道，从上往下难度递增：
  1. run_sequential          我已写完 + 逐行注释。**先读懂它**
  2. run_concurrent          骨架给你了，填一个 TODO
  3. run_concurrent_limited  只有签名，照着上面两个的模式自己写

练到的 Python：async/await、协程对象与调用的区别、列表推导式、
asyncio.gather、asyncio.Semaphore、async with。

运行：uv run python weeks/w01-python-foundations/ex1_async_basics.py
"""

from __future__ import annotations

import asyncio


async def slow_double(x: int, delay: float = 0.1) -> int:
    """把 x 翻倍，但先睡 delay 秒，模拟一次网络调用。

    `async def` 定义的叫协程函数。调用它不会立刻执行，
    只会得到一个"协程对象"——必须 await 它，或者交给 gather，才真的跑。
    """
    await asyncio.sleep(delay)
    return x * 2


# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


async def run_sequential(values: list[int]) -> list[int]:
    """依次 await，前一个做完才开始下一个。

    【已实现，先读懂】这是后面两个函数的模板。
    总耗时 ≈ len(values) × delay，因为大家排队。
    """
    results: list[int] = []  # 准备一个空列表装结果

    for x in values:  # 一个一个来
        doubled = await slow_double(x)  # await = 停在这里等它跑完，拿到返回值
        results.append(doubled)  # 装进结果列表

    return results


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


async def run_concurrent(values: list[int]) -> list[int]:
    """用 asyncio.gather 并发跑，返回顺序必须和 values 一致。

    总耗时 ≈ 一个 delay，和 len(values) 几乎无关——因为大家同时在跑。
    """
    # 第 1 步（已给）：把每个 x 变成一个协程对象，装进列表。
    #   注意这里没有 await，所以此刻一个都还没开始跑。
    coroutines = [slow_double(x) for x in values]

    # 第 2 步（轮到你）：用 asyncio.gather 把它们一起跑完并返回结果。
    #   gather 收的是"多个位置参数"，不是一个列表，所以要用 * 把列表展开。
    #   形状大概是：return await asyncio.gather(*某个东西)
    #   gather 保证返回顺序 = 传入顺序，不是谁先跑完谁在前。
    raise NotImplementedError("把这一行删掉，换成第 2 步的实现")


# ─────────────────── 第 3 段：独立完成，照着上面的模式写 ───────────────────


async def run_concurrent_limited(values: list[int], limit: int) -> list[int]:
    """并发跑，但同时最多 limit 个在飞。

    为什么需要：模型厂商有速率限制，无限并发会被 429 拒绝。

    思路（不给代码，自己组装）：
      1. 建一个 asyncio.Semaphore(limit)。它像一个只有 limit 把钥匙的柜子。
      2. 写一个内部的 async 函数，比如叫 run_one(x)，里面：
         用 `async with 信号量:` 包住 `await slow_double(x)`。
         拿不到钥匙的会在这里排队等，拿到的才往下走。
      3. 像第 2 段那样，把所有 run_one(x) 交给 gather。

    验证：test_exercises.py 里的测试会数你同时最多跑了几个。
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
