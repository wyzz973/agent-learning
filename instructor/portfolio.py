"""检查作品证明链和业务测量，评分不等于求职录用或本人通关。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def inspect_portfolio(root: Path, packet: dict[str, Any]) -> dict[str, Any]:
    """核对学生作品当前版本、来源和真实验收记录，不打包秘密。

    Args:
        root: 当前课程；packet: 文件指纹、本人origin、验收、演示与交接位置。
    Returns:
        ready_for_review或incomplete与具体缺口；没有自动录用、发布或学习完成。
    Raises:
        ValueError: 越界、私密路径或无效结构；OSError: 可读性问题。
    """
    root = root.resolve()
    issues: list[str] = []
    files = packet.get("files", [])
    if not files or not isinstance(files, list):
        raise ValueError("作品需要明确文件列表")
    identities: dict[str, str] = {}
    for row in files:
        relative = row["path"]
        path = (root / relative).resolve()
        if (
            not path.is_relative_to(root)
            or path.name.startswith(".env")
            or any(word in path.name.lower() for word in ("secret", "token", "credential"))
        ):
            raise ValueError("作品路径越界或包含秘密文件")
        if relative in identities:
            raise ValueError("作品文件重复")
        if not path.is_file():
            issues.append("缺文件：" + relative)
            continue
        current = hashlib.sha256(path.read_bytes()).hexdigest()
        identities[relative] = current
        if current != row.get("sha256"):
            issues.append("版本变化：" + relative)
        if relative.startswith("project/") and path.suffix == ".py":
            origin = path.with_suffix(".origin.json")
            if not origin.is_file():
                issues.append("缺本人来源：" + relative)
            elif json.loads(origin.read_text()).get("sha256") != current:
                issues.append("本人来源需重新核对：" + relative)
    for field in ("acceptance", "demo", "runbook", "failure_case"):
        relative = packet.get(field)
        if not relative:
            issues.append("缺交付依据：" + field)
            continue
        target = (root / relative).resolve()
        if target.name.startswith(".env") or any(
            word in target.name.lower() for word in ("secret", "token", "credential")
        ):
            raise ValueError("交付依据不能引用秘密文件")
        if not target.is_relative_to(root) or not target.is_file():
            issues.append("交付依据不存在：" + field)
    checks = packet.get("checks", [])
    if not checks:
        issues.append("尚无实际验收")
    for check in checks:
        if not check.get("passed") or identities.get(check.get("path")) != check.get("sha256"):
            issues.append("验收失败或对应旧版本：" + str(check.get("path")))
    for relative, sha in identities.items():
        if not any(
            check.get("path") == relative
            and check.get("sha256") == sha
            and check.get("passed") is True
            for check in checks
        ):
            issues.append("当前文件缺匹配检查：" + relative)
    return {
        "status": "incomplete" if issues else "ready_for_review",
        "issues": issues,
        "scope": "当前文件与证明链核对；设计、效果和本人独立能力需另行复核。",
    }


def summarize_workflow_trial(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """汇总实际人工/助手处理时间与质量，不用虚构价格推算收益。

    Args:
        rows: matched任务的before_seconds/after_seconds/quality_ok/critical_failure记录。
    Returns:
        已测时间差、质量、关键失败与缺测；没有测量时不编收益。
    Raises:
        ValueError: 空记录、负时间或无效类型。
    """
    if not rows:
        raise ValueError("业务比较需要实际样本")
    measured = []
    for row in rows:
        before, after = row.get("before_seconds"), row.get("after_seconds")
        if before is None or after is None:
            continue
        if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
            raise ValueError("处理时间必须是实际数值")
        if before < 0 or after < 0:
            raise ValueError("处理时间不能为负")
        measured.append(before - after)
    return {
        "tasks": len(rows),
        "measured_pairs": len(measured),
        "unmeasured_pairs": len(rows) - len(measured),
        "mean_seconds_saved": sum(measured) / len(measured) if measured else None,
        "quality_passed": sum(row.get("quality_ok") is True for row in rows),
        "critical_failures": sum(row.get("critical_failure") is True for row in rows),
        "release_allowed": all(
            row.get("quality_ok") is True and row.get("critical_failure") is False for row in rows
        ),
        "scope": "当前实际任务对照；没有价格、总体成本或录用率的保证。",
    }
