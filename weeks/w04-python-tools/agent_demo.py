"""教师提供的连接代码：ex1/ex2 完成后运行，重点读 repository_search。

练到的 Python：跨文件调用、装饰器、async/await；对应 01_tool_warmup。
默认仅在本机调用工具；--live 才调用 .env 配置的模型。未完成的练习会明确报错。
"""

import asyncio
import os
import sys
from typing import Any

from dotenv import load_dotenv
from ex2_search_tool import error_result, search_repository
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from sample_repo import FILES


@tool
def repository_search(keyword: str) -> dict[str, Any]:
    """在教学用迷你仓库中搜索路径或正文，返回匹配的文件路径。

    Args:
        keyword: 要查找的词，忽略英文大小写和两端空白；不可为空。
            例如 retry。这里仅搜索固定教学记录，不能读取磁盘上的真实仓库。
    Returns:
        包含 ok、items、count、error 的对象；items 的每项只含 path。
        查不到时 ok=True 且 count=0；空词时 ok=False，error 提示修正输入。
        执行错误也返回 ok=False，并保留异常类型与原因供模型和开发者检查。
    Raises:
        NotImplementedError: 学习者尚未完成 ex1/ex2；应先完成练习。
    """
    try:
        result = search_repository(FILES, keyword)  # 调用学习者自己写的 Python 函数。
    except NotImplementedError:
        raise  # 未完成的练习必须继续明确显示为未完成。
    except Exception as error:
        return error_result(type(error).__name__ + ": " + str(error))
    return result  # 把结果交回框架。


def build_demo_agent(model: Any) -> Any:
    """把搜索工具装进有模型调用上限的 agent；用于可选体验和离线连接测试。

    Args:
        model: 支持工具调用的已初始化聊天模型，或测试中使用的脚本模型。
    Returns:
        可通过 ainvoke 运行的 agent；每次运行最多调用模型四次。
    Raises:
        ValueError: 模型不兼容或框架配置无效。
    """
    limit = ModelCallLimitMiddleware(run_limit=4, exit_behavior="error")
    return create_agent(
        model=model,
        tools=[repository_search],
        middleware=[limit],
        system_prompt="先使用 repository_search 查找文件，再根据工具结果回答。不要编造路径。",
    )


async def main() -> None:
    if "--live" in sys.argv:
        load_dotenv()
        model = init_chat_model(
            os.environ.get("DEFAULT_MODEL", "deepseek:deepseek-chat"),
            temperature=0,
            timeout=20,
            max_retries=0,
        )
        agent = build_demo_agent(model)
        async with asyncio.timeout(60):
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": "哪些文件提到了 retry？"}]},
                config={"recursion_limit": 20},
            )
        for message in result["messages"]:
            print(message)
        print("最终回答:", result["messages"][-1].text)
    else:
        async with asyncio.timeout(5):
            result = await repository_search.ainvoke({"keyword": "retry"})
        print("本地工具结果（没有调用模型）:", result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except NotImplementedError:
        print("练习还没完成。先按 README 跑 ex1/ex2 的单项测试，再运行连接示范。")
        raise
