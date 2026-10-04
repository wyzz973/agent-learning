"""验证教师维护不会把不等价引用、未知依赖或异源导入覆盖当通过。"""

from pathlib import Path
from typing import Any

import nbformat
import pytest

from instructor.authoring_contracts import current_source_quote
from instructor.check_export_contracts import audit_notebook
from instructor.lint_notebooks import classify_diagnostics


def test_quotes_match_formatting_and_embedded_worker_but_reject_changed_behavior() -> None:
    source = 'packet = {\n    "id": "seat",\n    "ok": True,\n}\n'
    assert current_source_quote("packet = {'id': 'seat', 'ok': True}", source) == source.rstrip()
    worker = 'WORKER = ("def take(value):\\n" "    return value\\n")'
    assert current_source_quote("def take(value):", worker) == "def take(value):"
    with pytest.raises(ValueError, match="不再等价"):
        current_source_quote("packet = {'id': 'seat', 'ok': False}", source)


def test_export_audit_reports_unprovided_annotation_without_executing(tmp_path: Path) -> None:
    lesson = tmp_path / "lesson.ipynb"
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_code_cell(
            "def choose(mode: Literal['read']) -> str:\n    raise NotImplementedError('本人')",
            id="mine", metadata={"tags": ["exercise"]},
        ),
        nbformat.v4.new_code_cell(
            "prelude = ''\nexport_definitions(ROOT / 'lesson.ipynb', ['mine'], ['choose'], "
            "ROOT / 'project/choose.py', prelude)", id="wire",
            metadata={"tags": ["exercise-test"]},
        ),
    ])
    nbformat.write(notebook, lesson)
    result = audit_notebook(lesson, tmp_path)
    assert result[0]["missing_globals"] == ["Literal"]
    assert result[0]["learner_implementation_pending"] is True
    assert not (tmp_path / "project").exists()


def test_lint_explains_only_same_source_repeated_imports(tmp_path: Path) -> None:
    lesson = tmp_path / "lesson.ipynb"
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_code_cell("from one import label", metadata={"tags": ["setup"]}),
        nbformat.v4.new_code_cell("from one import label", metadata={"tags": ["demo"]}),
        nbformat.v4.new_code_cell("from other import label", metadata={"tags": ["demo"]}),
    ])
    nbformat.write(notebook, lesson)
    def diagnostic(cell: int) -> dict[str, Any]:
        return {"filename": str(lesson), "cell": cell, "code": "F811",
                "message": "Redefinition of unused `label` from cell 1, line 1",
                "location": {"row": 1, "column": 1}}
    report = classify_diagnostics([diagnostic(2), diagnostic(3)])
    assert len(report["explained_imports"]) == 1
    assert len(report["teacher_errors"]) == 1
