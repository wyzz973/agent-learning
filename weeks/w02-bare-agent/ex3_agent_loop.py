"""练习 3：agent 循环。本周的核心，也是整个 12 周的核心。

一句话说清 agent 是什么：

    把消息历史发给模型
      → 模型要么说话（结束），要么说"我要调这几个工具"
      → 你执行工具，把结果追加进历史
      → 再发一次
      → 直到模型不再要求调工具，或者撞上轮次上限

**就这些。** LangChain 的 create_agent、LangGraph 的 ReAct，底下都是这个循环。
写完这个文件，那些框架对你就不再是黑盒。

关于测试：真实模型每次回答都不一样，没法写确定的测试。所以我们定义一个 LLM
Protocol，让"真模型"和"照剧本演的假模型"都满足它。测试用假的——离线、免费、
结果确定。这是测试一切不确定系统的通用手法，第 9 周做 evals 时还会用到。

练到的 Python：Protocol、TypedDict、while 循环、for-else、类的组合。

本文件三段坡道：
  1. FakeLLM / run_once  我已写完
  2. Agent.run 主循环    骨架给你了
  3. 轮次护栏            独立完成
"""

from __future__ import annotations

from typing import Protocol, TypedDict

from ex1_messages import Conversation, ToolCall
from ex2_tool_registry import ToolRegistry
from langsmith import traceable


class LLMResponse(TypedDict):
    """模型的一次回复。

    两个字段至少有一个有内容：说话时 content 有值，要调工具时 tool_calls 非空。
    """

    content: str | None
    tool_calls: list[ToolCall]


class LLM(Protocol):
    """任何能"收消息和工具定义、返回一次回复"的东西都算 LLM。

    真实模型和 FakeLLM 都满足它，所以 Agent 不关心自己拿到的是哪个。
    """

    async def complete(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> LLMResponse:
        """请求模型给出下一步。

        Args:
            messages: 完整的消息历史。
            tools: 可用工具的定义列表。

        Returns:
            模型的回复。
        """
        ...


# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


class FakeLLM:
    """照剧本演的假模型。测试用它，不联网不花钱，结果完全确定。

    它满足 LLM Protocol（有同样签名的 complete 方法），但没有继承任何东西。
    """

    def __init__(self, script: list[LLMResponse]) -> None:
        """按剧本创建。

        Args:
            script: 预先写好的回复序列，第 n 次调用返回第 n 条。
        """
        self.script = list(script)
        self.seen_messages: list[list[dict[str, object]]] = []  # 记录每次收到的历史，供测试断言

    async def complete(
        self, messages: list[dict[str, object]], tools: list[dict[str, object]]
    ) -> LLMResponse:
        """返回剧本里的下一条。

        Args:
            messages: 收到的消息历史，会被记录下来。
            tools: 收到的工具定义，这里用不上。

        Returns:
            剧本里的下一条回复。

        Raises:
            AssertionError: 剧本演完了还在被调用——说明循环没有正确停止。
        """
        self.seen_messages.append(list(messages))
        assert self.script, "剧本演完了还在调模型，说明循环没停下来"
        return self.script.pop(0)


@traceable
async def run_once(llm: LLM, conversation: Conversation, registry: ToolRegistry) -> LLMResponse:
    """只跟模型交互一轮，不处理工具。

    【已实现，先读懂】这是主循环里的一次迭代，把它看懂再往下。

    Args:
        llm: 模型。
        conversation: 消息历史。
        registry: 工具注册表，这里只用它导出工具定义。

    Returns:
        模型这一轮的回复。
    """
    response = await llm.complete(conversation.to_api_format(), registry.to_schemas())
    conversation.add_assistant(response["content"], response["tool_calls"])
    return response


class Agent:
    """一个最小的 agent。"""

    def __init__(self, llm: LLM, registry: ToolRegistry, max_iterations: int = 10) -> None:
        """组装一个 agent。

        Args:
            llm: 满足 LLM Protocol 的模型。
            registry: 可用工具。
            max_iterations: 循环上限。**没有这个护栏，模型可能无限调工具烧光你的钱。**
        """
        self.llm = llm
        self.registry = registry
        self.max_iterations = max_iterations

    # ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────

    @traceable
    async def run(self, conversation: Conversation, user_input: str) -> str:
        """跑完一整轮对话，返回模型的最终答案。

        Args:
            conversation: 消息历史，会被就地修改。
            user_input: 用户这次说的话。

        Returns:
            模型的最终文本回复。撞上轮次上限时返回一句说明。
        """
        # 第 1 步（已给）：把用户的话记进历史。
        conversation.add_user(user_input)

        # 第 2 步（已给）：循环最多 max_iterations 次。
        for _ in range(self.max_iterations):
            # 第 3 步（已给）：问模型。run_once 已经帮你把回复记进历史了。
            response = await run_once(self.llm, conversation, self.registry)

            # 第 4 步（轮到你）：如果模型没有要求调工具，说明它给出最终答案了，
            #   直接返回 response["content"]。content 可能是 None，用 or "" 兜底。
            #   提示：判断 if not response["tool_calls"]:
            if not response["tool_calls"]:
                return response["content"] or ""
            # 第 5 步（轮到你）：模型要调工具。遍历 response["tool_calls"]，
            #   对每一个：
            #     用 self.registry.call(工具名, 参数) 执行，拿到结果字符串
            #     用 conversation.add_tool_result(那个 call 的 id, 结果) 记进历史
            #   注意 registry.call 不会抛异常，失败也是返回一段字符串，直接记进去就行——
            #   **让模型自己看到错误并重试**，这是 agent 和普通程序最大的差异。
            # TODO 在这里执行工具并记录结果
            for tool_call in response["tool_calls"]:
                result = self.registry.call(tool_call["name"], tool_call["arguments"])
                conversation.add_tool_result(tool_call["id"], result)
            # 循环回到第 3 步，模型会看到工具结果，然后决定下一步

        # 第 6 步（第 3 段，独立完成）：能走到这里说明 for 跑完了都没 return，
        #   也就是撞上了轮次上限。返回一句说明，**信息里要带上 max_iterations 的值**。
        #   为什么不抛异常：调用方拿到一句话比拿到一个崩溃更有用，
        #   而且这是可预期的正常结果，不是程序出错。
        return f"达到了轮次上限：{self.max_iterations}"


if __name__ == "__main__":
    import asyncio

    from ex2_tool_registry import calculator, get_weather

    async def demo() -> None:
        """跑一个照剧本演的 agent，观察消息历史怎么长出来。"""
        registry = ToolRegistry()
        registry.register(get_weather)
        registry.register(calculator)

        # 剧本：先要调天气工具，拿到结果后给出最终回答
        llm = FakeLLM(
            [
                {
                    "content": None,
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": '{"city": "上海"}'}
                    ],
                },
                {"content": "上海今天晴，25 度。", "tool_calls": []},
            ]
        )

        conversation = Conversation("你是一个有用的助手。")
        agent = Agent(llm, registry)
        answer = await agent.run(conversation, "上海天气怎么样？")

        print("最终答案:", answer)
        print("\n完整消息历史:")
        for i, m in enumerate(conversation.messages):
            content = m.get("content") or f"(调用 {len(m.get('tool_calls', []))} 个工具)"
            print(f"  {i}. [{m['role']:9}] {content}")

    asyncio.run(demo())
