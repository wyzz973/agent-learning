"""练习 4：init_chat_model —— 一行换厂商。

你 w02 手写的 OpenAICompatLLM 只能连 OpenAI 兼容接口。换 Anthropic 要重写
整个 complete：它的工具调用叫 tool_use，混在 content 数组里，格式差得远。

init_chat_model 把这层全包了：

    init_chat_model("deepseek:deepseek-chat")
    init_chat_model("anthropic:claude-opus-5")

后面的代码一行不用改——这就是本周自检标准里那条"两个厂商间切换而不改其他代码"。

没有测试，靠你自己跑。需要 .env 里的 key。

三段坡道：
  1. parse_model_id  我已写完
  2. make_model      骨架给你了
  3. main            独立完成
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from ex2_tools import get_weather, search_notes
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langsmith import traceable

load_dotenv()

# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


def parse_model_id(model_id: str) -> tuple[str, str]:
    """把 "provider:model" 拆成两段。

    【已实现】w01 ex5 你写过一模一样的东西，这里搬过来。

    Args:
        model_id: 形如 "deepseek:deepseek-chat"。

    Returns:
        (provider, model) 两元组。

    Raises:
        ValueError: 格式不是恰好一个冒号分隔的两段。
    """
    parts = model_id.split(":")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"模型标识要写成 provider:model，收到的是 {model_id!r}")
    return parts[0], parts[1]


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


def make_model(model_id: str | None = None) -> Any:
    """按标识创建一个聊天模型。

    Args:
        model_id: "provider:model" 格式。不传就读环境变量 DEFAULT_MODEL。

    Returns:
        LangChain 的聊天模型对象，可直接交给 create_agent。

    Raises:
        ValueError: 既没传参数、环境变量里也没有。
    """
    # 第 1 步（已给）：参数优先，其次环境变量，都没有就大声失败。
    model_id = model_id or os.environ.get("DEFAULT_MODEL")
    if not model_id:
        raise ValueError("没有指定模型：传 model_id 参数，或在 .env 里设 DEFAULT_MODEL")

    parse_model_id(model_id)  # 格式不对就在这里炸，比连上厂商之后再炸好

    # 第 2 步（轮到你）：调 init_chat_model 造出模型并返回。
    #   最简形式：init_chat_model(model_id)
    #   DeepSeek 需要额外指定接口地址，所以要多传一个参数：
    #       base_url=os.environ.get("LLM_BASE_URL")
    #   （其他厂商传 None 也无妨，SDK 会用各自的默认地址）
    #   还可以传 temperature=0，让输出更稳定——调试期建议这么做。
    # TODO 在这里创建并返回模型
    raise NotImplementedError


# ─────────────────── 第 3 段：独立完成 ───────────────────


@traceable
async def ask(question: str, model_id: str | None = None) -> str:
    """问一个问题，跑完整个 agent 循环。

    Args:
        question: 要问的问题。
        model_id: 用哪个模型，不传走 DEFAULT_MODEL。

    Returns:
        模型的最终文本回答。

    思路（三行左右）：
      1. model = make_model(model_id)
      2. agent = create_agent(model=..., tools=[get_weather, search_notes],
                              system_prompt="...")
      3. result = await agent.ainvoke({"messages": [HumanMessage(question)]})
         然后返回 result["messages"][-1].text

      注意是 ainvoke 不是 invoke —— 这个函数是 async 的。
      LangChain 的每个方法基本都有 a 开头的异步版本。
    """
    raise NotImplementedError


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "上海天气怎么样？再帮我搜两条关于 agent 的笔记"
    print(f"问题: {q}\n")
    print("回答:", asyncio.run(ask(q)))
    print("\n试试换个模型（需要对应的 key）：")
    print('  asyncio.run(ask(q, "anthropic:claude-opus-5"))')
    print("  除了这一个字符串，其他代码一行都不用改 —— 这就是本周的自检标准。")
