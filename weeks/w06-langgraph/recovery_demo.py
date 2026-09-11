"""教师完整示范：同一进程内的检查点与暂停恢复，不代表磁盘持久化。

练到的 Python：类声明、字典、函数调用；用在 D13/D14，先跑 00_warmup。
"""

import asyncio
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    """request 是待审内容，approved 记录模拟人的决定。"""

    request: str
    approved: bool


def review(state: ApprovalState) -> dict[str, bool]:
    """暂停，把恢复时传入的布尔值作为结果。

    Args:
        state: 待审内容和批准状态。
    Returns:
        approved 更新。
    Raises:
        ValueError: 恢复值不是布尔值；不把任意非空字符串当批准。
    """
    decision = interrupt({"question": "是否接受这个示范结果？", "request": state["request"]})
    if not isinstance(decision, bool):
        raise ValueError("恢复值必须是 True 或 False")
    return {"approved": decision}  # 副作用应放在获批之后，并考虑节点重跑的幂等性。


def build_review_graph() -> Any:
    """建立教师示范图。

    Args:
        无。
    Returns:
        带本进程内存检查点的图。
    Raises:
        无：这里使用固定有效图。
    """
    graph = StateGraph(ApprovalState)
    graph.add_node("review", review)
    graph.add_edge(START, "review")
    graph.add_edge("review", END)
    return graph.compile(checkpointer=InMemorySaver())


async def main() -> None:
    app = build_review_graph()
    for choice in [True, False]:
        config = {"configurable": {"thread_id": str(choice)}}
        print("模拟人工选择：", choice, "；这不是用户对真实操作的授权。")
        paused = await app.ainvoke({"request": "示范摘要", "approved": False}, config)
        print("暂停结果：", paused)
        finished = await app.ainvoke(Command(resume=choice), config)
        print("恢复结果：", finished)
        print("保存的状态：", app.get_state(config).values)
    print("退出这个进程后内存检查点消失；跨进程恢复安排在 w09。")


if __name__ == "__main__":
    asyncio.run(main())
