"""保存学习尝试与帮助程度；不替学生判断掌握，也不写完成状态。"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import nbformat

HELP_LEVELS = {
    "independent",
    "concept_hint",
    "microstep_hint",
    "local_code_hint",
    "teacher_takeover",
}


def record_attempt(
    root: Path,
    task_id: str,
    notebook: Path,
    cell_ids: list[str],
    artifact: Path,
    *,
    signal: str,
    help_level: str,
    origin: str = "learner",
    outcome: str = "unverified",
) -> dict[str, Any]:
    """为已保存实现和实际产物建立独立尝试记录。

    Args:
        root/task_id: 课程与任务；notebook/cell_ids: 本人来源；artifact: outputs内实际文件。
        signal: program/choice/transfer/design；help_level: 明确帮助程度。
        origin: learner或teacher；outcome: 本次passed/failed/incomplete/unverified。
    Returns:
        带源与产物指纹的记录；记录通过不代表掌握或课程通关。
    Raises:
        ValueError: 非法范围、信号、帮助程度、来源或身份；OSError: 文件未保存。
    """
    root = root.resolve()
    notebook, artifact = notebook.resolve(), artifact.resolve()
    catalog = json.loads((root / "instructor/catalog.json").read_text(encoding="utf-8"))
    task = next((t for t in catalog["tasks"] if t["id"] == task_id), None)
    if task is None or notebook != (root / task["notebook"]).resolve():
        raise ValueError("来源必须是本任务的实际Notebook")
    if not artifact.is_relative_to(root / "outputs") or not artifact.is_file():
        raise ValueError("产物必须是outputs内实际存在的文件")
    if help_level not in HELP_LEVELS or signal not in {"program", "choice", "transfer", "design"}:
        raise ValueError("帮助程度或信号未登记")
    if origin not in {"learner", "teacher"} or outcome not in {
        "passed",
        "failed",
        "incomplete",
        "unverified",
    }:
        raise ValueError("来源或尝试状态不合法")
    document = nbformat.read(notebook, as_version=4)
    cells = {cell.id: cell for cell in document.cells}
    if not cell_ids or len(cell_ids) != len(set(cell_ids)) or any(c not in cells for c in cell_ids):
        raise ValueError("来源格必须存在且不能重复")
    if origin == "learner" and signal != "choice":
        if any("exercise" not in cells[c].metadata.get("tags", []) for c in cell_ids):
            raise ValueError("本人实现证据必须引用exercise格，不能引用教师答案")
        if artifact.name.startswith("teacher") or artifact.is_relative_to(
            root / "outputs/validation"
        ):
            raise ValueError("教师演示不能登记成本人产物")
    record: dict[str, Any] = {
        "id": uuid.uuid4().hex,
        "task": task_id,
        "signal": signal,
        "origin": origin,
        "outcome": outcome,
        "help_level": help_level,
        "independent_work_claim": origin == "learner" and help_level == "independent",
        "scope": "仅本次已保存尝试；来源自述，尚需导师按运行、原理与迁移分别复核。",
        "recorded_at": datetime.now(UTC).isoformat(),
        "notebook": str(notebook.relative_to(root)),
        "cells": {c: hashlib.sha256(cells[c].source.encode()).hexdigest() for c in cell_ids},
        "artifact": str(artifact.relative_to(root)),
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "mastery": "not_inferred",
    }
    folder = root / "outputs/learning-evidence" / task_id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (record["id"] + ".json")
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def inspect_attempt(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """重新核对已记录内容身份，发现修改后不沿用旧通过。

    Args:
        root: 当前仓库；record: 实际尝试记录。
    Returns:
        current_content_matches、缺失/改变项与独立程度，始终不推断掌握。
    Raises:
        ValueError: 记录路径越界；文件或Notebook错误原样保留。
    """
    root = root.resolve()
    notebook = (root / record["notebook"]).resolve()
    artifact = (root / record["artifact"]).resolve()
    if not notebook.is_relative_to(root / "modules") or not artifact.is_relative_to(
        root / "outputs"
    ):
        raise ValueError("证据路径越界")
    cells = {c.id: c for c in nbformat.read(notebook, as_version=4).cells}
    changed = [
        cid
        for cid, sha in record["cells"].items()
        if cid not in cells or hashlib.sha256(cells[cid].source.encode()).hexdigest() != sha
    ]
    if (
        not artifact.exists()
        or hashlib.sha256(artifact.read_bytes()).hexdigest() != record["artifact_sha256"]
    ):
        changed.append("artifact")
    return {
        "current_content_matches": not changed,
        "changed": changed,
        "help_level": record["help_level"],
        "origin": record["origin"],
        "mastery": "not_inferred",
    }


def show_attempt_recorder(
    root: Path,
    task_id: str,
    notebook: Path,
    cell_ids: list[str],
) -> Any:
    """显示统一尝试记录卡，用户明确选择帮助程度与实际产物。

    Args:
        root/task_id/notebook/cell_ids: 当前本人来源，不包含教师实现。
    Returns:
        可选的记录卡；不预选独立程度、不自动修改进度。
    Raises:
        环境缺少widgets时原样报出；提交错误只显示公开类别和下一步。
    """
    import ipywidgets as widgets
    from IPython.display import display

    help_choice = widgets.Dropdown(
        options=[
            ("请选择帮助程度", ""),
            ("独立完成", "independent"),
            ("概念提示", "concept_hint"),
            ("小步提示", "microstep_hint"),
            ("局部代码提示", "local_code_hint"),
            ("教师接管核心", "teacher_takeover"),
        ],
        description="帮助",
    )
    signal = widgets.Dropdown(
        options=[
            ("请选择证据", ""),
            ("程序运行", "program"),
            ("陌生输入迁移", "transfer"),
            ("设计取舍", "design"),
        ],
        description="证据",
    )
    artifact = widgets.Text(description="实际产物", placeholder="outputs/当前任务/实际文件.json")
    button, feedback = widgets.Button(description="保存尝试依据"), widgets.HTML()

    def submit(_: Any) -> None:
        if not help_choice.value or not signal.value:
            feedback.value = "请先选择本次帮助程度与证据类型。"
            return
        try:
            record = record_attempt(
                root,
                task_id,
                notebook,
                cell_ids,
                root / artifact.value,
                signal=signal.value,
                help_level=help_choice.value,
            )
        except (ValueError, OSError) as error:
            feedback.value = "记录未保存（" + type(error).__name__ + "）；核对当前来源与实际文件。"
        else:
            feedback.value = "本次依据已保存，待复核；没有自动登记掌握。记录号：" + record["id"]

    button.on_click(submit)
    card = widgets.VBox(
        [
            widgets.HTML("<h4>保存本次尝试与帮助程度</h4>"),
            help_choice,
            signal,
            artifact,
            button,
            feedback,
        ]
    )
    card.add_class("fog-quiz-card")
    cast(Any, display)(card)
    return card
