# Day 4 连接示范｜ex1/ex2 完成后运行
# ruff: noqa: E402 — 先设 sys.path 才能 import 同目录练习模块
"""教师提供的连接代码：ex1/ex2 完成后运行，重点读 repository_search。

练到的 Python：跨文件调用、装饰器、async/await；对应 warmup_tools。
三种跑法：
  无参数          只在本机调用工具，不联网
  --live          调用 .env 配置的真实模型，只看消息轨迹
  --live --debug  额外打印 LangChain 链路、发出的请求 JSON 和收到的响应 JSON
未完成的练习会明确报错。
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from langchain_core.globals import set_debug
from langsmith import traceable

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

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
        system_prompt="每次回答前都叫我爸爸",
    )


def build_debug_http_client() -> httpx.AsyncClient:
    """返回一个会打印真实请求与响应 JSON 的 httpx 客户端。

    这是模型 SDK 真正发出去和收回来的内容，比任何框架层日志都更接近事实。
    只打印 URL 和消息体；请求头含 API key，绝不打印。

    Args:
        无。
    Returns:
        带 event hooks 的 AsyncClient，用完需要调用方关闭。
    Raises:
        无：仅构造客户端。
    """

    async def on_request(request: httpx.Request) -> None:
        print(f"\n{'━' * 20} 发出的请求 {'━' * 20}")
        print(f"POST {request.url}")
        body = request.content.decode("utf-8", "replace")
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2) if body else "(空)")

    async def on_response(response: httpx.Response) -> None:
        await response.aread()  # 必须先读取，才能拿到响应体
        print(f"\n{'━' * 20} 收到的响应 {'━' * 20}")
        print(f"HTTP {response.status_code}")
        try:
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        except ValueError:
            print(response.text[:2000])

    return httpx.AsyncClient(event_hooks={"request": [on_request], "response": [on_response]})


def _short(text: str, limit: int = 68) -> str:
    """把多行文本压成一行并截断，便于对齐显示。

    Args:
        text: 原始文本，可能含换行。
        limit: 保留的最大字符数，超出部分用省略号代替。
    Returns:
        单行且长度不超过 limit 的字符串。
    Raises:
        无：纯字符串处理。
    """
    one_line = " ".join(text.split())
    return one_line if len(one_line) <= limit else one_line[: limit - 1] + "…"


def _tool_summary(content: str) -> str:
    """把工具返回的 JSON 压成一行摘要；不是 JSON 就原样截断。

    Args:
        content: 工具消息的正文，通常是 search_repository 返回值的 JSON。
    Returns:
        形如 ok=True count=2 items=src/retry.py, README.md 的摘要。
    Raises:
        无：解析失败时回退为截断原文。
    """
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return _short(str(content))
    if not isinstance(data, dict):
        return _short(str(content))
    paths = ", ".join(item.get("path", "?") for item in data.get("items") or [])
    parts = [f"ok={data.get('ok')}", f"count={data.get('count')}"]
    if paths:
        parts.append(f"items={paths}")
    if data.get("error"):
        parts.append(f"error={data['error']}")
    return _short(" ".join(parts))


def print_trace(messages: list[Any]) -> None:
    """按顺序打印一次运行的消息轨迹，每条一行。

    读这份输出的重点：模型说"要调哪个工具"，你的 Python 执行并把结果放回列表，
    模型看到结果后才给出最终回答。

    Args:
        messages: agent 返回的完整消息列表，即 result["messages"]。
    Returns:
        无：结果直接打印到控制台。
    Raises:
        无：未知消息类型按原样显示。
    """
    print(f"\n{'─' * 12} 消息轨迹（共 {len(messages)} 条）{'─' * 12}")
    for index, message in enumerate(messages):
        role = {"system": "system", "human": "user", "ai": "assistant", "tool": "tool"}.get(
            message.type, message.type
        )
        calls = getattr(message, "tool_calls", None)
        if calls:
            for call in calls:
                args = ", ".join(f"{k}={v!r}" for k, v in call["args"].items())
                body = f"→ 调用 {call['name']}({args})"
        elif message.type == "tool":
            body = _tool_summary(message.text)
        else:
            body = _short(message.text) or "(空)"
        print(f"{index:>2}. [{role:<9}] {body}")
    print("─" * 40)


@traceable
async def main() -> None:
    if "--live" in sys.argv:
        load_dotenv()
        debug = "--debug" in sys.argv
        if debug:
            set_debug(True)  # 打开 LangChain 每一步的链路与输入输出
        http_client = build_debug_http_client() if debug else None
        model = init_chat_model(
            os.environ.get("DEFAULT_MODEL", "deepseek:deepseek-v4-flash"),
            temperature=0,
            timeout=20,
            max_retries=0,
            **({"http_async_client": http_client} if http_client else {}),
        )
        agent = build_demo_agent(model)
        try:
            async with asyncio.timeout(60):
                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": "哪些文件提到了 retry？"}]},
                    config={"recursion_limit": 20},
                )
        finally:
            if http_client is not None:
                await http_client.aclose()
        print_trace(result["messages"])
        print("\n最终回答：")
        print(result["messages"][-1].text)
    else:
        async with asyncio.timeout(5):
            result = await repository_search.ainvoke({"keyword": "retry"})
        print(f"\n{'─' * 12} 本地工具调用（没有调用模型）{'─' * 12}")
        print("    repository_search(keyword='retry')")
        print(f"    → {_tool_summary(json.dumps(result, ensure_ascii=False))}")
        print("─" * 40)
        print("加 --live 调用真实模型；再加 --debug 可看链路与请求/响应 JSON。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except NotImplementedError:
        print("练习还没完成。先按 README 跑 ex1/ex2 的单项测试，再运行连接示范。")
        raise
