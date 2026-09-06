"""练习 3：pydantic 与 JSON Schema。

模型看不到你的 Python 函数。它只看到一段 JSON Schema——函数叫什么、
收哪些参数、每个参数什么类型、字段描述写了什么。**模型完全靠这段 JSON 决定
要不要调、怎么填参数。** 描述写得含糊，模型就填错参数。

所以 pydantic 不是"顺手用的校验库"，它是你和模型之间的接口定义语言。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class Location(BaseModel):
    """一个地点。嵌套模型会在 JSON Schema 里变成 $defs 引用，自己跑出来看看。"""

    city: str
    country: str = "CN"


class WeatherQuery(BaseModel):
    """查询天气的参数。

    要求：
    - location: Location 类型，必填，描述写"要查询的地点"
    - unit: 只能是 "celsius" 或 "fahrenheit"，默认 "celsius"（提示：Literal）
    - days: int，默认 1，范围 1..7（提示：pydantic 的 Field 有 ge/le）

    每个字段都要有 description——**那是给模型看的 prompt，不是给人看的注释**。
    """

    # 由你补全字段定义
    location: Location
    unit: Literal["celsius", "fahrenheit"] = "celsius"
    days: int = 1


def build_tool_schema(model: type[BaseModel], name: str, description: str) -> dict[str, Any]:
    """把一个 pydantic 模型包装成模型厂商认识的工具定义。

    目标结构（OpenAI/Anthropic 的 tool 定义大同小异）：

        {
            "name": name,
            "description": description,
            "input_schema": <model 生成的 JSON Schema>,
        }

    提示：model.model_json_schema()。
    实现完跑一下 __main__，把打印出来的 JSON 从头读到尾——
    **这就是模型眼里你的工具的全部样子。**
    """
    raise NotImplementedError


def describe_required_fields(schema: dict[str, Any]) -> list[str]:
    """从 JSON Schema 里取出必填字段名列表。

    有默认值的字段不在 required 里。改一下 WeatherQuery 的默认值再跑，
    观察 required 怎么变——这解释了为什么给工具参数设默认值会让模型少填一个参数。
    """
    raise NotImplementedError


if __name__ == "__main__":
    import json

    schema = build_tool_schema(WeatherQuery, "get_weather", "查询指定地点未来几天的天气")
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    print("\n必填字段:", describe_required_fields(schema["input_schema"]))
