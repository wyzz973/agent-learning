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

    Args:
        x: 要翻倍的整数。
        delay: 假装网络往返的秒数，默认 0.1。调大它能更明显看出串行和并发的差距。

    Returns:
        x 的两倍。
    """
    await asyncio.sleep(delay)
    return x * 2


# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


async def run_sequential(values: list[int]) -> list[int]:
    """依次 await，前一个做完才开始下一个。

    【已实现，先读懂】这是后面两个函数的模板。
    总耗时 ≈ len(values) × delay，因为大家排队。

    Args:
        values: 待处理的整数列表。

    Returns:
        每个元素翻倍后的列表，顺序与 values 一致。
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

    Args:
        values: 待处理的整数列表。

    Returns:
        每个元素翻倍后的列表。顺序必须与 values 一致，
        而不是谁先跑完谁在前——gather 已经保证了这一点。
    """
    # 第 1 步（已给）：把每个 x 变成一个协程对象，装进列表。
    #   注意这里没有 await，所以此刻一个都还没开始跑。
    coroutines = [slow_double(x) for x in values]

    # 第 2 步（轮到你）：用 asyncio.gather 把它们一起跑完并返回结果。
    #   gather 收的是"多个位置参数"，不是一个列表，所以要用 * 把列表展开。
    #   形状大概是：return await asyncio.gather(*某个东西)
    #   gather 保证返回顺序 = 传入顺序，不是谁先跑完谁在前。
    return await asyncio.gather(*coroutines)


# ─────────────────── 第 3 段：独立完成，照着上面的模式写 ───────────────────


async def run_concurrent_limited(values: list[int], limit: int) -> list[int]:
    """并发跑，但同时最多 limit 个在飞。

    为什么需要：模型厂商有速率限制，无限并发会被 429 拒绝。

    Args:
        values: 待处理的整数列表。
        limit: 同时最多允许几个任务在执行。传 1 就退化成串行，
            传 len(values) 就等于完全并发——写完拿这两个极端值验证一下。

    Returns:
        每个元素翻倍后的列表，顺序与 values 一致。

    思路（不给代码，自己组装）：
      1. 建一个 asyncio.Semaphore(limit)。它像一个只有 limit 把钥匙的柜子。
      2. 写一个内部的 async 函数，比如叫 run_one(x)，里面：
         用 `async with 信号量:` 包住 `await slow_double(x)`。
         拿不到钥匙的会在这里排队等，拿到的才往下走。
      3. 像第 2 段那样，把所有 run_one(x) 交给 gather。

    验证：test_exercises.py 里的测试会数你同时最多跑了几个。
    """
    semaphore = asyncio.Semaphore(limit)

    async def run_one(x: int) -> int:
        async with semaphore:
            return await slow_double(x)

    return await asyncio.gather(*(run_one(x) for x in values))


async def main() -> None:
    """手动跑一遍看耗时差异。测试断言不了"快多少"，得自己看。"""
    # range(80) 是个"惰性"的数字序列，list() 把它摊成真正的列表 [0, 1, ..., 79]。
    values = list(range(80))

    # ─── 关键概念：调用 async 函数 ≠ 执行它 ───
    #
    # 下面这三行 run_sequential(values) 看着像"调用"，但**一个都还没开始跑**。
    # 调用普通函数会立刻执行并返回结果；调用 async 函数只会返回一个"协程对象"。
    # 把它想成一张写好的待办卡片：任务写清楚了，但没人动手。
    #
    # 所以这个列表里装的是三张卡片，配上各自的名字。
    for name, coro in [
        ("串行", run_sequential(values)),
        ("并发", run_concurrent(values)),
        ("并发限流 3", run_concurrent_limited(values, 100)),
    ]:
        # for 后面写两个变量名，是"元组解包"：每轮把 ("串行", 卡片) 这个二元组
        # 拆开，左边给 name，右边给 coro。等价于写 for item in [...] 再 item[0]、item[1]。

        # 事件循环自带一个单调时钟。用它而不是 time.time()，因为它不会被系统改时间影响。
        start = asyncio.get_running_loop().time()

        # ─── 这一行才是真正开跑 ───
        # await 做两件事：把卡片交给事件循环去执行，然后停在这里等结果。
        # 没有 await，卡片永远躺着不动；Python 退出时还会警告 "was never awaited"。
        result = await coro

        elapsed = asyncio.get_running_loop().time() - start

        # f-string 里冒号后面是格式说明：
        #   {name:12}    左对齐补空格到 12 字符宽，让几行输出对齐
        #   {elapsed:.3f} 小数点后保留 3 位
        print(f"{name:12} 耗时 {elapsed:.3f}s  结果 {result}")


if __name__ == "__main__":
    asyncio.run(main())
