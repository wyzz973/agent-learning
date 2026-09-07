"""练习 1：消息历史。

agent 的记忆就是一个列表。每轮对话往里追加，下次调模型时整个列表都发过去。
模型本身**什么都不记得**——它每次收到的是完整历史，看起来"记得"是因为你把历史又发了一遍。

四种角色：
    system     开场白，定规矩，通常只有一条且在最前面
    user       我说的话
    assistant  模型说的话。可能是纯文本，也可能是"我要调这几个工具"
    tool       工具执行结果，必须带上对应的 tool_call_id

练到的 Python：类与 self、TypedDict、列表 append、切片、可变默认参数的坑。

本文件三段坡道：
  1. Conversation.__init__ / add_user  我已写完
  2. add_assistant                     骨架给你了
  3. add_tool_result / to_api_format   独立完成
"""

from __future__ import annotations

from typing import Any, TypedDict


class ToolCall(TypedDict):
    """模型说"我要调这个工具"时给出的东西。"""

    id: str  # 调用编号，工具结果要用它对上号
    name: str  # 工具名
    arguments: str  # 参数，是一段 JSON 字符串，不是字典


class Message(TypedDict, total=False):
    """一条消息。total=False 表示这些键都可以不填。

    role 总是有的；content 在模型只想调工具时可能是 None；
    tool_calls 只在 assistant 消息里出现；tool_call_id 只在 tool 消息里出现。
    """

    role: str
    content: str | None
    tool_calls: list[ToolCall]
    tool_call_id: str


# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


class Conversation:
    """一轮对话的完整消息历史。

    【已实现的部分先读懂】这是本周所有练习的地基。
    """

    def __init__(self, system_prompt: str | None = None) -> None:
        """新建一段对话。

        Args:
            system_prompt: 开场的 system 消息内容。不传就没有 system 消息。
        """
        # 注意这里没有写 messages: list = []，那是上周 warmup 第 6 节的坑。
        self.messages: list[Message] = []

        if system_prompt is not None:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_user(self, content: str) -> None:
        """追加一条用户消息。

        Args:
            content: 用户说的话。
        """
        self.messages.append({"role": "user", "content": content})

    # ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────

    def add_assistant(self, content: str | None, tool_calls: list[ToolCall] | None = None) -> None:
        """追加一条模型消息。

        模型有两种回复：说话（content 有值），或者要调工具（tool_calls 有值）。
        也可能两者都有——模型一边解释一边调工具。

        Args:
            content: 模型说的话。只调工具不说话时是 None。
            tool_calls: 模型要调的工具列表。不调工具时是 None。
        """
        # 第 1 步（已给）：先造出基本的消息。
        message: Message = {"role": "assistant", "content": content}

        # 第 2 步（轮到你）：只有当 tool_calls 有内容时，才把它放进 message。
        #   为什么要判断：没有工具调用时塞一个空列表进去，
        #   有些模型厂商的接口会报错或行为异常。**没有的东西就别放。**
        #   提示：字典加键就是 message["tool_calls"] = ...
        #   注意 None 和空列表 [] 都算"没有"。
        if tool_calls is not None and len(tool_calls) > 0:
            message["tool_calls"] = tool_calls
        self.messages.append(message)

    # ─────────────────── 第 3 段：独立完成，照着上面的模式写 ───────────────────

    def add_tool_result(self, tool_call_id: str, result: str) -> None:
        """追加一条工具执行结果。

        **tool_call_id 必须和模型给的那个 id 对上**，否则模型不知道这是哪个工具的结果。
        模型一次要调三个工具时，你要追加三条 tool 消息，各自带自己的 id。

        Args:
            tool_call_id: 对应的 ToolCall 的 id。
            result: 工具返回的内容，必须是字符串。工具返回字典时要先转成 JSON。

        思路：和 add_user 一样简单，只是 role 换成 "tool"，
        并且多带一个 tool_call_id 键。
        """
        message: Message = {"role": "tool", "tool_call_id": tool_call_id, "content": result}
        self.messages.append(message)

    def to_api_format(self) -> list[dict[str, Any]]:
        """导出成能直接发给模型接口的格式。

        Returns:
            消息列表的一个**副本**。调用方拿去改不会影响这里的历史。

        思路：为什么要副本？因为返回 self.messages 的话，
        调用方 append 一下就污染了你的历史（warmup 第 5 节那个坑）。
        列表复制用 .copy() 或 list(...)。
        """
        return self.messages.copy()

    def last_assistant_content(self) -> str | None:
        """取最后一条 assistant 消息的文本内容。

        agent 循环结束后，用它拿到最终答案。

        Returns:
            最后一条 assistant 消息的 content；没有 assistant 消息时返回 None。

        思路：倒着遍历 self.messages，找到第一条 role 是 assistant 的就返回它的 content。
        倒着遍历用 reversed(列表)。
        """
        for message in reversed(self.messages):
            if message["role"] == "assistant":
                return message["content"]
        return None


if __name__ == "__main__":
    conv = Conversation("你是一个有用的助手。")
    conv.add_user("上海天气怎么样？")
    conv.add_assistant(
        None, [{"id": "call_1", "name": "get_weather", "arguments": '{"city": "上海"}'}]
    )
    conv.add_tool_result("call_1", "晴，25 度")
    conv.add_assistant("上海今天晴，25 度。")

    for i, m in enumerate(conv.messages):
        print(f"{i}. [{m['role']:9}] {m.get('content') or '(只调工具，没说话)'}")
    print(f"\n最终答案: {conv.last_assistant_content()}")
