"""练到的 Python：TypedDict、字典更新、函数作为值、条件分支。

第 1 段 normalize_query 是完整示范；第 2 段 choose_route 填空；
第 3 段 build_search_graph 独立写。先运行 00_warmup。
"""

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class SearchState(TypedDict):
    """共享状态：query 是输入，answer 是回答，messages 是执行证据。"""

    query: str
    answer: str
    messages: list[Any]


def normalize_query(state: SearchState) -> dict[str, str]:
    """第 1 段：只返回本节点修改的字段。

    Args:
        state: 已有 query 字符串的共享状态。
    Returns:
        去掉关键词两端空白的更新字典。
    Raises:
        KeyError: 内部状态缺 query。
    """
    cleaned = state["query"].strip()  # 取一个字段处理，不把整个 state 当字符串。
    return {"query": cleaned}  # 图把这个更新合入已有状态，其他字段保留。


def clarify_query(state: SearchState) -> dict[str, str]:
    """教师提供的空输入节点。

    Args:
        state: 路由后的共享状态。
    Returns:
        提示用户提供关键词的回答更新。
    Raises:
        无：这里只产生固定提示。
    """
    return {"answer": "请提供搜索关键词"}


def choose_route(state: SearchState) -> str:
    """第 2 段：规范化后的空查询走 clarify，否则走 search。

    Args:
        state: 已经过 normalize_query 的状态。
    Returns:
        'clarify' 或 'search'，对应图中的节点名。
    Raises:
        NotImplementedError: 路由尚未完成。
    """
    query = state["query"]
    # TODO：判断 query 是否为空，返回对应的路由名字。
    raise NotImplementedError("D11：根据当前数据选择下一步")


def build_search_graph(search_node: Any) -> Any:
    """第 3 段：独立连接带条件分支的图。

    Args:
        search_node: 教师/调用方提供的异步节点，接收状态，返回 answer/messages 更新。
    Returns:
        compile 后的图：START→normalize→按 choose_route 分支；
        search 与 clarify 都通往 END。
    Raises:
        NotImplementedError: 图尚未完成。

    思路：创建 StateGraph(SearchState)；注册 normalize、search、clarify 三个节点；
    连接入口、条件边与两个出口；最后 compile 并返回。不要在组图时调用节点函数。
    """
    raise NotImplementedError("D12：独立连接状态图")


if __name__ == "__main__":
    print(normalize_query({"query": " retry ", "answer": "", "messages": []}))
