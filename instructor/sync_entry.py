"""根据唯一进度刷新 README 的当前任务链接，避免多入口漂移。"""

import json
import re
from typing import Any

from instructor.check import ROOT, load_catalog


def current_entry(task: dict[str, Any]) -> str:
    """生成当前 Notebook 的单一入口。

    Args:
        task: 包含 id/title/notebook 的目录对象。
    Returns:
        带受管理标记的 Markdown 块。
    Raises:
        KeyError: 目录缺字段。
        ValueError: 完整教材尚未就绪。
    """
    if task.get("status") != "ready" or not task.get("notebook"):
        raise ValueError("只允许把完整教材已就绪的任务设为学习入口")
    return (
        "<!-- current-task:start -->\n"
        f"### [{task['id']} · {task['title']}]({task['notebook']})\n"
        "<!-- current-task:end -->"
    )


def main() -> int:
    state = json.loads((ROOT / "instructor/state.json").read_text())
    task = next(t for t in load_catalog()["tasks"] if t["id"] == state["active_task"])
    path = ROOT / "README.md"
    text, count = re.subn(
        r"<!-- current-task:start -->.*?<!-- current-task:end -->",
        lambda _: current_entry(task),
        path.read_text(encoding="utf-8"),
        flags=re.DOTALL,
    )
    if count != 1:
        raise ValueError("README 必须有且只有一个当前任务区块")
    path.write_text(text, encoding="utf-8")
    print("当前入口：", task["id"], task["notebook"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
