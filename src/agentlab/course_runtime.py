"""跨周教师连接：加载本人练习，保持搜索逻辑只有一份。

这里提供教学文件、脚本模型和应用装配，不实现任何学习者 TODO。
"""

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.messages import AIMessage
from langchain.tools import BaseTool, tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

ROOT = Path(__file__).resolve().parents[2]
# 此文件在 src/agentlab，parents[2] 是仓库根目录。
FIXTURE = ROOT / "curriculum/fixtures/repository"
LESSONS = {
    "records": ("w04-python-tools", "ex2_search_tool"),
    "files": ("w05-files-loop", "ex1_files"),
    "loop": ("w05-files-loop", "ex2_loop"),
    "graph": ("w06-langgraph", "ex1_graph"),
    "eval": ("w07-evaluation", "ex1_eval"),
}


def _lesson(name: str) -> ModuleType:
    week, module = LESSONS[name]
    location = str(ROOT / "weeks" / week)
    if location not in sys.path:
        sys.path.insert(0, location)
    return importlib.import_module(module)


def read_records() -> list[dict[str, str]]:
    """通过本人文件工具读取固定教学仓库。

    Args:
        无。
    Returns:
        w04 搜索函数接收的 path/content 列表。
    Raises:
        NotImplementedError: 文件练习未完成。
        RuntimeError: 教学文件读取失败，不以缺失数据继续评分。
    """
    result = []
    files = _lesson("files")
    for relative in ["src/retry.py", "src/chat.py", "README.md"]:
        value = files.read_text_tool(FIXTURE, relative)
        if not value["ok"]:
            raise RuntimeError(value["error"])
        result.append({"path": relative, "content": value["content"]})
    return result


def build_tools() -> list[BaseTool]:
    """用本人代码建立同一套 LangChain 工具。

    Args:
        无。
    Returns:
        搜索与读取两个工具对象。
    Raises:
        无：构建时不会执行学习者函数。
    """

    @tool
    def repository_search(keyword: str) -> dict[str, Any]:
        """在固定教学仓库里查找路径或正文含关键词的文件。

        Args:
            keyword: 非空关键词；忽略大小写和两端空白。
        Returns:
            ok/items/count/error；items 仅含路径，正文需调用读取工具。
        Raises:
            NotImplementedError: 本人前置练习尚未完成。
        """
        try:
            return dict(_lesson("records").search_repository(read_records(), keyword))
        except NotImplementedError:
            raise
        except Exception as error:
            return {"ok": False, "items": [], "count": 0, "error": str(error)}

    @tool
    def read_repository_file(path: str) -> dict[str, Any]:
        """读取教学仓库中的小型文本，不接受仓库外路径。

        Args:
            path: 教学目录内相对 .py/.md 路径，最多 32768 字节。
        Returns:
            ok/path/content/error，错误以对象返回。
        Raises:
            NotImplementedError: 本人文件读取练习未完成。
        """
        return dict(_lesson("files").read_text_tool(FIXTURE, path))

    return [repository_search, read_repository_file]


class ScriptedModel(GenericFakeChatModel):
    """教学回放模型；回复预先编排，不证明模型的自主推理能力。"""

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        """接受与真实模型相同的绑定调用。

        Args:
            tools: 本轮工具列表，回放模型不据此自主选择。
            **kwargs: 框架绑定选项，回放中不使用。
        Returns:
            回放模型自身。
        Raises:
            无：此方法仅适配框架接口。
        """
        return self


def replay_model() -> ScriptedModel:
    """构造搜索→读取→回答的三条回放回复。

    Args:
        无。
    Returns:
        新的回放模型，每次运行使用新实例。
    Raises:
        无：消息来自固定教学剧本。
    """
    return ScriptedModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "repository_search",
                            "args": {"keyword": "retry"},
                            "id": "search-1",
                        }
                    ],
                ),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "read_repository_file",
                            "args": {"path": "src/retry.py"},
                            "id": "read-1",
                        }
                    ],
                ),
                AIMessage(
                    content="脚本回放结束：已展示搜索与读取消息。该固定回复不作为真实模型回答质量证据。"
                ),
            ]
        )
    )


async def run_app(mode: str, model: Any, query: str = "retry") -> dict[str, Any]:
    """调用本人函数完成选定的应用入口。

    Args:
        mode: tool、loop、langchain、graph 或 evaluate。
        model: 模型或回放对象；tool/evaluate 模式不调用它。
        query: 用户查询；回放剧本固定搜索 retry，其他问题请用真实模型。
    Returns:
        模式、结果及消息等可检查记录。
    Raises:
        NotImplementedError: 依赖的本人练习未完成。
        ValueError: 模式未知。
        RuntimeError: 读取或调用上限失败。
        TimeoutError: 整次入口执行超过 65 秒。
    """
    tools = build_tools()
    async with asyncio.timeout(65):
        if mode == "tool":
            return {"mode": mode, "result": await tools[0].ainvoke({"keyword": query})}
        if mode == "evaluate":
            cases = json.loads(
                (ROOT / "curriculum/fixtures/search_cases.json").read_text(encoding="utf-8")
            )
            scores = []
            rows = []
            for case in cases:
                actual = await tools[0].ainvoke({"keyword": case["query"]})
                paths = []
                for item in actual["items"]:
                    paths.append(item["path"])
                passed = actual["ok"] == case["ok"] and paths == case["paths"]
                scores.append(passed)
                rows.append({"query": case["query"], "passed": passed, "actual": actual})
            return {
                "mode": mode,
                "scope": "确定性检索工具评估",
                "score": _lesson("eval").score_cases(scores),
                "cases": rows,
            }

        loop = _lesson("loop")
        if mode == "loop":
            messages = await loop.run_agent(model, loop.index_tools(tools), query)
            return {"mode": mode, "messages": messages}
        if mode == "langchain":
            agent = create_agent(
                model=model,
                tools=tools,
                middleware=[ModelCallLimitMiddleware(run_limit=4, exit_behavior="error")],
            )
            return {
                "mode": mode,
                "result": await agent.ainvoke(
                    {"messages": [{"role": "user", "content": query}]},
                    config={"recursion_limit": 20},
                ),
            }
        if mode == "graph":

            async def search_node(state: dict[str, Any]) -> dict[str, Any]:
                messages = await loop.run_agent(model, loop.index_tools(tools), state["query"])
                return {"answer": messages[-1].text, "messages": messages}

            graph = _lesson("graph").build_search_graph(search_node)
            result = await graph.ainvoke(
                {"query": query, "answer": "", "messages": []}, config={"recursion_limit": 20}
            )
            return {"mode": mode, "result": result}
        raise ValueError("未知运行模式：" + mode)
