"""练习 4：装饰器。

第 3 周你会写 `@tool`，然后一个普通函数就变成了 agent 能调的工具。
在那之前先自己写一个，这样 `@tool` 对你就不是魔法，是十几行代码。

装饰器的全部秘密：它接收一个函数，做点手脚，再把函数还回去。
`@foo` 写在 `def bar` 上面，等价于 `bar = foo(bar)`。就这样。

练到的 Python：函数是一等对象、装饰器、functools.wraps、
给函数对象挂属性、inspect 模块、字典推导式、getattr。

本文件三段坡道：
  1. log_calls     我已写完 + 逐行注释。最小的装饰器长什么样
  2. tool          骨架给你了，填两个 TODO
  3. collect_tools 独立完成
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


def log_calls(fn: Callable[..., Any]) -> Callable[..., Any]:
    """【已实现，先读懂】一个最小的装饰器：调用前后打印一行。

    读三遍这个函数，装饰器就通了。
    """

    # wrapper 是"替身"：以后别人调 add，实际调到的是这个 wrapper。
    # @functools.wraps(fn) 把原函数的名字和 docstring 复制给替身，
    # 否则调试时看到的全是 "wrapper"，非常难查。
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"  调用 {fn.__name__}，参数 {args} {kwargs}")
        result = fn(*args, **kwargs)  # 真正调用原函数
        print(f"  {fn.__name__} 返回 {result}")
        return result  # 别忘了把结果还回去

    return wrapper  # 装饰器返回替身，替身取代了原函数的位置


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """把普通函数标记成工具，并附加模型需要的元数据。

    和 log_calls 不同：这次**不需要替身**。我们不改变函数的行为，
    只是给函数对象挂一个 __tool__ 属性，然后原样还回去。
    Python 里函数也是对象，可以随便挂属性——这就是全部机关。
    """
    # 第 1 步（已给）：从函数签名里读出参数名和类型名。
    #   inspect.signature(fn).parameters 是个有序字典：参数名 -> 参数对象。
    #   p.annotation 是那个参数的类型注解，__name__ 取它的名字（如 "int"）。
    signature = inspect.signature(fn)
    parameters = {
        name: p.annotation.__name__ if hasattr(p.annotation, "__name__") else str(p.annotation)
        for name, p in signature.parameters.items()
    }

    # 第 2 步（轮到你）：取 docstring 的第一行作为 description。
    #   fn.__doc__ 是整个 docstring，可能是多行，也可能是 None。
    #   要点：按换行切开取第一段，去掉首尾空白，None 时给空字符串。
    #   提示：(fn.__doc__ or "").strip().splitlines() 想想这串东西返回什么
    description = ""  # TODO 换成真正的取值

    # 第 3 步（轮到你）：把元数据挂到函数上，键是 name / description / parameters。
    #   写法就是普通赋值：fn.__tool__ = {...}
    #   name 取 fn.__name__。
    #   （类型检查器会抱怨给函数挂属性，本周不用管，weeks/ 不跑 mypy）
    # TODO 在这里挂 __tool__

    return fn  # 原样还回去，函数行为完全不变


# ─────────────────── 第 3 段：独立完成，照着上面的模式写 ───────────────────


def collect_tools(namespace: dict[str, Any]) -> list[dict[str, Any]]:
    """从一个命名空间里挑出所有被 @tool 标记过的函数，返回它们的元数据列表。

    这就是框架"自动发现工具"的原理——没有魔法，就是遍历加属性检查。

    思路：
      namespace 是个普通字典（比如 vars(某模块)），键是名字，值是各种对象。
      遍历它的值，挑出那些身上有 __tool__ 属性的，把 __tool__ 收集起来。
      提示：hasattr(obj, "__tool__") 判断有没有；getattr(obj, "__tool__") 取值。
    """
    raise NotImplementedError


@tool
def add(a: int, b: int) -> int:
    """把两个整数相加。

    第二行开始的内容不进 description，只取第一行。
    """
    return a + b


@tool
def search(query: str, limit: int = 5) -> list[str]:
    """按关键词搜索，返回最多 limit 条结果。"""
    return [f"{query}-{i}" for i in range(limit)]


@log_calls
def demo_logged(x: int) -> int:
    """用来演示第 1 段那个装饰器的效果。"""
    return x + 1


if __name__ == "__main__":
    import json

    print("log_calls 装饰器的效果：")
    demo_logged(41)

    print("\n直接调用被 @tool 装饰的函数，行为不变:", add(2, 3))
    print("挂上的元数据:")
    print(json.dumps(collect_tools(globals()), indent=2, ensure_ascii=False))
    print("\n签名保住了吗:", inspect.signature(add), add.__name__)
