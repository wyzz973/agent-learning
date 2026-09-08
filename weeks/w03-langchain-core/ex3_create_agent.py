"""练习 3：create_agent —— 一行换掉你 w02 的整个循环。

这是本周的核心。你 w02 写的：

    conversation.add_user(...)          维护历史
    for _ in range(max_iterations):     循环
        response = await llm.complete(...)   问模型
        if not response["tool_calls"]:  没工具就返回
            return ...
        for call in response["tool_calls"]:  执行工具
            result = registry.call(...)
            conversation.add_tool_result(...)

这些 create_agent 全包了。你要学的不是"怎么用"（一行而已），
而是**它到底替你做了什么、什么时候该自己写**。

关于测试：create_agent 需要模型支持 bind_tools，langchain 自带的
FakeMessagesListChatModel 会抛 NotImplementedError。所以我们继承
GenericFakeChatModel 补一个 bind_tools —— 和你 w02 造 FakeLLM 一个道理，
只是从"实现 Protocol"变成了"继承并覆盖一个方法"。

练到的：继承与方法覆盖、create_agent、invoke 的输入输出结构。

三段坡道：
  1. ScriptedChatModel / build_agent  我已写完
  2. run_agent                        骨架给你了
  3. trace_of                         独立完成
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ex2_tools import get_weather
from langchain.agents import create_agent
from langchain.messages import AIMessage, AnyMessage, HumanMessage
from langchain.tools import BaseTool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


class ScriptedChatModel(GenericFakeChatModel):
    """按剧本返回的假模型，用于离线测试。

    继承 GenericFakeChatModel 拿到"按顺序吐消息"的能力，
    只补一个 bind_tools —— create_agent 会调它来绑工具，假模型不需要真绑。
    """

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptedChatModel:
        """接受工具绑定但忽略它。

        Args:
            tools: 要绑定的工具，假模型用不上。
            **kwargs: 其他绑定参数，同样忽略。

        Returns:
            模型自己，好让 create_agent 继续往下走。
        """
        return self


def scripted(*responses: AIMessage) -> ScriptedChatModel:
    """用一串预设回复造一个假模型。

    【已实现】GenericFakeChatModel 要一个迭代器，这里帮你包好。

    Args:
        *responses: 模型第 1 次、第 2 次……调用时分别返回什么。

    Returns:
        照这个剧本演的假模型。
    """
    return ScriptedChatModel(messages=iter(responses))


def build_agent(tools: list[BaseTool], model: Any, system_prompt: str | None = None) -> Any:
    """组装一个 agent。

    【已实现，先读懂】对比你 w02 的 Agent.__init__ ——
    那里你要自己存 llm、registry、max_iterations，这里一个函数调用搞定。

    Args:
        tools: 可用工具列表。注意这里直接吃列表，没有 ToolRegistry 那一层。
        model: 聊天模型，真的假的都行。
        system_prompt: 开场的系统提示，不传就没有。

    Returns:
        编译好的 agent，用 .invoke() 跑。
    """
    return create_agent(model=model, tools=tools, system_prompt=system_prompt)


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


def run_agent(agent: Any, question: str) -> str:
    """跑一轮对话，返回最终的文本答案。

    Args:
        agent: build_agent 造出来的 agent。
        question: 用户的问题。

    Returns:
        最后一条 AIMessage 的文本内容。
    """
    # 第 1 步（已给）：invoke 的输入是一个字典，键是 "messages"，值是消息列表。
    #   这和你 w02 的 conversation.add_user(...) 是同一件事，只是换了形式。
    result = agent.invoke({"messages": [HumanMessage(question)]})

    # 第 2 步（轮到你）：从 result 里取出最终答案。
    #   result 是个字典，result["messages"] 是完整的消息列表
    #   （包含你传进去的那条 + agent 跑出来的所有）。
    #   最终答案是**最后一条消息**的文本，用 .text 属性取。
    #   提示：列表取最后一个元素用 [-1]。
    #   这和你 w02 写的 last_assistant_content 是同一个动作，但简单得多——
    #   因为 create_agent 保证最后一条一定是模型的最终回复。
    raise NotImplementedError("把这一行换成第 2 步的取值")


# ─────────────────── 第 3 段：独立完成（两个函数）───────────────────


def build_resilient_agent(tools: list[BaseTool], model: Any) -> Any:
    """组装一个"工具报错也不会崩"的 agent。

    **本周最反直觉的一件事**：create_agent 默认不接住工具异常。
    工具抛 ValueError，整个 agent.invoke() 就炸了。

    而你 w02 手写的 ToolRegistry.call 是主动接住所有异常、把错误文本返回给模型的。
    也就是说这一点上**你手写的版本比框架的默认行为更健壮**——
    框架把这个决策留给了你，因为"该不该让模型看到错误"要看场景。

    Args:
        tools: 可用工具列表。
        model: 聊天模型。

    Returns:
        编译好的 agent。工具抛异常时会变成一条 ToolMessage 交给模型，
        而不是中断整个调用。

    思路：
      from langchain.agents.middleware import ToolErrorMiddleware

      create_agent 有个 middleware 参数，收一个列表：
          middleware=[ToolErrorMiddleware(on_error=...)]

      on_error 是个函数，签名是 (异常, 请求) -> str，返回的字符串会变成
      ToolMessage 的内容。最简单的写法是一个 lambda：
          lambda error, request: f"工具执行失败：{error}"

      想想 w01 学的那条：错误信息要能让**模型**自己修好。
      光说"失败了"模型只能瞎猜，带上原因它下一轮就能改对。
    """
    raise NotImplementedError


def trace_of(result: dict[str, Any]) -> list[str]:
    """把 agent 跑完的结果压成一条可读的执行轨迹。

    调 agent 时最想知道的就是"它走了哪几步"。LangSmith 给你图形界面，
    这个函数给你一行行的文本，写测试断言时更好用。

    Args:
        result: agent.invoke(...) 的返回值。

    Returns:
        每步一行的描述，形如：
            ["human: 上海天气？",
             "ai -> get_weather({'city': '上海'})",
             "tool: 上海：晴，25 度",
             "ai: 上海今天晴，25 度。"]

    思路：
      遍历 result["messages"]，按消息类型生成不同格式的字符串。
      判断类型可以用 isinstance（ex1 用过），也可以用 m.type ——
      LangChain 的每条消息都有 .type 属性，值是 "human"/"ai"/"tool"/"system"。
      先跑一下 __main__ 里的例子，把 m.type 打印出来看看再动手。

      AIMessage 带 tool_calls 时要显示调了什么工具、参数是什么；
      不带的时候显示它说的话。
    """
    raise NotImplementedError


if __name__ == "__main__":
    model = scripted(
        AIMessage(
            content="",
            tool_calls=[
                {"name": "get_weather", "args": {"city": "上海"}, "id": "c1", "type": "tool_call"}
            ],
        ),
        AIMessage("上海今天晴，25 度。"),
    )
    agent = build_agent([get_weather], model, "你是一个有用的助手。")

    result = agent.invoke({"messages": [HumanMessage("上海天气怎么样？")]})

    print("每条消息的 type 属性（第 3 段会用到）：")
    for m in result["messages"]:
        print(f"  {type(m).__name__:14} .type = {m.type!r}")

    print("\n执行轨迹：")
    for line in trace_of(result):
        print("  " + line)
