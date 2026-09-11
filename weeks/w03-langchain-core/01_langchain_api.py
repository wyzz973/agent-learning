"""API 热身：LangChain 1.0 的五个入口。

先跑 00_warmup.py（Python 语法），再跑这个。

**做练习之前先跑这个文件**，只读只跑不用写，约 15 分钟。

    uv run python weeks/w03-langchain-core/01_langchain_api.py

这周不学新语法了——Python 的部分你上两周已经够用。这周学的是**五个 API 入口**，
以及它们和你 w02 手写的东西怎么对应。

一条警告：网上 90% 的 LangChain 教程是 0.x 的。看到 LLMChain、initialize_agent、
AgentExecutor、ConversationBufferMemory，立刻关掉——那些在 1.0 已经移到
langchain-classic 包里了。只认下面这五个入口。
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


def section(title: str) -> None:
    """打印分节标题。

    Args:
        title: 小节名。
    """
    print(f"\n{'=' * 8} {title} {'=' * 8}")


# ═══════════════ 1. 消息：从字典变成了对象 ═══════════════


def demo_messages() -> None:
    """w02 你用字典表示消息，LangChain 用类。"""
    section("1. 消息类型")

    print("w02 你写的：       {'role': 'user', 'content': '你好'}")
    print("LangChain 写的：   HumanMessage('你好')")

    messages = [
        SystemMessage("你是一个有用的助手。"),
        HumanMessage("上海天气怎么样？"),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "get_weather", "args": {"city": "上海"}, "id": "c1", "type": "tool_call"}
            ],
        ),
        ToolMessage(content="晴，25 度", tool_call_id="c1"),
        AIMessage("上海今天晴，25 度。"),
    ]

    print("\n和你 w02 的四种角色一一对应：")
    for m in messages:
        calls = (
            f"  tool_calls={[c['name'] for c in m.tool_calls]}"
            if getattr(m, "tool_calls", None)
            else ""
        )
        print(f"  {type(m).__name__:14} content={(m.content or '(空)')[:20]!r}{calls}")

    print("\n注意 ToolMessage 的 tool_call_id —— 和你 w02 手动维护的是同一个东西。")


# ═══════════════ 2. @tool：和你手写的那个几乎一样 ═══════════════


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。

    Args:
        city: 城市名，例如"上海"。

    Returns:
        天气描述。
    """
    return f"{city}：晴，25 度"


def demo_tool() -> None:
    """LangChain 的 @tool 做的事，和你 w02 手写的一模一样。"""
    section("2. @tool")

    print(f"名字:     {get_weather.name}")
    print(f"描述:     {get_weather.description}")
    print(f"参数定义: {get_weather.args}")
    print("\n这三样正是你 w02 手写 @tool 时挂进 __tool__ 的东西。")
    print("差别：描述取的是整个 docstring（含 Args/Returns），不只第一行。")

    print(f"\n直接调用它要用 .invoke()：{get_weather.invoke({'city': '北京'})}")
    print("因为被 @tool 装饰后它变成了一个 BaseTool 对象，不再是普通函数——")
    print("这点和你手写的版本不同，你那个是原样返回函数。")


# ═══════════════ 3. create_agent：一行换掉你的整个循环 ═══════════════


class ScriptedChatModel(GenericFakeChatModel):
    """按剧本返回的假模型，用于离线测试。

    继承现成的假模型，只补一个 bind_tools —— create_agent 会调它来绑工具，
    而假模型不需要真的绑，返回自己就行。
    """

    def bind_tools(self, tools: object, **kwargs: object) -> ScriptedChatModel:
        """接受工具绑定但忽略它。

        Args:
            tools: 要绑定的工具，假模型用不上。
            **kwargs: 其他绑定参数，同样忽略。

        Returns:
            模型自己。
        """
        return self


def demo_create_agent() -> None:
    """你 w02 写的一百行循环，这里是一行。"""
    section("3. create_agent")

    script = iter(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_weather",
                        "args": {"city": "上海"},
                        "id": "c1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage("上海今天晴，25 度。"),
        ]
    )

    agent = create_agent(
        model=ScriptedChatModel(messages=script),
        tools=[get_weather],
        system_prompt="你是一个有用的助手。",
    )
    result = agent.invoke({"messages": [HumanMessage("上海天气怎么样？")]})

    print("跑出来的消息序列：")
    for m in result["messages"]:
        calls = (
            f"  tool_calls={[c['name'] for c in m.tool_calls]}"
            if getattr(m, "tool_calls", None)
            else ""
        )
        print(f"  [{type(m).__name__:14}] {(m.content or '(空)')[:30]}{calls}")

    print("\n和你 w02 跑出来的四条一模一样。create_agent 底下就是你写的那个循环。")


# ═══════════════ 4. init_chat_model：一行换厂商 ═══════════════


def demo_init_chat_model() -> None:
    """provider:model 一个字符串搞定所有厂商。"""
    section("4. init_chat_model")

    print("你 w02 手写的 OpenAICompatLLM 只能连 OpenAI 兼容接口。")
    print("换成 Anthropic 要重写整个 complete —— 格式差得远。\n")
    print("LangChain 的写法：")
    print('  model = init_chat_model("deepseek:deepseek-chat")')
    print('  model = init_chat_model("anthropic:claude-opus-5")')
    print('  model = init_chat_model("openai:gpt-5")')
    print("\n后面的代码一行不用改。你 w02 手写的那层格式转换（_to_wire_message、")
    print("complete 里的解析），LangChain 为每个厂商都写好了。")


# ═══════════════ 5. content_blocks：跨厂商读同一份内容 ═══════════════


def demo_content_blocks() -> None:
    """不同厂商的响应结构不同，content_blocks 抹平了差异。"""
    section("5. content_blocks")

    msg = AIMessage("这是模型说的话。")
    print(f"msg.content       = {msg.content!r}")
    print(f"msg.content_blocks = {msg.content_blocks}")
    print("\n为什么需要它：有的厂商 content 是字符串，有的是数组（文本块、思考块、")
    print("工具调用块混在一起）。content_blocks 让你用同一种方式读，不用判断厂商。")
    print("推理模型的 thinking 内容也从这里取。")


def main() -> None:
    """按顺序跑完所有小节。"""
    demo_messages()
    demo_tool()
    demo_create_agent()
    demo_init_chat_model()
    demo_content_blocks()
    print("\n跑完了。回去做练习，卡住就回来查对应小节。")


if __name__ == "__main__":
    main()
