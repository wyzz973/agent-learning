"""练习 2：工具注册表。

上周你写的 @tool 把元数据挂在函数上。这周要把一堆工具管起来：
按名字查、生成给模型看的 schema 列表、按模型的要求执行。

一条核心规则：**工具执行失败，返回错误字符串给模型，不要抛异常。**
抛异常会中断整个 agent 循环；返回错误信息，模型能看到"参数填错了"然后自己重试。
这是 agent 和普通程序最大的行为差异。

练到的 Python：类、字典存函数、json.loads、异常转字符串、字典推导式。

本文件三段坡道：
  1. tool 装饰器 / register  我已写完（tool 是上周的，直接搬过来）
  2. to_schemas              骨架给你了
  3. call                    独立完成
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from typing import Any

# 类型注解到 JSON Schema 类型名的对照。模型认的是右边这些词。
_JSON_TYPES = {int: "integer", float: "number", str: "string", bool: "boolean"}


# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """把函数标记成工具，挂上模型需要的元数据。

    【已实现】和上周 ex4 是同一个东西，参数部分改成了 JSON Schema 格式。

    Args:
        fn: 被装饰的函数。

    Returns:
        原函数本身，多了 __tool__ 属性。
    """
    signature = inspect.signature(fn)

    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, param in signature.parameters.items():
        properties[name] = {"type": _JSON_TYPES.get(param.annotation, "string")}
        # 没有默认值的参数是必填的。inspect.Parameter.empty 是"没有默认值"的标记。
        if param.default is inspect.Parameter.empty:
            required.append(name)

    fn.__tool__ = {  # type: ignore[attr-defined]
        "name": fn.__name__,
        "description": (fn.__doc__ or "").strip().splitlines()[0],
        "parameters": {"type": "object", "properties": properties, "required": required},
    }
    return fn


class ToolRegistry:
    """一组工具。agent 从这里查工具、执行工具。"""

    def __init__(self) -> None:
        """新建一个空注册表。"""
        # 名字 -> 函数。字典可以存函数，因为函数也是对象。
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, fn: Callable[..., Any]) -> None:
        """把一个被 @tool 标记过的函数收进来。

        Args:
            fn: 被 @tool 装饰过的函数。

        Raises:
            ValueError: fn 没有被 @tool 装饰过。
        """
        if not hasattr(fn, "__tool__"):
            # 误配置大声失败：现在报错，好过 agent 跑到一半发现工具不存在。
            raise ValueError(f"{fn.__name__} 没有被 @tool 装饰，无法注册")
        self._tools[fn.__tool__["name"]] = fn

    # ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────

    def to_schemas(self) -> list[dict[str, Any]]:
        """导出所有工具的定义，这份东西会随每次请求发给模型。

        Returns:
            每个工具的 __tool__ 字典组成的列表。没有工具时返回空列表。

        提示：self._tools.values() 拿到所有函数，每个函数身上有 __tool__。
        上周 collect_tools 你写过一模一样的逻辑，这次可以用列表推导式一行写完。
        """
        raise NotImplementedError("一行列表推导式")

    # ─────────────────── 第 3 段：独立完成，本周最重要的一个 ───────────────────

    def call(self, name: str, arguments_json: str) -> str:
        """执行一个工具，把结果转成字符串返回。

        **这个函数永远不抛异常。** 任何失败都变成一段描述错误的字符串返回，
        因为它的返回值会作为 tool 消息喂回给模型，模型要靠它决定下一步。

        Args:
            name: 工具名，来自模型的 tool_call。
            arguments_json: 参数，模型给的是 JSON 字符串不是字典。

        Returns:
            工具的返回值转成的字符串；任何一步失败时，返回描述失败原因的字符串。

        要处理的四种情况（测试会逐条验证）：
          1. 工具不存在      -> 返回错误信息，**并列出有哪些可用工具**
          2. arguments_json 不是合法 JSON -> 返回错误信息，带上原始字符串
          3. 工具执行时抛异常 -> 接住，返回错误信息，带上异常类型和消息
          4. 一切正常        -> 返回结果的字符串形式（用 str(...) 转）

        为什么第 1 条要列出可用工具：模型看到"工具 get_wether 不存在，
        可用的有 get_weather / calculator"，下一轮就能自己改对。
        只说"工具不存在"它只能瞎猜。这是错误信息设计的核心——
        **告诉模型怎么修，不只是告诉它错了**。

        提示：把工具函数取出来之后，用 fn(**参数字典) 调用它。
        ** 解包在上周 warmup 第 7 节见过。
        """
        raise NotImplementedError


# ─────────────────────────── 几个用来练手的工具 ───────────────────────────


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。

    Args:
        city: 城市名，例如"上海"。

    Returns:
        天气描述。
    """
    fake = {"上海": "晴，25 度", "北京": "多云，18 度"}
    if city not in fake:
        raise ValueError(f"不认识的城市: {city}")
    return fake[city]


@tool
def calculator(expression: str) -> str:
    """计算一个简单的算术表达式。

    Args:
        expression: 形如 "2 + 3 * 4" 的表达式。

    Returns:
        计算结果的字符串。
    """
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        raise ValueError(f"表达式里有不允许的字符: {expression}")
    return str(eval(expression))  # noqa: S307 — 上面已经限制了字符集，仅供练习


if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register(get_weather)
    registry.register(calculator)

    print("发给模型的工具定义:")
    print(json.dumps(registry.to_schemas(), indent=2, ensure_ascii=False))

    print("\n四种调用情况:")
    for name, args in [
        ("get_weather", '{"city": "上海"}'),
        ("get_wether", '{"city": "上海"}'),
        ("get_weather", "{坏掉的"),
        ("get_weather", '{"city": "火星"}'),
    ]:
        print(f"  {name}({args}) -> {registry.call(name, args)}")
