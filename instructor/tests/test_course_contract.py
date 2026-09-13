"""验证教师校验不会把学生题目悄悄执行或填完。"""

from pathlib import Path
from typing import Any

import nbformat
import pytest

from instructor.check import LEARNING_FIELDS, QUEST_FIELDS, material_issues, notebook_issues
from instructor.render_curriculum import prompt_text
from instructor.sync_entry import current_entry
from instructor.validate_notebooks import demo_copy, validate_one


def test_demo_execution_keeps_student_source_untouched() -> None:
    source = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("print('demo')", metadata={"tags": ["demo"]}),
            nbformat.v4.new_code_cell(
                "raise NotImplementedError('本人练习')", metadata={"tags": ["exercise"]}
            ),
            nbformat.v4.new_code_cell(
                "assert student_result", metadata={"tags": ["exercise-test"]}
            ),
        ]
    )
    copied, skipped = demo_copy(source)
    assert len(skipped) == 2
    assert "skip-execution" in copied.cells[1].metadata.tags
    assert "skip-execution" not in source.cells[1].metadata.tags
    assert copied.cells[1].source == source.cells[1].source


def test_rejects_demo_disguised_as_student_cell(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("x=1", metadata={"tags": ["demo", "exercise"]}),
        ]
    )
    path = tmp_path / "bad.ipynb"
    nbformat.write(notebook, path)
    issues = notebook_issues(path)
    assert any("只能有一个" in issue for issue in issues)
    assert any("本人验收" in issue for issue in issues)


def test_accepts_top_level_await_in_teaching_cell(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("await model.ainvoke([])", metadata={"tags": ["demo"]}),
            nbformat.v4.new_code_cell("raise NotImplementedError", metadata={"tags": ["exercise"]}),
            nbformat.v4.new_code_cell("assert result", metadata={"tags": ["exercise-test"]}),
        ]
    )
    path = tmp_path / "valid.ipynb"
    nbformat.write(notebook, path)
    assert notebook_issues(path) == []


def test_planned_design_is_not_a_fake_notebook(tmp_path: Path) -> None:
    task: dict[str, Any] = {
        "id": "M04-T03",
        "status": "planned",
        "notebook": None,
        "learning": dict.fromkeys(LEARNING_FIELDS, "明确的学习内容"),
        "quest": dict.fromkeys(QUEST_FIELDS, "具体委托内容"),
        "external_prerequisites": [],
    }
    assert material_issues(task, tmp_path) == []
    # 目录允许诚实规划，但不能把规划当成可学习入口或一次成功执行。
    with pytest.raises(ValueError, match="教材已就绪"):
        current_entry(task)
    with pytest.raises(ValueError, match="尚无 Notebook"):
        validate_one(task)


def test_ready_material_cannot_point_to_missing_notebook(tmp_path: Path) -> None:
    task = {
        "id": "M04-T03",
        "status": "ready",
        "notebook": "missing.ipynb",
        "learning": dict.fromkeys(LEARNING_FIELDS, "明确的学习内容"),
        "quest": dict.fromkeys(QUEST_FIELDS, "具体委托内容"),
        "external_prerequisites": [],
    }
    assert "缺 Notebook" in material_issues(task, tmp_path)


def test_unfinished_lesson_cannot_be_promoted_to_learning_entry() -> None:
    with pytest.raises(ValueError, match="教材已就绪"):
        current_entry({"id": "M06-T01", "status": "draft", "notebook": "demo.ipynb"})


def test_scene_prompt_keeps_current_mission_and_evidence_boundary() -> None:
    result = prompt_text({"quest": {"prompt_role": "接待读者", "prompt_mission": "解释临时公告"}})
    assert "雾岛图书馆助手阿灯" in result
    assert "馆长林禾" in result and "解释临时公告" in result
    assert "没有资料或没有完成动作时" in result
