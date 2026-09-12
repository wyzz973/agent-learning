# Day 4 框架热身｜只读只跑，不用写
"""Day 4 的框架热身，只读只跑，全部离线。

练到的 Python：装饰器、函数作为值、async def/await、async with、模块属性。
用在 ex2 完成后的 agent_demo；基础循环先看 00_warmup。
框架只看 @tool、ainvoke、create_agent 三个连接点；限制器由教师提供。
"""

import asyncio
import os
import sys
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.tools import tool


@tool
def keyword_length(keyword: str) -> dict[str, Any]:
    """返回关键词的字符数，示范一个普通函数如何变成工具。

    Args:
        keyword: 任意字符串，空字符串的长度为零。
    Returns:
        包含 length 的字典。
    Raises:
        无：框架在调用函数前校验字符串参数。
    """
    size = len(keyword)  # 工具内部运行的仍是普通 Python 代码。
    return {"length": size}  # 把有固定字段的结果返回调用方。


async def main() -> None:
    print("1. 用在 ex2 → agent_demo：@tool 把函数包装成工具对象")
    print("工具名:", keyword_length.name)
    print("模型看到的说明:\n", keyword_length.description)
    print("输入 schema:", keyword_length.get_input_schema().model_json_schema())

    print("\n2. 用在 ex2 → agent_demo：await 接住调用的结果")
    async with asyncio.timeout(5):
        result = await keyword_length.ainvoke({"keyword": "retry"})
    print("普通字典参数 -> 工具函数 -> 返回字典:", result)
    print("这次是代码指定调用，尚未让模型决定用哪个工具。")

    print("\n3. 用在 ex2 → agent_demo：工具放在列表里传入 create_agent")
    tools = [keyword_length]
    print("列表中的工具:", tools[0].name)
    print("组装函数的名字:", create_agent.__name__)
    limit = ModelCallLimitMiddleware(run_limit=4, exit_behavior="error")
    print("限制器类型:", type(limit))
    print("agent_demo 用 create_agent(model=model, tools=[...], middleware=[limit]) 组装。")
    print("await agent.ainvoke(...) 运行循环；result['messages'][-1].text 读末条文本。")
    print("asyncio.timeout 包住整个异步调用，限制器另管模型调用次数。")

    print("\n4. 用在 ex2 → agent_demo：启动与配置写法")
    print("命令行参数列表:", sys.argv)
    print("是否选择 --live:", "--live" in sys.argv)
    print("缺少配置时用默认值:", os.environ.get("W04_EXAMPLE_SETTING", "demo"))
    print("live 模式先 load_dotenv() 读 .env，再 init_chat_model(...) 初始化模型。")
    print("try/except 捕获预计的运行失败；raise 原样重抛，避免把失败显示为成功。")
    try:
        empty: dict[str, str] = {}
        print(empty["missing"])
    except KeyError as error:
        print("捕获的类型和原因:", type(error).__name__ + ": " + str(error))


if __name__ == "__main__":
    asyncio.run(main())
