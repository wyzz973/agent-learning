# Day 3-4｜本文件含练习 3 和练习 4（共 5 个）
"""练习 2：把你写的数据处理函数接成一个能被 agent 使用的工具。

练到的 Python：函数参数、接住返回值、跨文件 import、if/return、len、字典、None。
对应 00_warmup 第 4～6 节。先完成 ex1；无需学习新的框架 API。

第 1 段 error_result：示范。
第 2 段 success_result：你填数量和返回对象。
第 3 段 search_repository：你独立连接各函数。
"""

from typing import Any

from ex1_records import find_matches, make_hits


# ── 示范（不编号）· 第 1 段：完整示范。所有结果使用相同的四个字段。
def error_result(message: str) -> dict[str, Any]:
    """把可预期的输入错误表示成工具结果。

    Args:
        message: 指向可修正原因的错误说明；本函数原样保留，不做校验。
    Returns:
        含 ok=False、空 items、count=0 和错误说明 error 的字典。
    Raises:
        无：此函数只组装结果。
    """
    result = {  # 创建形状固定的结果字典。
        "ok": False,  # 告诉调用方这次输入无效。
        "items": [],  # 即使失败，也保留列表字段。
        "count": 0,  # 发生此错误时没有结果项。
        "error": message,  # 保留原因，让调用方能修正输入。
    }
    return result  # 返回对象，而不是只打印出来。


# ── 练习 3/5 · Day 3 · 第 2 段：按下面的输入输出契约完成 TODO。
def success_result(records: list[dict[str, str]]) -> dict[str, Any]:
    """整理成功的搜索结果，包括“查过了但没找到”的情况。

    Args:
        records: ex1 找到的记录列表；每项含 path、content；允许空列表。
    Returns:
        含 ok=True、items=路径字典列表、count=条数、error=None 的字典。
        空列表对应 {"ok": True, "items": [], "count": 0, "error": None}。
    Raises:
        KeyError: 记录缺少 path；练习数据保证包含它。
    """
    hits = make_hits(records)
    count = len(hits)
    return {"ok": True, "items": hits, "count": count, "error": None}


# ── 练习 4/5 · Day 4 · 第 3 段：只有签名和契约。由你组合已经写过的函数。
def search_repository(records: list[dict[str, str]], keyword: str) -> dict[str, Any]:
    """在迷你仓库中查找路径或正文包含关键词的文件。

    Args:
        records: 每项含字符串 path、content 的记录列表；允许空列表，不修改输入。
        keyword: 字符串，忽略英文大小写与两端空白；纯空白属于输入错误。
    Returns:
        固定包含 ok、items、count、error。成功时 items 仅含路径字典；
        没找到也是成功。空关键词返回 error_result("keyword must not be blank")。
    Raises:
        KeyError: 内部记录缺少约定字段；这是程序数据错误，需要开发者修正。

    思路：先处理空关键词；有效时查找、接住结果、交给成功结果函数，再返回。
    输入校验失败是交给模型的反馈；不要把编程错误或未完成的 TODO 当成搜索成功。
    """
    cleaned = keyword.strip().lower()
    if cleaned == "":
        return error_result("keyword must not be blank")
    matches = find_matches(records, cleaned)
    return success_result(matches)


if __name__ == "__main__":
    print("第 1 段示范:", error_result("keyword must not be blank"))
    print("先用 pytest -k success_result，再用 -k search_repository。")
