"""练习 1：LangChain 的消息类型。

w02 你用字典表示消息，LangChain 用类。对应关系：

    {"role": "system"}    → SystemMessage
    {"role": "user"}      → HumanMessage
    {"role": "assistant"} → AIMessage      （tool_calls 挂在 .tool_calls 上）
    {"role": "tool"}      → ToolMessage    （必须带 tool_call_id）

换成类的好处：字段名拼错会被编辑器抓到，而字典拼错要等运行时。
你 w02 就踩过一次——`result` 写成了 `content` 该在的位置。

练到的：LangChain 消息类、isinstance 判断、列表推导式过滤。

三段坡道：
  1. describe_messages   我已写完
  2. extract_tool_calls  骨架给你了
  3. from_dicts          独立完成
"""

from __future__ import annotations

from typing import Any

from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage

# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


def describe_messages(messages: list[AnyMessage]) -> list[str]:
    """把消息列表描述成人类可读的字符串列表。

    【已实现，先读懂】重点是 isinstance 判断和属性访问。

    Args:
        messages: 任意消息列表。

    Returns:
        每条消息一行描述。
    """
    lines: list[str] = []
    for m in messages:
        kind = type(m).__name__  # AIMessage / HumanMessage / ...
        # tool_calls 只有 AIMessage 才有，用 getattr 兜底避免 AttributeError
        calls = getattr(m, "tool_calls", None)
        suffix = f" -> 调用 {[c['name'] for c in calls]}" if calls else ""
        lines.append(f"{kind}: {(m.text or '(空)')[:30]}{suffix}")
    return lines


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


def extract_tool_calls(messages: list[AnyMessage]) -> list[dict[str, Any]]:
    """把所有 AIMessage 里的工具调用收集成一个平铺列表。

    调试 agent 时最常问的问题是"它到底调了哪些工具、参数是什么"，这个函数回答它。

    Args:
        messages: 消息列表，通常是 agent 跑完后的 result["messages"]。

    Returns:
        每个工具调用一个字典，含 name 和 args 两个键。没有调用时返回空列表。
    """
    calls: list[dict[str, Any]] = []

    # 第 1 步（已给）：只有 AIMessage 可能带 tool_calls，先筛出来。
    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        # 第 2 步（轮到你）：遍历 message.tool_calls，每个取出 name 和 args
        #   追加进 calls，形如 {"name": ..., "args": ...}。
        #   注意 message.tool_calls 可能是空列表，for 遍历空列表不会出错，不用额外判断。
        #   LangChain 的 tool_call 是字典，键有 name / args / id / type。
        #   注意 args 是**已经解析好的字典**，不像 w02 那样是 JSON 字符串——
        #   这是 LangChain 替你做掉的一件事。
        for call in message.tool_calls:
            calls.append({"name": call["name"], "args": call["args"]})

    return calls


# ─────────────────── 第 3 段：独立完成 ───────────────────


def from_dicts(raw: list[dict[str, Any]]) -> list[AnyMessage]:
    """把 w02 的字典格式消息转成 LangChain 的消息对象。

    这是一个真实场景：你有一批旧格式的对话记录，要喂给新代码。

    Args:
        raw: w02 格式的消息列表，每条有 role/content，
            assistant 可能有 tool_calls，tool 必有 tool_call_id。

    Returns:
        对应的 LangChain 消息对象列表，顺序不变。

    Raises:
        ValueError: 遇到不认识的 role，信息里要带上那个 role 的值。

    思路：
      遍历 raw，按 role 分发到四个类。用 match 语句（w02 warmup 第 7 节）
      或者 if/elif 都行。
        system    -> SystemMessage(content)
        user      -> HumanMessage(content)
        assistant -> AIMessage(content=..., tool_calls=...)
        tool      -> ToolMessage(content=..., tool_call_id=...)
      别忘了 case 兜底抛 ValueError——**误配置要大声失败**，这是 w01 学的。

      w02 的 tool_call 是 {"id","name","arguments"}（arguments 是 JSON 字符串），
      LangChain 要的是 {"name","args","id","type"}（args 是字典）。
      所以要转格式，arguments 用 json.loads 解析。
    """
    raise NotImplementedError


if __name__ == "__main__":
    demo: list[AnyMessage] = [
        SystemMessage("你是助手。"),
        HumanMessage("上海天气？"),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "get_weather", "args": {"city": "上海"}, "id": "c1", "type": "tool_call"}
            ],
        ),
        ToolMessage(content="晴，25 度", tool_call_id="c1"),
        AIMessage("上海今天晴。"),
    ]
    for line in describe_messages(demo):
        print(" ", line)
    print("\n工具调用轨迹:", extract_tool_calls(demo))
