"""验证路由与图的两个分支。"""

from typing import Any

from ex1_graph import build_search_graph, choose_route, normalize_query


def test_demo_normalize() -> None:
    assert normalize_query({"query": "  Retry  ", "answer": "", "messages": []}) == {
        "query": "Retry"
    }


def test_choose_route() -> None:
    assert choose_route({"query": "", "answer": "", "messages": []}) == "clarify"
    assert choose_route({"query": "retry", "answer": "", "messages": []}) == "search"


async def test_build_search_graph_valid_query() -> None:
    observed = []

    async def search(state: dict[str, Any]) -> dict[str, Any]:
        observed.append(state["query"])
        return {"answer": "found", "messages": []}

    result = await build_search_graph(search).ainvoke(
        {"query": " retry ", "answer": "", "messages": []}
    )
    assert observed == ["retry"]
    assert result["answer"] == "found"


async def test_build_search_graph_empty_query() -> None:
    async def search(state: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError("空输入不能执行搜索")

    result = await build_search_graph(search).ainvoke({"query": "  ", "answer": "", "messages": []})
    assert result["answer"] == "请提供搜索关键词"
