"""练习 4：接上真实模型，并让 LangSmith 看得见。

前三个练习都在跟 FakeLLM 演戏。这一个换成真的。

**没有测试。** 真实模型每次回答都不一样，断言不了。这个文件靠你自己跑、自己看。
这也说明了为什么前三个练习要用 FakeLLM——不可测的东西要隔离在边缘，
核心逻辑（消息、工具、循环）必须可测。

关于 LangSmith：从这周起接上它。不接可观测就调 agent，等于闭着眼睛调试。
它会把每一轮的输入输出、工具调用、耗时都记下来，网页上能一层层点开看。
成本是三行配置。

练到的 Python：httpx 发 POST、构造嵌套请求体、解析嵌套响应、环境变量、装饰器复用。

本文件三段坡道：
  1. 请求体的构造  我已写完
  2. 响应的解析    骨架给你了
  3. 接 LangSmith  独立完成
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from ex1_messages import Conversation
from ex2_tool_registry import ToolRegistry, calculator, get_weather
from ex3_agent_loop import Agent, LLMResponse
from langsmith import traceable

# 必须在模块层加载：@traceable 在导入这个模块时就生效，
# 那一刻它要读 LANGSMITH_* 环境变量。放在函数体里就太晚了。
load_dotenv()

# 设 DEBUG_WIRE=1 就打印每一轮完整的请求体和响应体。
# 平时关着，调 API 出问题时打开——它显示的是真正发出去/收回来的 JSON。
_DEBUG_WIRE = os.environ.get("DEBUG_WIRE") == "1"


class OpenAICompatLLM:
    """直接用 HTTP 调 OpenAI 兼容接口，不走任何 SDK。

    为什么不用 SDK：这周的目的是看清楚 wire format——你发出去的到底是什么 JSON，
    收回来的又是什么。SDK 会把这些包起来，而它们正是你要理解的东西。
    DeepSeek、Kimi、智谱、OpenAI 都兼容这个格式。
    """

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        """配置一个模型客户端。

        Args:
            api_key: API 密钥，从环境变量读，永远不要写进代码。
            model: 模型名，例如 deepseek-chat。
            base_url: 接口地址，例如 https://api.deepseek.com/v1。
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    # ─────────────────── 第 1 段：示范，已写完 ───────────────────

    def _build_payload(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """把消息和工具拼成请求体。

        【已实现，读一遍就知道模型收到的是什么】

        注意工具定义外面要包一层 {"type": "function", "function": {...}}，
        这是 OpenAI 协议的规定，你的 __tool__ 字典正好放进 function 里。

        Args:
            messages: 消息历史。
            tools: 工具定义列表。

        Returns:
            可以直接 json 化发出去的请求体。
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [self._to_wire_message(message) for message in messages],
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
        return payload

    def _to_wire_message(self, m: dict[str, Any]) -> dict[str, Any]:
        """把内部格式的消息转成厂商要的格式。"""
        calls = m.get("tool_calls")
        if not calls:
            return m  # 没有工具调用的消息原样发
        return {
            **m,
            "tool_calls": [
                {
                    "id": c["id"],
                    "type": "function",
                    "function": {"name": c["name"], "arguments": c["arguments"]},
                }
                for c in calls
            ],
        }

    # ─────────────────── 第 2 段：填空 ───────────────────

    @traceable(run_type="llm")
    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        """请求模型，把响应转成我们自己的 LLMResponse。

        Args:
            messages: 消息历史。
            tools: 可用工具定义。

        Returns:
            统一格式的回复，Agent 只认这个格式。

        Raises:
            httpx.HTTPStatusError: 接口返回 4xx/5xx。
        """
        # 第 1 步（已给）：发请求。
        payload = self._build_payload(messages, tools)
        if _DEBUG_WIRE:
            print("\n──── 请求 ────")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            if response.status_code >= 400:
                # raise_for_status 只说状态码，丢掉了服务器写明的原因。
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
            response.raise_for_status()
            data = response.json()

        if _DEBUG_WIRE:
            print("──── 响应 ────")
            print(json.dumps(data, indent=2, ensure_ascii=False))

        # 第 2 步（轮到你）：从嵌套的响应里挖出 content 和 tool_calls。
        #
        #   响应长这样（warmup 第 3 节演示过同样的结构）：
        #     data["choices"][0]["message"] 里有 "content" 和可选的 "tool_calls"
        #
        #   厂商给的 tool_call 长这样：
        #     {"id": "call_x", "function": {"name": "get_weather", "arguments": "{...}"}}
        #   我们的 ToolCall 要的是扁平的：
        #     {"id": "call_x", "name": "get_weather", "arguments": "{...}"}
        #   所以要把 function 那一层拆开。
        #
        #   注意 content 可能是 None（模型只想调工具），tool_calls 可能整个键都不存在，
        #   用 .get(...) or [] 兜底，别用 [] 直接取。
        #
        #   返回形如：{"content": ..., "tool_calls": [...]}
        message = data["choices"][0]["message"]
        content = message.get("content")
        raw_calls = message.get("tool_calls") or []
        tool_calls = [
            {
                "id": c["id"],
                "name": c["function"].get("name"),
                "arguments": c["function"].get("arguments"),
            }
            for c in raw_calls
        ]

        return {
            "content": content,
            "tool_calls": tool_calls,
        }


# ─────────────────── 第 3 段：独立完成 ───────────────────


# 让 LangSmith 记录这个 agent 的每一步。
#
# 做法：从 langsmith 导入 traceable，用 @traceable 装饰下面的 chat 函数。
#   from langsmith import traceable
# 然后确认 .env 里这三行都有值：
#   LANGSMITH_API_KEY=<去 smith.langchain.com 申请，免费>
#   LANGSMITH_TRACING=true
#   LANGSMITH_PROJECT=agent-learning
#
# 跑完去 smith.langchain.com 看，能一层层点开每一轮的输入输出。
# 上周你写的 @tool 就是同一个机制——装饰器在函数外面包一层，做点额外的事。
@traceable
async def chat(question: str) -> str:
    """问一个问题，跑完整个 agent 循环。

    Args:
        question: 要问的问题。

    Returns:
        模型的最终回答。

    Raises:
        ValueError: 缺少必要的环境变量。
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("缺少 DEEPSEEK_API_KEY，请在 .env 里设置")

    llm = OpenAICompatLLM(
        api_key=api_key,
        model=os.environ.get("DEFAULT_MODEL", "deepseek:deepseek-chat").split(":")[-1],
        base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com"),
    )

    registry = ToolRegistry()
    registry.register(get_weather)
    registry.register(calculator)

    conversation = Conversation(
        "你是一个有用的助手。需要查天气或算数时，调用提供的工具，不要自己编造。"
    )
    agent = Agent(llm, registry, max_iterations=5)
    return await agent.run(conversation, question)


if __name__ == "__main__":
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else "上海天气怎么样？顺便算一下 23 * 17"
    print(f"问题: {question}\n")
    print("回答:", asyncio.run(chat(question)))
