"""整理已保存的本人定义与场景素材；不运行或补写练习答案。"""

import ast
import builtins
import difflib
import hashlib
import json
import symtable
from pathlib import Path
from typing import Any

import nbformat

from instructor.check import ROOT


def load_cabinet() -> list[dict[str, str]]:
    """读取世界目录登记的资料，只提供本地实验数据。

    Args:
        无：读取本仓库的world/cabinet/catalog.json。
    Returns:
        含id、title、text的资料列表；模型不会自动收到这个列表。
    Raises:
        ValueError: 编号重复，或路径超出world目录。
        OSError: 文件读取失败。
    """
    world = (ROOT / "world").resolve()
    rows = json.loads((world / "cabinet/catalog.json").read_text(encoding="utf-8"))
    seen = set()
    documents = []
    for row in rows:
        path = (ROOT / row["path"]).resolve()
        if not path.is_relative_to(world) or row["id"] in seen:
            raise ValueError("资料目录有越界路径或重复编号")
        seen.add(row["id"])
        documents.append(
            {
                "id": row["id"],
                "title": row["title"],
                "text": path.read_text(encoding="utf-8"),
            }
        )
    return documents


def unresolved_globals(source: str) -> list[str]:
    """静态核对模块和嵌套函数依赖，不运行定义或导入。

    Args:
        source: 完整的导出Python文本，包括已展示的设施前置代码。
    Returns:
        没有在模块、局部作用域或Python内建中定义的全局名字。
    Raises:
        SyntaxError: 源码不能编译为有效Python模块。
    """
    table = symtable.symtable(source, "<learner-export>", "exec")
    available = set(dir(builtins)) | {
        "__file__", "__name__", "__package__", "__doc__", "__annotations__", "__builtins__"
    }
    available.update(
        symbol.get_name()
        for symbol in table.get_symbols()
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()
    )
    missing: set[str] = set()

    def inspect(scope: symtable.SymbolTable) -> None:
        for symbol in scope.get_symbols():
            if symbol.is_referenced() and symbol.is_global() and symbol.get_name() not in available:
                missing.add(symbol.get_name())
        for child in scope.get_children():
            inspect(child)

    inspect(table)
    return sorted(missing)


def _build_export(
    notebook: Path,
    cell_ids: list[str],
    names: list[str],
    destination: Path,
    prelude: str,
) -> tuple[Path, str, dict[str, Any]]:
    """生成待导出内容与来源，保留本人控制逻辑且不执行它。"""
    source_path = notebook.resolve()
    target = destination.resolve()
    if not source_path.is_relative_to((ROOT / "modules").resolve()):
        raise ValueError("只能从当前课程modules中的Notebook整理本人代码")
    if not target.is_relative_to((ROOT / "project").resolve()) or target.suffix != ".py":
        raise ValueError("本人定义只能整理到project中的Python文件")
    document = nbformat.read(source_path, as_version=4)
    chunks: dict[str, str] = {}
    for cell_id in cell_ids:
        matches = [c for c in document.cells if c.id == cell_id]
        if len(matches) != 1 or "exercise" not in matches[0].metadata.get("tags", []):
            raise ValueError(f"{cell_id}不是唯一的本人练习格")
        cell = matches[0]
        tree = ast.parse(cell.source)
        lines = cell.source.splitlines(keepends=True)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name not in names:
                continue
            if node.name in chunks:
                raise ValueError("同名定义重复，请先整理练习格")
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                body = body[1:]
            if not body or all(isinstance(item, ast.Pass) for item in body):
                raise ValueError("定义尚未完成，请本人编写并保存Notebook后再导出")
            for item in ast.walk(node):
                if isinstance(item, ast.Raise):
                    exc = item.exc.func if isinstance(item.exc, ast.Call) else item.exc
                    if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                        raise ValueError("练习仍有占位异常，请本人完成并保存Notebook后再导出")
            start = min([node.lineno, *[d.lineno for d in node.decorator_list]]) - 1
            chunks[node.name] = "".join(lines[start : node.end_lineno]).rstrip()
    if set(chunks) != set(names) or len(set(names)) != len(names):
        raise ValueError("缺少请求的本人定义，请保存正确的练习格")
    content = (
        '"""来自本人Notebook的定义；来源记录见同名.origin.json。"""\n\n'
        + prelude.rstrip()
        + "\n\n"
        + "\n\n".join(chunks[name] for name in names)
        + "\n"
    )
    compile(content, str(target), "exec")  # 只检查语法，不执行函数、装饰器或模型调用。
    missing = unresolved_globals(content)
    if missing:
        raise ValueError(
            "导出缺少运行依赖：" + ", ".join(missing)
            + "。请核对本页公开设施或本人定义；不会补入教师答案。"
        )
    origin = {
        "notebook": str(source_path.relative_to(ROOT)),
        "cells": cell_ids,
        "names": names,
        "sha256": hashlib.sha256(content.encode()).hexdigest(),
        "scope": "仅提取本人已保存定义；文件存在不证明独立掌握，未执行被导出的代码。",
    }
    return target, content, origin


def preview_export(
    notebook: Path,
    cell_ids: list[str],
    names: list[str],
    destination: Path,
    prelude: str,
) -> dict[str, Any]:
    """比较已保存本人定义与project，不写入文件或执行任何代码。

    Args:
        notebook: 当前课程Notebook；cell_ids: 唯一exercise格ID。
        names: 本人函数或类；destination: project内目标；prelude: 已公开的设施。
    Returns:
        new/unchanged/update/conflict状态、指纹与可阅读差异。
    Raises:
        ValueError: 定义、路径、占位或运行依赖不合法。
        OSError: 本人文件无法读取。
    """
    target, content, origin = _build_export(notebook, cell_ids, names, destination, prelude)
    current = target.read_text(encoding="utf-8") if target.exists() else None
    current_sha = hashlib.sha256(current.encode()).hexdigest() if current is not None else None
    status = "new" if current is None else "unchanged" if current == content else "conflict"
    origin_path = target.with_suffix(".origin.json")
    if status == "conflict" and origin_path.exists():
        try:
            previous = json.loads(origin_path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            previous = None
        if isinstance(previous, dict) and all(
            previous.get(key) == origin[key] for key in ("notebook", "cells", "names")
        ) and previous.get("sha256") == current_sha:
            status = "update"
    return {
        "status": status,
        "destination": str(target.relative_to(ROOT)),
        "current_sha": current_sha,
        "proposed_sha": origin["sha256"],
        "diff": "".join(difflib.unified_diff(
            (current or "").splitlines(keepends=True), content.splitlines(keepends=True),
            fromfile="project当前版本", tofile="Notebook已保存版本",
        )),
        "scope": "只比较源码；不运行、不给出题目答案，也不登记掌握。",
    }


def export_definitions(
    notebook: Path,
    cell_ids: list[str],
    names: list[str],
    destination: Path,
    prelude: str,
    *,
    expected_previous_sha: str | None = None,
) -> Path:
    """提取已保存的本人定义，检查依赖，保留版本与来源。

    Args:
        notebook: 课程Notebook；cell_ids: 本人exercise格；names: 导出定义。
        destination: project目标；prelude: 已展示的导入与设施，不含练习答案。
        expected_previous_sha: 更新时来自preview_export的当前指纹，防止比较后版本变化。
    Returns:
        实际目标路径；旧版仅在来源匹配且无独立改动时备份后更新。
    Raises:
        ValueError: 占位、定义、依赖或路径不合法。
        FileExistsError: 未预览更新、内容变化或project有独立修改，保留文件。
        OSError: 文件读取或写入失败。
    """
    target, content, origin = _build_export(notebook, cell_ids, names, destination, prelude)
    preview = preview_export(notebook, cell_ids, names, destination, prelude)
    if preview["status"] == "conflict":
        raise FileExistsError(
            "project有独立改动或来源不匹配；请查看preview_export差异并保留本人修改"
        )
    if preview["status"] == "update":
        if not expected_previous_sha or expected_previous_sha != preview["current_sha"]:
            raise FileExistsError("Notebook有修订；请先preview_export，再传入该次current_sha更新")
        backup = target.parent / ".export-history" / target.stem / expected_previous_sha
        backup.mkdir(parents=True, exist_ok=True)
        old_text = target.read_text(encoding="utf-8")
        if hashlib.sha256(old_text.encode()).hexdigest() != expected_previous_sha:
            raise FileExistsError("比较后project版本发生变化，请重新预览")
        (backup / target.name).write_text(old_text, encoding="utf-8")
        (backup / target.with_suffix(".origin.json").name).write_text(
            target.with_suffix(".origin.json").read_text(encoding="utf-8"), encoding="utf-8"
        )
        origin["previous_sha256"] = expected_previous_sha
        origin["backup"] = str(backup.relative_to(ROOT))
    if preview["status"] == "unchanged":
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    target.with_suffix(".origin.json").write_text(
        json.dumps(origin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return target
