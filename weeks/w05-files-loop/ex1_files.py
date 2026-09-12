"""练到的 Python：Path、字符串、try/except、列表筛选；用在 D06/D10。

第 1 段 safe_path 是教师完整示范；第 2 段 read_text_tool 留 TODO；
第 3 段 successful_paths 由本人独立写。先跑 00_warmup 第 1～3 节。
"""

from pathlib import Path
from typing import Any


def safe_path(root: Path, relative_path: str) -> Path:
    """第 1 段：把相对文件名限制在教学目录内部。

    Args:
        root: 教学根目录；允许临时测试目录。
        relative_path: 相对路径；绝对路径、越界和非 .py/.md 后缀会被拒绝。
    Returns:
        解析后的绝对路径；此时文件不一定存在。
    Raises:
        ValueError: 输入路径违反教学范围。
    """
    base = root.resolve()  # 先固定教学目录的真实位置。
    given = Path(relative_path)  # 字符串变成路径对象，尚未读文件。
    if given.is_absolute():  # 不允许绕过根目录直接指定绝对路径。
        raise ValueError("请使用教学目录内的相对路径")
    target = (base / given).resolve()  # 解析 .. 和符号链接的最终位置。
    if not target.is_relative_to(base):  # 最终位置也必须属于根目录。
        raise ValueError("文件超出教学目录")
    if target.suffix not in [".py", ".md"]:  # 本课只读两种小文本文件。
        raise ValueError("本课仅支持 .py 和 .md 文件")
    return target  # 路径检查和文件读取是两个不同动作。


def read_text_tool(root: Path, relative_path: str) -> dict[str, Any]:
    """第 2 段：读取小型 UTF-8 教学文件，错误也交还调用方。

    Args:
        root: 教学目录，范围规则由 safe_path 执行。
        relative_path: 相对文件名，文件最多 32768 字节。
    Returns:
        成功为 ok=True/path=输入名/content=正文/error=None；
        失败为 ok=False/path=输入名/content=""/error=具体原因。
    Raises:
        无：路径、大小与编码错误都转成 ok=False 的返回值。
    """
    try:
        target = safe_path(root, relative_path)
        if target.stat().st_size > 32768:
            raise ValueError("文件超过本课 32768 字节上限")
        content = target.read_text(encoding="utf-8")
    except (OSError, ValueError, UnicodeError) as error:
        return {"ok": False, "path": relative_path, "content": "", "error": str(error)}

    return {"ok": True, "path": relative_path, "content": content, "error": None}

def successful_paths(results: list[dict[str, Any]]) -> list[str]:
    """第 3 段：独立收集读取成功的文件路径。

    Args:
        results: 每项有布尔 ok 与字符串 path；允许空列表。
    Returns:
        仅成功项的路径字符串列表，保持顺序；不修改输入。
    Raises:
        KeyError: 内部记录缺少约定字段。

    思路：建立结果容器，逐个判断是否成功，保存路径，最后返回。
    """
    paths = []
    for result in results:
        if result["ok"]:
            paths.append(result["path"])
    return paths


if __name__ == "__main__":
    print("教师示范：", safe_path(Path(__file__).parent, "00_warmup.py"))
