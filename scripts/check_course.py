"""检查课程任务、每日预算、规则共享和完成证据的结构。"""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = (
    "今天要做什么",
    "为什么这样做",
    "核心思想",
    "能学到什么",
    "前置条件",
    "60 分钟步骤",
    "验收标准",
    "卡住怎么办",
    "资料与边界",
)


def validate_tasks(tasks: list[dict[str, Any]], root: Path) -> list[str]:
    """检查唯一编号、顺序、预算与任务卡必需章节。

    Args:
        tasks: course.json 中按教学顺序排列的任务列表。
        root: 仓库根目录，可传测试临时目录。
    Returns:
        违规说明列表，空列表表示结构满足约定。
    Raises:
        OSError: 已存在的任务卡不可读取。
    """
    problems = []
    previous = None
    seen = set()
    for task in tasks:
        task_id = task.get("id")
        if task_id in seen:
            problems.append(f"任务重复：{task_id}")
        seen.add(task_id)
        if task.get("prerequisite") != previous:
            problems.append(f"{task_id} 前置顺序不连续")
        previous = task_id
        minutes = task.get("minutes")
        if not isinstance(minutes, int) or not 1 <= minutes <= 60:
            problems.append(f"{task_id} 每日预算须在 1～60 分钟")
        card = root / task.get("card", "missing")
        if not card.is_file():
            problems.append(f"{task_id} 缺任务卡")
            continue
        text = card.read_text(encoding="utf-8")
        for section in SECTIONS:
            if f"## {section}" not in text:
                problems.append(f"{task_id} 缺少 {section}")
    return problems


def validate_progress(state: dict[str, Any], task_ids: set[str]) -> list[str]:
    """检查完成记录是否有证据字段，不替代人的独立性判断。

    Args:
        state: 学习状态对象。
        task_ids: 课程中存在的任务编号。
    Returns:
        状态结构违规列表。
    Raises:
        无：此函数只核对已解析状态。
    """
    problems = []
    if state.get("active_task") not in task_ids:
        problems.append("当前任务不存在")
    else:
        for earlier in sorted(task_ids):
            if earlier >= state["active_task"]:
                break
            if state.get("progress", {}).get(earlier, {}).get("status") != "completed":
                problems.append(f"当前任务的前置任务 {earlier} 未完成")
    for task_id, record in state.get("progress", {}).items():
        if task_id not in task_ids:
            problems.append(f"未知任务进度：{task_id}")
        status = record.get("status")
        if status not in {"in_progress", "needs_practice", "completed"}:
            problems.append(f"{task_id} 学习状态不合法")
        if status == "completed":
            if not record.get("learner_evidence"):
                problems.append(f"{task_id} 缺本人证据")
            checks = record.get("checks", [])
            if not checks or any(check.get("passed") is not True for check in checks):
                problems.append(f"{task_id} 缺成功验收证据")
    return problems


def validate_alias(directory: Path) -> list[str]:
    """确保两种 harness 规则入口共享同一文本。

    Args:
        directory: 含 AGENTS.md 的目录。
    Returns:
        链接问题列表。
    Raises:
        OSError: 文件系统无法读取链接。
    """
    alias = directory / "CLAUDE.md"
    canonical = directory / "AGENTS.md"
    if not alias.is_symlink() or not alias.exists() or alias.resolve() != canonical.resolve():
        return [f"{directory}: CLAUDE.md 必须链接同目录 AGENTS.md"]
    return []


def main() -> int:
    try:
        course = json.loads((ROOT / "curriculum/course.json").read_text(encoding="utf-8"))
        state = json.loads((ROOT / "COURSE_STATE.json").read_text(encoding="utf-8"))
        tasks = course["tasks"]
        problems = validate_tasks(tasks, ROOT)
        if len(tasks) != course["total_sessions"]:
            problems.append("任务数与课程总数不符")
        problems.extend(validate_progress(state, {task["id"] for task in tasks}))
        for rules in ROOT.rglob("AGENTS.md"):
            if any(part.startswith(".") for part in rules.relative_to(ROOT).parts):
                continue
            problems.extend(validate_alias(rules.parent))
        for problem in problems:
            print("✗", problem)
        if problems:
            return 1
        print(f"✓ {len(tasks)} 张任务卡、每日预算、规则共享与进度结构")
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"课程检查失败：{error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
