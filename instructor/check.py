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
        if not cell.source.strip():
            continue  # 编辑器自动添加的空白格没有可执行内容，不构成教学分类缺失。
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
        if classification & {"setup", "demo"} and len(cell.source.splitlines()) > 40:
            issues.append(f"cell {index}: 教师代码超过40行，应拆成可理解的小步")
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


def enrichment_issues(catalog: dict[str, Any], data: dict[str, Any]) -> list[str]:
    """检查章节、任务原理和复盘题是否覆盖当前目录。

    Args:
        catalog: 当前课程目录。
        data: 剧情、原理和题库。
    Returns:
        缺项、无效答案或重复题目的问题列表。
    Raises:
        无；用于教材维护检查，不登记本人进度。
    """
    issues: list[str] = []
    fields = {"opening", "principle", "arc", "capability_contract", "pitfalls", "game_goal"}
    for module in catalog["modules"]:
        chapter = data.get("modules", {}).get(module["id"], {})
        for field in fields:
            if not isinstance(chapter.get(field), str) or not chapter[field].strip():
                issues.append(f"{module['id']}: 缺章节 {field}")
    seen: set[str] = set()
    for task in catalog["tasks"]:
        content = data.get("tasks", {}).get(task["id"], {})
        if not content.get("principle_markdown"):
            issues.append(f"{task['id']}: 缺原理解释")
        for index, step in enumerate(content.get("microsteps", []), 1):
            required = {"title", "explanation", "predict", "code", "observe", "student_next"}
            if any(not isinstance(step.get(key), str) or not step[key].strip() for key in required):
                issues.append(f"{task['id']}: 小步{index}缺讲授、预测、代码或本人衔接")
                continue
            try:
                compile(step["code"], task["id"], "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            except SyntaxError:
                issues.append(f"{task['id']}: 小步{index}代码语法不合法")
            if len(step["code"].splitlines()) > 40:
                issues.append(f"{task['id']}: 小步{index}教师代码超过40行")
        quiz = content.get("quiz", [])
        if len(quiz) < 2:
            issues.append(f"{task['id']}: 至少需要两张原理判断卡")
        for question in quiz:
            qid = question.get("id", "")
            if not qid.startswith(task["id"] + "-") or qid in seen:
                issues.append(f"{task['id']}: 题目编号缺失、归属错误或重复")
            seen.add(qid)
            options = question.get("options", [])
            option_ids = [option.get("id") for option in options]
            if len(options) < 3 or len(set(option_ids)) != len(options):
                issues.append(f"{qid}: 需要至少三个不同选项")
            if question.get("correct") not in option_ids:
                issues.append(f"{qid}: 正确答案不在选项中")
            if not question.get("prompt") or not question.get("concept"):
                issues.append(f"{qid}: 缺情景问题或原理标签")
            if any(not option.get("label") or not option.get("feedback") for option in options):
                issues.append(f"{qid}: 每个选项都需要内容和解析")
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
        rules = ROOT / module["directory"] / "AGENTS.md"
        alias = rules.with_name("AGENT.md")
        if not alias.is_symlink() or alias.resolve() != rules.resolve():
            issues.append(f"{module['id']}: AGENT.md 没有链接同目录规则")
    from instructor.render_curriculum import load_enrichment, render

    issues.extend(enrichment_issues(catalog, load_enrichment()))

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
