"""练习 2：LangChain 的 @tool。

和你 w02 手写的那个几乎一样，但有三点不同：

  1. 被装饰后变成 BaseTool 对象，不再是普通函数——要用 .invoke() 调用
  2. description 取整个 docstring（含 Args/Returns），不只第一行
  3. 参数 schema 由 pydantic 自动生成，类型、默认值、约束全都带上

第 3 点是你 w02 手写时最费劲的部分（还记得 _JSON_TYPES 那个映射表吗），
LangChain 直接复用了 pydantic，所以 w01 ex3 学的东西在这里全能用上。

练到的：@tool 装饰器、BaseTool 的属性、.invoke()、pydantic 约束。

三段坡道：
  1. tool 定义与 describe_tool  我已写完
  2. calculator 的错误处理       骨架给你了
  3. build_tool_index            独立完成
"""

from __future__ import annotations

from typing import Any, re

from langchain.tools import BaseTool, tool
from pydantic import Field

# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。

    Args:
        city: 城市名，例如"上海"或"北京"。只支持这两个。

    Returns:
        天气描述字符串。
    """
    fake = {"上海": "晴，25 度", "北京": "多云，18 度"}
    if city not in fake:
        # 注意：create_agent 默认**不会**接住这个异常，它会直接抛出中断整个 agent。
        # 这和你 w02 手写的 ToolRegistry.call 不同——你当时主动接住了所有异常。
        # 想恢复那个行为要显式加 ToolErrorMiddleware，见 ex3 第 3 段。
        raise ValueError(f"不支持的城市 {city!r}，只能查：上海、北京")
    return fake[city]


def describe_tool(t: BaseTool) -> dict[str, Any]:
    """把一个工具的元数据摘出来。

    【已实现】跑 __main__ 看输出，对比你 w02 手写的 __tool__ 字典。

    Args:
        t: 被 @tool 装饰过的工具。

    Returns:
        含 name、description、args 三个键的字典。
    """
    return {"name": t.name, "description": t.description, "args": t.args}


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


@tool
def calculator(expression: str, precision: int = 2) -> str:
    """计算一个算术表达式并按指定精度返回。

    Args:
        expression: 形如 "23 * 17" 的表达式，只允许数字和 + - * / ( ) . 空格。
        precision: 结果保留几位小数，范围 0 到 6，默认 2。

    Returns:
        计算结果的字符串。

    Raises:
        ValueError: 表达式含非法字符，或计算过程本身出错。
    """
    # 第 1 步（已给）：白名单校验，防止 eval 执行任意代码。
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        raise ValueError(f"表达式含不允许的字符: {expression!r}")

    # 第 2 步（轮到你）：算出结果并按 precision 位小数返回。
    #   - 用 eval(expression) 求值（上面已经限制了字符集，仅供练习）
    #   - 除以零之类的错误要接住，转成 ValueError 抛出，**信息里带上原表达式**
    #     （这条是 w01 学的：错误信息要能指向解决办法）
    #   - 返回值要是字符串，用 f"{数值:.{precision}f}" 格式化
    #     那个嵌套的大括号是把 precision 的值插进格式说明里

    try:
        value = eval(expression)
    except Exception as error:
        raise ValueError(f"表达式计算错误: {expression!r}") from error

    return f"{value:.{precision}f}"


# ─────────────────── 第 3 段：独立完成 ───────────────────


def build_tool_index(tools: list[BaseTool]) -> dict[str, BaseTool]:
    """按名字建立工具索引，并拒绝重名。

    这是你 w02 的 ToolRegistry 的核心，LangChain 没有提供现成的——
    create_agent 直接吃一个列表。但真实项目里工具来自多个模块，重名很常见，
    而重名的后果是**静默覆盖**：模型调 A 实际执行了 B，极难排查。

    Args:
        tools: 工具列表。

    Returns:
        名字到工具的字典。

    Raises:
        ValueError: 出现重名工具，信息里要带上那个重复的名字。

    思路：遍历 tools，用 t.name 做键。放进字典前先检查这个名字在不在，
    在就抛 ValueError。四行左右。
    """
    index = {}
    for t in tools:
        if t.name in index:
            raise ValueError(f"出现重名工具: {t.name!r}")
        index[t.name] = t
    return index


@tool
def search_notes(query: str, limit: int = Field(default=5, ge=1, le=20)) -> list[str]:
    """在我的笔记里按关键词搜索。

    Args:
        query: 搜索关键词。
        limit: 最多返回几条，1 到 20 之间，默认 5。

    Returns:
        匹配到的笔记标题列表。
    """
    return [f"{query} 相关笔记 {i}" for i in range(limit)]


if __name__ == "__main__":
    import json

    for t in [get_weather, calculator, search_notes]:
        print(json.dumps(describe_tool(t), indent=2, ensure_ascii=False))
        print()

    print("直接调用要用 .invoke():", get_weather.invoke({"city": "上海"}))
