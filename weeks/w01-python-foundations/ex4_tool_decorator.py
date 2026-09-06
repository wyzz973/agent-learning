"""练习 4：装饰器。

第 3 周你会写 `@tool` 然后一个函数就变成了 agent 能调的工具。
在那之前先自己写一个，这样 `@tool` 对你就不是魔法，是十几行代码。

装饰器的全部秘密：它在不改函数体的前提下，给函数对象挂上额外的东西
（元数据、包装逻辑），然后把它交还回去。
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """把普通函数标记成工具，并附加模型需要的元数据。

    要求（test_exercises.py 会验证）：
    - 原函数照常可以直接调用，行为完全不变
    - 函数上多出 `__tool__` 属性，是个 dict，含 name / description / parameters
    - name 取函数名
    - description 取 docstring 的第一行——**所以工具的 docstring 是功能代码**
    - parameters 从类型注解生成：{参数名: 类型名}，跳过 return
    - 用 functools.wraps 保住 __name__ 和 __doc__，否则调试时看到的全是 wrapper

    提示：inspect.signature(fn) 拿参数，fn.__annotations__ 拿注解。
    """
    # 占位实现：原样返回，好让本模块能被导入。替换掉整个函数体。
    return fn


def collect_tools(namespace: dict[str, Any]) -> list[dict[str, Any]]:
    """从一个命名空间里挑出所有被 @tool 标记过的函数，返回它们的元数据列表。

    这就是框架"自动发现工具"的原理——没有魔法，就是遍历加属性检查。
    用 globals() 调它试试。
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


if __name__ == "__main__":
    import json

    print("直接调用不受影响:", add(2, 3))
    print("挂上的元数据:")
    print(json.dumps(collect_tools(globals()), indent=2, ensure_ascii=False))
    print("\n签名保住了吗:", inspect.signature(add), add.__name__)
