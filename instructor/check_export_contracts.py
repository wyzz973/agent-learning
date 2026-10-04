"""静态核对公开导出设施和练习声明；不执行或补写本人实现。"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import nbformat

from instructor.check import ROOT, load_catalog
from instructor.learner_exports import unresolved_globals


class NotStatic(ValueError):
    """表达式需要运行时数据，不能在静态检查中执行。"""


def _literal(node: ast.AST, bindings: dict[str, Any]) -> Any:
    """只解释字面量、路径组合与已知文字，不执行Notebook函数。"""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in bindings:
        return bindings[node.id]
    if isinstance(node, ast.List):
        return [_literal(item, bindings) for item in node.elts]
    if isinstance(node, ast.BinOp):
        left, right = _literal(node.left, bindings), _literal(node.right, bindings)
        if isinstance(node.op, ast.Add) and isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(node.op, ast.Div) and isinstance(left, Path) and isinstance(right, str):
            return left / right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1:
        if node.func.id == "str":
            return str(_literal(node.args[0], bindings))
        if node.func.id == "repr":
            return repr(_literal(node.args[0], bindings))
    raise NotStatic("需要动态运行的表达式，不在静态检查中执行")


def audit_notebook(path: Path, root: Path = ROOT) -> list[dict[str, Any]]:
    """核对导出声明与可静态读取的设施，区分未完成与未知。

    Args:
        path: 当前课程Notebook；root: 当前仓库或测试根。
    Returns:
        每个导出的依赖、占位状态与范围；不证明运行正确或本人掌握。
    Raises:
        SyntaxError: 当前代码不能解析；OSError: 文件无法读取。
    """
    notebook = nbformat.read(path, as_version=4)
    cells = {cell.id: cell for cell in notebook.cells}
    bindings: dict[str, Any] = {"ROOT": root}
    records: list[dict[str, Any]] = []
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        tree = ast.parse(cell.source)
        for node in tree.body:
            try:
                if isinstance(node, ast.Assign):
                    value = _literal(node.value, bindings)
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            bindings[target.id] = value
                if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                    if isinstance(node.op, ast.Add):
                        bindings[node.target.id] += _literal(node.value, bindings)
            except (NotStatic, KeyError):
                pass  # 未静态得到的值保留未知，后面的对应导出明确报告。
            for call in ast.walk(node):
                if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
                    continue
                if call.func.id != "export_definitions":
                    continue
                try:
                    arguments = {
                        name: _literal(value, bindings)
                        for name, value in zip(
                            ["notebook", "cell_ids", "names", "destination", "prelude"],
                            call.args, strict=False,
                        )
                    }
                    arguments.update({
                        keyword.arg: _literal(keyword.value, bindings)
                        for keyword in call.keywords
                        if keyword.arg in {
                            "notebook", "cell_ids", "names", "destination", "prelude"
                        }
                    })
                    requested_ids, names = arguments["cell_ids"], arguments["names"]
                    definitions = []
                    found: set[str] = set()
                    placeholder = False
                    for cell_id in requested_ids:
                        selected = cells[cell_id]
                        if "exercise" not in selected.metadata.get("tags", []):
                            raise ValueError("导出只能引用本人exercise格")
                        for definition in ast.parse(selected.source).body:
                            if isinstance(
                                definition, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                            ):
                                if definition.name in names:
                                    if definition.name in found:
                                        raise ValueError("导出定义同名重复")
                                    found.add(definition.name)
                                    text = ast.get_source_segment(selected.source, definition)
                                    definitions.append(str(text))
                                    placeholder |= "NotImplementedError" in str(text)
                    if found != set(names):
                        raise ValueError("导出声明缺少请求的本人定义")
                    combined = arguments["prelude"] + "\n\n" + "\n\n".join(definitions)
                    missing = unresolved_globals(combined)
                    records.append({
                        "cell": cell.id, "names": names, "missing_globals": missing,
                        "status": "missing_dependency" if missing else "scaffold_checked",
                        "learner_implementation_pending": placeholder,
                        "scope": "静态名字闭包；未执行导入、函数、装饰器或模型，不证明逻辑正确。",
                    })
                except (NotStatic, KeyError) as error:
                    records.append({
                        "cell": cell.id, "status": "manual_review_required",
                        "reason": type(error).__name__, "scope": "动态设施未静态核实，未执行。",
                    })
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records: list[dict[str, Any]] = []
    for task in load_catalog()["tasks"]:
        if task.get("notebook"):
            records.extend(
                {"task": task["id"], **row}
                for row in audit_notebook(ROOT / task["notebook"])
            )
    result = {"records": records, "scope": "导出设施静态检查；本人运行与新进程验收另做"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    counts = {key: sum(row["status"] == key for row in records) for key in (
        "scaffold_checked", "missing_dependency", "manual_review_required",
    )}
    print(json.dumps(counts, ensure_ascii=False))
    for record in records:
        if record["status"] != "scaffold_checked":
            print(json.dumps(record, ensure_ascii=False))
    return int(bool(counts["missing_dependency"] or counts["manual_review_required"]))


if __name__ == "__main__":
    raise SystemExit(main())
