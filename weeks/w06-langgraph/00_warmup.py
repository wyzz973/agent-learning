"""练到的 Python：TypedDict、函数传参、部分字段更新；用在 ex1_graph。"""

import asyncio
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class GreetingState(TypedDict):
    """name 是输入，text 是输出；运行时仍是字典。"""

    name: str
    text: str


def greet(state: GreetingState) -> dict[str, str]:
    """产生一个字段的状态更新。

    Args:
        state: 含名字的状态字典。
    Returns:
        问候文本更新。
    Raises:
        KeyError: 缺 name 字段。
    """
    return {"text": "你好，" + state["name"]}  # 更新字段由图合并。


def route(state: GreetingState) -> str:
    """示范条件边返回节点名。

    Args:
        state: 当前状态，本示范始终前往 greet。
    Returns:
        固定路由名字。
    Raises:
        无：仅用于说明接口。
    """
    return "greet"


async def main() -> None:
    state: GreetingState = {"name": "Lin", "text": ""}
    print("1. 用在 ex1：TypedDict 实例仍是", type(state))
    print("一个节点返回：", greet(state), "原状态：", state)
    graph = StateGraph(GreetingState)
    graph.add_node("greet", greet)  # 传函数本身，不能写 greet(state) 把它提前执行。
    graph.add_conditional_edges(START, route, {"greet": "greet"})
    graph.add_edge("greet", END)
    app = graph.compile()
    print("2. 用在 ex1：图编译后再执行")
    print(await app.ainvoke(state))
    print("固定边 add_edge 起点→终点；条件边根据函数返回名选终点。")
    print("3. 用在 recovery_demo：async for 逐次读取异步事件")
    async for event in app.astream(state, stream_mode="updates"):
        print(event)
    print("4. 用在 recovery_demo：创建内存保存器和恢复命令")
    print(type(InMemorySaver()), Command(resume=True))
    print("interrupt 必须在可恢复的图节点中运行；下一份完整示范演示其执行位置。")
    print("config 中的 configurable/thread_id 指定会话；get_state(config).values 读取保存状态。")


if __name__ == "__main__":
    asyncio.run(main())
