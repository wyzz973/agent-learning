"""练习 1：从一批文件记录里取值、筛选、整理。

练到的 Python：list[dict[str, str]]、for、if、in、or、append、return、字符串方法。
对应 00_warmup 第 1～3 节。用普通循环写对就可以。

第 1 段 collect_paths：示范。
第 2 段 find_matches：你填判断和收集。
第 3 段 make_hits：你独立组装返回值。
"""

from sample_repo import FILES


# 第 1 段：完整示范。先预测输出，再运行文件。
def collect_paths(records: list[dict[str, str]]) -> list[str]:
    """按输入顺序收集文件路径。

    Args:
        records: 每项含字符串 path、content 的文件记录列表；允许空列表。
    Returns:
        路径字符串列表，保持输入顺序；空输入返回空列表。
    Raises:
        KeyError: 记录缺少 path；练习数据保证包含它。
    """
    paths: list[str] = []  # 创建最后要返回的容器。
    for record in records:  # 每个 record 是一个字典，不是整份列表。
        path = record["path"]  # 从这个字典中取出一个字符串。
        paths.append(path)  # 将它保存在输出容器中。
    return paths  # 循环结束后再返回，保证所有记录都已经处理。


# 第 2 段：补 TODO，不修改输入记录。
def find_matches(records: list[dict[str, str]], keyword: str) -> list[dict[str, str]]:
    """按关键词筛选文件路径或正文，忽略英文大小写和关键词两端的空白。

    Args:
        records: 每项包含字符串 path、content；允许空列表，不修改输入。
        keyword: 字符串；去掉两端空白后为空时返回空列表。
    Returns:
        匹配记录的列表，保留原字段和原顺序；每条记录最多出现一次。
        例如搜 retry 可以同时找到 src/retry.py 和正文含 retry 的 README.md。
    Raises:
        KeyError: 记录缺少 path 或 content；练习数据保证包含它们。
    """
    cleaned = keyword.strip().lower()
    matches: list[dict[str, str]] = []
    if cleaned == "":
        return matches

    for record in records:
        path = record["path"].lower()
        content = record["content"].lower()
        # TODO：判断任一字段是否包含 cleaned，再把这条记录收集一次。
        raise NotImplementedError("ex1: 判断是否命中，把这一个 record 收集起来")

    return matches


# 第 3 段：仅有签名与契约，函数体由你独立写。
def make_hits(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """只保留匹配记录的路径，给模型足够回答“在哪个文件”的信息。

    Args:
        records: 每项含字符串 path、content；允许空列表，不修改输入。
    Returns:
        仅含 path 键的新字典列表，顺序不变；空输入返回 []。
        例：[{"path": "a.py", "content": "hello"}] -> [{"path": "a.py"}]。
    Raises:
        KeyError: 记录缺少 path；练习数据保证包含它。

    思路：先确定返回容器；逐个取路径、组成小字典、保存；最后交还容器。
    """
    raise NotImplementedError("ex1: 独立写 make_hits")


if __name__ == "__main__":
    print("第 1 段示范:", collect_paths(FILES))
    print("第 2 段从 pytest -k find_matches 开始；第 3 段用 -k make_hits。")
