"""验证当前 module/task 课程，绝不执行或补写学习者答案。"""

import ast
import json
from pathlib import Path
from typing import Any

import nbformat

ROOT = Path(__file__).resolve().parent.parent
KINDS = {"setup", "demo", "exercise", "exercise-test"}
MATERIAL_STATUSES = {"ready", "draft", "planned"}
LEARNING_FIELDS = {
    "mechanism",
    "python",
    "framework",
    "frontier",
    "references",
}
QUEST_FIELDS = {
    "id",
    "title",
    "zone",
    "commission",
    "obstacle",
    "starting_kit",
    "player_action",
    "reward",
    "acceptance",
    "replay",
    "transfer",
    "next_hook",
    "choice",
    "prompt_role",
    "prompt_mission",
}


def notebook_issues(path: Path) -> list[str]:
    """检查 Notebook 格式、代码标签、语法与练习存在性。

    Args:
        path: 当前课程 Notebook 的路径。
    Returns:
        问题列表；不判断本人是否独立掌握。
    Raises:
        OSError: 文件不可读。
        ValueError: Notebook 格式不合法。
    """
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    issues: list[str] = []
    kinds: set[str] = set()
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        tags = set(cell.metadata.get("tags", []))
        classification = tags & KINDS
        if len(classification) != 1:
            issues.append(f"cell {index}: 必须且只能有一个执行分类标签")
        kinds.update(classification)
        try:
            compile(
                cell.source, str(path) + f":cell{index}", "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
            )
        except SyntaxError as error:
            issues.append(f"cell {index}: {error.msg}")
        if len(cell.source.splitlines()) > 40:
            issues.append(f"cell {index}: 代码超过 40 行，应拆成可理解的小步")
    if not {"demo", "exercise", "exercise-test"} <= kinds:
        issues.append("必须包含独立的示范、本人练习与本人验收")
    return issues


def load_catalog(root: Path = ROOT) -> dict[str, Any]:
    """读取唯一的课程目录。

    Args:
        root: 仓库根目录，可用于测试临时目录。
    Returns:
        课程目录对象。
    Raises:
        OSError: 文件不可读。
        ValueError: JSON 不是对象。
    """
    data: Any = json.loads((root / "instructor/catalog.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("课程目录必须为对象")
    return dict(data)


def material_issues(task: dict[str, Any], root: Path = ROOT) -> list[str]:
    """检查任务情景、教学契约与实际教材状态。

    Args:
        task: 目录中的任务，含情景、学习内容与材料状态。
        root: 仓库根目录或测试目录。
    Returns:
        材料状态、情景契约和 Notebook 的问题。
    Raises:
        OSError: 已有 Notebook 无法读取。
    """
    issues = []
    status = task.get("status")
    if status not in MATERIAL_STATUSES:
        issues.append("未知材料状态")
    for group, fields in [("learning", LEARNING_FIELDS), ("quest", QUEST_FIELDS)]:
        for field in sorted(fields):
            if not task.get(group, {}).get(field):
                issues.append(f"{group}缺 {field}")
    if task.get("external_prerequisites") != []:
        issues.append("本课程不设外部学习前置；必要写法须在本关提供")
    notebook = task.get("notebook")
    if status == "planned":
        if notebook is not None:
            issues.append("planned任务还没有Notebook；开始编写后标draft，验证完整后标ready")
        return issues
    if not isinstance(notebook, str) or not notebook:
        issues.append("现有教材状态必须提供真实 Notebook")
        return issues
    path = root / notebook
    if not path.is_file():
        issues.append("缺 Notebook")
        return issues
    issues.extend(notebook_issues(path))
    document = nbformat.read(path, as_version=4)
    if document.metadata.get("agent_learning", {}).get("task_id") != task["id"]:
        issues.append("Notebook 标识与目录不一致")
    if document.metadata.get("agent_learning", {}).get("campaign_id") != "fog-island-library":
        issues.append("Notebook缺雾岛情景标识")
    return issues


def main() -> int:
    catalog = load_catalog()
    state = json.loads((ROOT / "instructor/state.json").read_text(encoding="utf-8"))
    issues: list[str] = []
    ids = []
    for task in catalog["tasks"]:
        ids.append(task["id"])
        issues.extend(f"{task['id']}: {item}" for item in material_issues(task))
        if task.get("requires"):
            issues.append(f"{task['id']}: 不设课程外任务门槛，按情景顺序原位教学")
    if len(set(ids)) != len(ids):
        issues.append("任务 ID 重复")
    if state["active_task"] not in ids:
        issues.append("当前任务不在目录中")
    else:
        from instructor.sync_entry import current_entry

        active = next(t for t in catalog["tasks"] if t["id"] == state["active_task"])
        if active["status"] != "ready":
            issues.append("当前任务教材尚未就绪；导师必须先完成教学材料，不让本人找不存在的课")
        elif current_entry(active) not in (ROOT / "README.md").read_text(encoding="utf-8"):
            issues.append("README 当前入口与学习状态不一致，请运行 instructor.sync_entry")
    for task_id, progress in state.get("progress", {}).items():
        if task_id not in ids:
            issues.append(f"未知进度：{task_id}")
        if progress.get("status") == "completed" and (
            not progress.get("learner_evidence") or not progress.get("checks")
        ):
            issues.append(f"{task_id}: 完成记录缺本人证据或验收")
    for rules in [
        ROOT / "AGENTS.md",
        ROOT / "world/AGENTS.md",
        ROOT / "project/AGENTS.md",
        *ROOT.glob("modules/*/AGENTS.md"),
    ]:
        alias = rules.with_name("CLAUDE.md")
        if not alias.is_symlink() or alias.resolve() != rules.resolve():
            issues.append(f"{rules.parent}: CLAUDE.md 没有链接同目录规则")
    for module in catalog["modules"]:
        if not (ROOT / module["directory"] / "README.md").is_file():
            issues.append(f"{module['id']}: 缺专题索引")
    from instructor.render_curriculum import render

    for path in render(check=True):
        issues.append(f"地图或prompt过期：{path}，运行 instructor.render_curriculum 同步")
    for issue in issues:
        print("✗", issue)
    if issues:
        return 1
    counts = {s: sum(t["status"] == s for t in catalog["tasks"]) for s in MATERIAL_STATUSES}
    print(f"✓ 雾岛{len(catalog['modules'])}个区域 / {len(ids)}项委托，情景、prompt与入口一致")
    print(
        f"材料：{counts['ready']} 关可开始 / {counts['draft']} 关编写中 / "
        f"{counts['planned']} 个待编写任务；不代表本人完成"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
