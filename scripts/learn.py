"""读取当日任务并生成跨模型交接提示，不自动修改学习进度。"""

import argparse
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent


def read_object(path: Path) -> dict[str, Any]:
    """读取 JSON 对象。

    Args:
        path: 已知课程配置文件路径。
    Returns:
        顶层对象。
    Raises:
        ValueError: JSON 顶层不是对象或内容无法解析。
        OSError: 文件不可读取。
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} 顶层必须是对象")
    return cast(dict[str, Any], value)


def handoff_text(root: Path, task: dict[str, Any], state: dict[str, Any]) -> str:
    """生成仅含已知状态的可携带提示。

    Args:
        root: 仓库根目录。
        task: 已找到的课程任务对象。
        state: 实际学习状态，不由此函数修改。
    Returns:
        中文交接文本；缺少证据明确表示未知。
    Raises:
        KeyError: 配置缺少必要字段。
    """
    progress = state.get("progress", {}).get(task["id"], {})
    return (
        f"仓库：{root}\n"
        "请先读根 AGENTS.md、HARNESS_GUIDE.md、COURSE_STATE.json，再读目标目录规则。\n"
        f"当前任务：{task['id']} · {task['title']}\n"
        f"任务卡：{task['card']}\n"
        f"本次动作位置：{task['target']}\n"
        f"材料状态：{state.get('materials', {}).get(task['week'], task['material_status'])}\n"
        f"学习状态：{progress.get('status', 'not_started')}\n"
        f"本人证据：{json.dumps(progress.get('learner_evidence', []), ensure_ascii=False)}\n"
        f"实际检查：{json.dumps(progress.get('checks', []), ensure_ascii=False)}\n"
        f"卡点：{state.get('blocker') or '尚未记录'}\n"
        f"下一步：{state['next_action']}\n"
        "请从一个输入/输出小问题开始，中文解释；保留 TODO 和独立题给本人完成。\n"
        "不要把教师示范或脚本回放标成本人掌握；结束前按真实证据更新状态与逐字问答。"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", help="只读指定任务，例如 D01；不会推进状态")
    parser.add_argument("--handoff", action="store_true", help="输出给下一个模型的提示")
    args = parser.parse_args()
    try:
        course = read_object(ROOT / "curriculum/course.json")
        state = read_object(ROOT / "COURSE_STATE.json")
        if args.handoff and args.task and args.task != state["active_task"]:
            parser.error("--handoff 只交接实际当前任务；--task 可单独预览其他课程")
        task_id = args.task or state["active_task"]
        matches = [task for task in course["tasks"] if task["id"] == task_id]
        if not matches:
            parser.error(f"未知任务 {task_id}，请使用 D01～D60")
        task = matches[0]
        if args.handoff:
            print(handoff_text(ROOT, task, state))
        else:
            print((ROOT / task["card"]).read_text(encoding="utf-8"))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"课程入口读取失败：{error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
