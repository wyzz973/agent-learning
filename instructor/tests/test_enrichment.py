"""确保教材补充不覆盖本人代码，题目失配能够被维护检查发现。"""

import copy
import json
from pathlib import Path
from typing import Any

import nbformat
import pytest

from instructor import render_curriculum
from instructor.check import enrichment_issues, load_catalog


def test_detects_feedback_and_answer_drift() -> None:
    catalog = load_catalog()
    data = copy.deepcopy(render_curriculum.load_enrichment())
    assert enrichment_issues(catalog, data) == []
    question = data["tasks"]["M01-T01"]["quiz"][0]
    question["correct"] = "missing"
    question["options"][1]["feedback"] = ""
    issues = enrichment_issues(catalog, data)
    assert any("正确答案不在选项中" in issue for issue in issues)
    assert any("每个选项都需要内容和解析" in issue for issue in issues)


def test_microsteps_require_runnable_observations_and_student_handoff() -> None:
    catalog = load_catalog()
    data = copy.deepcopy(render_curriculum.load_enrichment())
    step = data["tasks"]["M09-T02"]["microsteps"][0]
    step["code"] = "unclosed = '"
    assert any("小步1代码语法" in issue for issue in enrichment_issues(catalog, data))
    step["student_next"] = ""
    assert any("本人衔接" in issue for issue in enrichment_issues(catalog, data))


def test_export_preview_is_idempotent_and_preserves_non_export_code() -> None:
    from instructor.authoring_contracts import with_export_preview

    source = (
        "# 接线说明保留\n"
        "saved = export_definitions(notebook, ['mine'], ['label'], target, prelude)\n"
        "print('这是公开回执', saved)\n"
    )
    actual = with_export_preview(source)
    assert "expected_previous_sha=export_preview_1['current_sha']" in actual
    assert "# 接线说明保留" in actual and "print('这是公开回执', saved)" in actual
    assert with_export_preview(actual) == actual


def test_render_keeps_saved_learner_cell_and_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalog = copy.deepcopy(load_catalog())
    catalog["modules"] = catalog["modules"][:1]
    catalog["tasks"] = catalog["tasks"][:1]
    enrichment = render_curriculum.load_enrichment()
    (tmp_path / "instructor").mkdir()
    (tmp_path / "instructor/course_enrichment.json").write_text(
        json.dumps(enrichment), encoding="utf-8"
    )
    (tmp_path / "README.md").write_text(
        "<!-- evolution-map:start -->\n<!-- evolution-map:end -->", encoding="utf-8"
    )
    path = tmp_path / catalog["tasks"][0]["notebook"]
    path.parent.mkdir(parents=True)
    cell: Any = nbformat.v4.new_code_cell(
        'my_greeting = "我的原始实现"', id="learner-original",
        metadata={"tags": ["exercise"]}, execution_count=7,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="我的已保存结果\n")],
    )
    supplied = [
        nbformat.v4.new_code_cell(source, id=cell_id, metadata={"tags": ["demo"]})
        for cell_id, source in enrichment["tasks"]["M01-T01"].get("code_overrides", {}).items()
    ]
    nbformat.write(nbformat.v4.new_notebook(cells=[*supplied, cell]), path)
    monkeypatch.setattr(render_curriculum, "ROOT", tmp_path)
    monkeypatch.setattr(render_curriculum, "load_catalog", lambda: catalog)
    render_curriculum.render()
    actual = nbformat.read(path, as_version=4)
    assert next(c for c in actual.cells if c.id == "learner-original") == cell
    assert any(c.id == "course-principles" for c in actual.cells)
    assert any(c.id == "course-choice-widget" for c in actual.cells)
    assert render_curriculum.render(check=True) == []
