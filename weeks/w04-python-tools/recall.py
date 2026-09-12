RECORDS = [
    {"path": "app/cache.py", "content": "Cache lookup helper."},
    {"path": "docs/cache.md", "content": "How caching works."},
]


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
    for record in records:
        if cleaned in record["path"].lower() or cleaned in record["content"].lower():
            matches.append(record)

    return matches


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
    hits: list[dict[str, str]] = []
    for record in records:
        path = record["path"]
        hits.append({"path": path})
    return hits
