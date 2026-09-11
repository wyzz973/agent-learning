"""练到的 Python：字典索引、对象、for/range、async/await、return。

第 1 段 execute_call 是完整示范；第 2 段 run_agent 填关键循环；
第 3 段 index_tools 独立写。先跑 00_warmup 第 4～6 节。
"""

import asyncio
from typing import Any

from langchain.messages import AnyMessage, HumanMessage, ToolMessage
from langchain.tools import BaseTool


async def execute_call(tools: dict[str, BaseTool], call: dict[str, Any]) -> ToolMessage:
    """第 1 段：执行模型声明的一次工具调用并保留关联编号。

    Args:
        tools: 工具名到工具对象的字典。
        call: 包含 name、args、id、type='tool_call' 的调用对象。
    Returns:
        对应 ToolMessage；运行失败时 status='error' 且含原因。
    Raises:
        NotImplementedError: 被调用的学习者练习未完成。
        KeyError: 调用对象缺 id；正常模型调用保证包含它。
    """
    try:
        selected = tools[call["name"]]  # 名字用于查找对象，此处还未执行。
        async with asyncio.timeout(10):  # 单次工具执行也需要终止边界。
            result = await selected.ainvoke(call)  # 完整调用对象让框架保留 call id。
        return result  # 把工具观察结果交回外层循环。
    except NotImplementedError:
        raise  # 学习占位符必须继续显示为未完成。
    except Exception as error:
        return ToolMessage(  # 将错误作为观察交给模型，使它能改参数。
            content=type(error).__name__ + ": " + str(error),
            tool_call_id=call["id"],
            status="error",
        )


async def run_agent(
    model: Any, tools: dict[str, BaseTool], question: str, max_calls: int = 4
) -> list[AnyMessage]:
    """第 2 段：运行有限的模型—工具—模型循环。

    Args:
        model: 支持 bind_tools 与 ainvoke 的模型或脚本替身。
        tools: 名字唯一的工具字典。
        question: 用户问题。
        max_calls: 模型最多调用次数，必须大于零。
    Returns:
        完整消息列表；收到没有 tool_calls 的最终回复后返回。
    Raises:
        ValueError: max_calls 不为正数。
        RuntimeError: 达到模型调用上限仍未结束。
        TimeoutError: 单次模型超过 20 秒或整轮超过 60 秒。
        NotImplementedError: 循环关键动作尚未完成。
    """
    if max_calls < 1:
        raise ValueError("max_calls 必须大于零")
    bound = model.bind_tools(list(tools.values()))
    history: list[AnyMessage] = [HumanMessage(question)]
    async with asyncio.timeout(60):
        for _ in range(max_calls):
            async with asyncio.timeout(20):
                reply = await bound.ainvoke(history)
            history.append(reply)
            # TODO 1：没有工具调用时返回 history。
            # TODO 2：逐个执行 reply.tool_calls，把每次 execute_call 返回值追加到 history。
            raise NotImplementedError("D08：补停止判断和工具观察回传")
    raise RuntimeError("模型调用达到上限")


def index_tools(tools: list[BaseTool]) -> dict[str, BaseTool]:
    """第 3 段：独立按工具名建立索引。

    Args:
        tools: 工具对象列表，保证名字唯一；允许空列表。
    Returns:
        键为工具 name、值为原工具对象的字典。
    Raises:
        无：输入保证为合法工具列表。

    思路：逐个查看工具名，把同一个对象放在那个名字对应的位置。
    """
    raise NotImplementedError("D07：独立建立工具索引")


if __name__ == "__main__":
    print("本文件包含有限 agent 循环；先完成 D07，再填 D08，运行 test_w05.py。")
