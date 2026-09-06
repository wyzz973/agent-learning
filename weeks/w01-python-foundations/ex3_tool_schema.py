"""练习 3：pydantic 与 JSON Schema。

模型看不到你的 Python 函数。它只看到一段 JSON Schema——函数叫什么、
收哪些参数、每个参数什么类型、字段描述写了什么。**模型完全靠这段 JSON
决定要不要调、怎么填参数。** 描述写得含糊，模型就填错参数。

所以 pydantic 不是"顺手用的校验库"，它是你和模型之间的接口定义语言。

练到的 Python：类属性与类型注解、Literal 类型、pydantic Field、
嵌套数据模型、字典操作、dict.get 的默认值。

本文件三段坡道：
  1. build_tool_schema        我已写完，读完跑一遍看输出
  2. WeatherQuery 的字段      给了两个，补第三个
  3. describe_required_fields 独立完成
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Location(BaseModel):
    """一个地点。

    pydantic 模型 = 一个类 + 一堆带类型注解的类属性。
    有默认值的字段可以不传，没默认值的必须传。
    """

    city: str = Field(description="城市名，例如 Shanghai")
    country: str = Field(default="CN", description="ISO 国家代码")


class WeatherQuery(BaseModel):
    """查询天气的参数。

    【第 2 段：补最后一个字段】

    前两个字段给你打样了。照着加第三个：
        days: int，默认 1，允许范围 1 到 7，描述写"要查询未来几天"
    提示：Field(default=1, ge=1, le=7, description="...")
        ge = greater or equal（>=），le = less or equal（<=）

    注意每个字段都有 description——**那是给模型看的 prompt，不是给人看的注释**。
    模型靠它判断这个参数该填什么。
    """

    location: Location = Field(description="要查询的地点")
    unit: Literal["celsius", "fahrenheit"] = Field(default="celsius", description="温度单位")
    # 轮到你：在这里加 days 字段
    days: int = Field(default=1, ge=1, le=7, description="要查询未来几天")


# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


def build_tool_schema(model: type[BaseModel], name: str, description: str) -> dict[str, Any]:
    """把一个 pydantic 模型包装成模型厂商认识的工具定义。

    【已实现】就三行。重点不是代码，是**跑一遍看看输出的 JSON 长什么样**。

    参数 `model: type[BaseModel]` 读作：model 是一个类本身，不是类的实例。
    所以调用时传 WeatherQuery，不是 WeatherQuery()。

    Args:
        model: pydantic 模型类本身（传 WeatherQuery，不是 WeatherQuery()）。
            它的字段定义会被翻译成模型看到的参数列表。
        name: 工具名，模型在 tool_call 里回给你的就是这个字符串。
        description: 工具用途的一句话说明。**模型靠它决定要不要调这个工具**，
            写得含糊模型就不会用，或者在不该用的时候用。

    Returns:
        含 name、description、input_schema 三个键的字典，
        形状与各家模型厂商的工具定义一致。
    """
    return {
        "name": name,
        "description": description,
        # model_json_schema() 是 pydantic 送的：把类定义翻译成 JSON Schema。
        # 嵌套的 Location 会被抽到 $defs 里，用 $ref 引用——跑一遍就看到了。
        "input_schema": model.model_json_schema(),
    }


# ─────────────────── 第 3 段：独立完成，读懂上面的输出再写 ───────────────────


def describe_required_fields(schema: dict[str, Any]) -> list[str]:
    """从 JSON Schema 里取出必填字段名列表。

    先跑 __main__ 看一眼 input_schema 里有什么键，答案就在里面。

    有默认值的字段不会出现在必填列表里。改一下 WeatherQuery 的默认值再跑，
    观察它怎么变——这解释了为什么给工具参数设默认值，会让模型少填一个参数。

    提示：schema 是个普通 dict，用 .get(键名, 默认值) 取值比 [键名] 安全，
    因为全部字段都有默认值时，那个键可能根本不存在。

    Args:
        schema: JSON Schema 字典，即 build_tool_schema 返回值里的 input_schema
            那一层，不是整个返回值。

    Returns:
        必填字段名列表。全部字段都有默认值时返回空列表。
    """
    return schema.get("required", [])


if __name__ == "__main__":
    import json

    schema = build_tool_schema(WeatherQuery, "get_weather", "查询指定地点未来几天的天气")
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    print("\n必填字段:", describe_required_fields(schema["input_schema"]))
