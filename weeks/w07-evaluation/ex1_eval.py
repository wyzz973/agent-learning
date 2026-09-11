"""练到的 Python：in/not in、列表、循环计数、除法与 None。

第 1 段 is_known_path 是示范；第 2 段 unknown_paths 填空；
第 3 段 score_cases 独立写。先运行 00_warmup。
"""

from typing import Any


def is_known_path(path: str, known_paths: list[str]) -> bool:
    """第 1 段：检查单个路径是否在实际证据集合中。

    Args:
        path: 要核对的路径字符串。
        known_paths: 本轮实际取得的路径列表，允许为空。
    Returns:
        路径存在返回 True，否则 False；这里只检查成员关系。
    Raises:
        无：输入保证为字符串及列表。
    """
    known = path in known_paths  # 从实际证据查成员，不能用模型的自信程度作判断。
    return known  # 布尔值可被上层评分函数消费。


def unknown_paths(paths: list[str], known_paths: list[str]) -> list[str]:
    """第 2 段：按顺序找出没有证据支持的路径。

    Args:
        paths: 回答中出现的路径列表，保证同一列表内不重复。
        known_paths: 本轮取得的路径列表。
    Returns:
        paths 中不属于 known_paths 的项；空输入返回 []。
    Raises:
        NotImplementedError: 筛选尚未完成。
    """
    unknown: list[str] = []
    for path in paths:
        # TODO：判断这个路径不在证据中时，把它收集起来。
        raise NotImplementedError("D16：逐项核对来源：" + path)
    return unknown


def score_cases(results: list[bool]) -> dict[str, Any]:
    """第 3 段：独立统计固定样例的通过率。

    Args:
        results: 每项为一个样例的布尔评分；允许空列表。
    Returns:
        passed 为 True 的数量，total 为总数，rate 为 passed/total；
        没有样例时 rate=None，不声称通过率 100%。
    Raises:
        NotImplementedError: 评分尚未完成。

    思路：逐个数通过数量，得到总数；分别考虑总数为零与不为零的返回值。
    """
    raise NotImplementedError("D17：独立统计评估结果")


if __name__ == "__main__":
    print(is_known_path("a.py", ["a.py"]), is_known_path("fake.py", ["a.py"]))
