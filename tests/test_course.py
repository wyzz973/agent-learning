"""课程结构应能拒绝超时计划、漂移规则与无证据完成。"""

from pathlib import Path

from check_course import SECTIONS, validate_alias, validate_progress, validate_tasks
from learn import handoff_text


def test_tasks_reject_missing_sections_and_excess_budget(tmp_path: Path) -> None:
    (tmp_path / "task.md").write_text("# 只有标题", encoding="utf-8")
    issues = validate_tasks(
        [{"id": "D01", "minutes": 90, "prerequisite": None, "card": "task.md"}], tmp_path
    )
    assert any("预算" in issue for issue in issues)
    assert any("核心思想" in issue for issue in issues)


def test_tasks_accept_complete_card(tmp_path: Path) -> None:
    (tmp_path / "task.md").write_text("\n".join("## " + item for item in SECTIONS))
    assert (
        validate_tasks(
            [{"id": "D01", "minutes": 60, "prerequisite": None, "card": "task.md"}], tmp_path
        )
        == []
    )


def test_completed_requires_learner_and_check_evidence() -> None:
    issues = validate_progress(
        {"active_task": "D01", "progress": {"D01": {"status": "completed"}}}, {"D01"}
    )
    assert any("本人证据" in issue for issue in issues)
    assert any("验收证据" in issue for issue in issues)


def test_active_task_cannot_skip_unfinished_prerequisite() -> None:
    issues = validate_progress({"active_task": "D02", "progress": {}}, {"D01", "D02"})
    assert any("前置任务 D01 未完成" in issue for issue in issues)


def test_alias_rejects_divergent_copy(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("共同规则")
    (tmp_path / "CLAUDE.md").write_text("另一套规则")
    assert validate_alias(tmp_path)
    (tmp_path / "CLAUDE.md").unlink()
    (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")
    assert validate_alias(tmp_path) == []


def test_handoff_does_not_invent_learner_progress(tmp_path: Path) -> None:
    task = {
        "id": "D01",
        "title": "开始",
        "week": "w04",
        "card": "task.md",
        "target": "ex.py",
        "material_status": "scaffold_ready",
    }
    state = {"progress": {}, "next_action": "先预测输出"}
    text = handoff_text(tmp_path, task, state)
    assert "not_started" in text
    assert "本人证据：[]" in text
    assert state["progress"] == {}
