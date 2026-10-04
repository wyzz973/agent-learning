"""检查Notebook教师代码，明确区分本人写法与重复教学导入。"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import nbformat

from instructor.check import ROOT


def _import_at(source: str, row: int) -> dict[str, tuple[str, str]]:
    """取得诊断所在导入的名字与准确来源，避免忽略不同来源的覆盖。"""
    result = {}
    for node in ast.parse(source).body:
        if not node.lineno <= row <= (node.end_lineno or node.lineno):
            continue
        if isinstance(node, ast.ImportFrom):
            result.update({alias.asname or alias.name: (node.module or "", alias.name)
                           for alias in node.names})
        if isinstance(node, ast.Import):
            result.update({alias.asname or alias.name.split(".")[0]: (alias.name, "")
                           for alias in node.names})
    return result


def classify_diagnostics(diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    """按实际cell标签分类，不把学生长签名或独立修改当教师检查失败。

    Args:
        diagnostics: Ruff JSON结果，cell序号为一基。
    Returns:
        教师待修项、仅同来源重复导入的解释项与本人诊断数。
    Raises:
        ValueError: 诊断不能定位；OSError: Notebook无法读取。
    """
    cache: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    explained: list[dict[str, Any]] = []
    learner: list[dict[str, Any]] = []
    for diagnostic in diagnostics:
        filename = diagnostic["filename"]
        if diagnostic.get("cell") is None:
            errors.append({"cell_id": "Python设施文件", **diagnostic})
            continue
        if filename not in cache:
            cache[filename] = nbformat.read(filename, as_version=4)
        notebook = cache[filename]
        cell = notebook.cells[diagnostic["cell"] - 1]
        tags = set(cell.metadata.get("tags", []))
        entry = {"file": filename, "cell_id": cell.id, **diagnostic}
        if not tags & {"setup", "demo"}:
            learner.append(entry)
            continue
        match = re.search(r"from cell (\d+), line (\d+)", diagnostic["message"])
        symbol = re.search(r"`([^`]+)`", diagnostic["message"])
        if diagnostic["code"] == "F811" and match and symbol:
            earlier = notebook.cells[int(match[1]) - 1]
            previous = _import_at(earlier.source, int(match[2]))
            current = _import_at(cell.source, diagnostic["location"]["row"])
            name = symbol[1]
            if name in current and previous.get(name) == current[name]:
                explained.append({
                    **entry,
                    "reason": "同来源导入在独立教学格重复；未覆盖不同对象，保留原位可读性。"
                })
                continue
        errors.append(entry)
    return {"teacher_errors": errors, "explained_imports": explained,
            "learner_diagnostics": learner,
            "scope": "仅setup/demo为教师门禁；本人及exercise-test不由样式成绩推断掌握。"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    process = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(ROOT / "modules"), "--output-format", "json"],
        capture_output=True, text=True, timeout=60,
    )
    if process.returncode not in {0, 1}:
        raise RuntimeError("Ruff未产生可用诊断，请核对环境")
    report = classify_diagnostics(json.loads(process.stdout))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    counts = {
        "teacher_errors": len(report["teacher_errors"]),
        "explained_imports": len(report["explained_imports"]),
        "learner_diagnostics": len(report["learner_diagnostics"]),
    }
    print(json.dumps(counts, ensure_ascii=False))
    for error in report["teacher_errors"]:
        print(error["file"], error["cell_id"], error["code"], error["message"])
    return int(bool(report["teacher_errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
