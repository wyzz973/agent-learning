"""保证代码整理不运行答案、不复制调用格、不吞掉未完成状态。"""

from pathlib import Path

import nbformat
import pytest

from instructor import learner_exports


def make_lesson(tmp_path: Path, source: str, tag: str = "exercise") -> Path:
    path = tmp_path / "modules/lesson.ipynb"
    path.parent.mkdir()
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(source, id="mine", metadata={"tags": [tag]}),
        ]
    )
    nbformat.write(notebook, path)
    return path


def test_only_saved_definitions_are_exported_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(learner_exports, "ROOT", tmp_path)
    source = make_lesson(
        tmp_path,
        '@marker\ndef greeting(name):\n    return "你好" + name\n'
        'raise RuntimeError("不要执行调用格")',
    )
    target = tmp_path / "project/greeting.py"
    result = learner_exports.export_definitions(
        source, ["mine"], ["greeting"], target, "def marker(function):\n    return function\n"
    )
    assert result == target
    assert "@marker" in target.read_text()
    assert "不要执行调用格" not in target.read_text()
    assert target.with_suffix(".origin.json").exists()


def test_placeholder_and_teacher_cells_cannot_be_exported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(learner_exports, "ROOT", tmp_path)
    source = make_lesson(tmp_path, "def greeting():\n    raise NotImplementedError('本人完成')")
    with pytest.raises(ValueError, match="占位"):
        learner_exports.export_definitions(
            source, ["mine"], ["greeting"], tmp_path / "project/x.py", ""
        )
    notebook = nbformat.read(source, as_version=4)
    notebook.cells[0].metadata.tags = ["demo"]
    nbformat.write(notebook, source)
    with pytest.raises(ValueError, match="本人练习格"):
        learner_exports.export_definitions(
            source, ["mine"], ["greeting"], tmp_path / "project/x.py", ""
        )


def test_export_does_not_overwrite_an_existing_learner_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(learner_exports, "ROOT", tmp_path)
    source = make_lesson(tmp_path, "def greeting():\n    return '你好'")
    target = tmp_path / "project/x.py"
    target.parent.mkdir()
    target.write_text("# 本人另一份实现\n")
    with pytest.raises(FileExistsError):
        learner_exports.export_definitions(source, ["mine"], ["greeting"], target, "")
    assert target.read_text() == "# 本人另一份实现\n"


def test_export_rejects_unresolved_runtime_globals_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(learner_exports, "ROOT", tmp_path)
    source = make_lesson(tmp_path, "def inspect_dependency():\n    return structured_model")
    target = tmp_path / "project/probe.py"
    with pytest.raises(ValueError, match="structured_model"):
        learner_exports.export_definitions(source, ["mine"], ["inspect_dependency"], target, "")
    assert not target.exists()
    assert learner_exports.unresolved_globals(
        "items = [1]\ndef inspect_local():\n    return [str(item) for item in items]\n"
    ) == []


def test_saved_notebook_revision_requires_preview_and_keeps_old_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(learner_exports, "ROOT", tmp_path)
    source = make_lesson(tmp_path, "def label():\n    return '旧标签'")
    target = tmp_path / "project/label.py"
    learner_exports.export_definitions(source, ["mine"], ["label"], target, "")
    original = target.read_text()
    notebook = nbformat.read(source, as_version=4)
    notebook.cells[0].source = "def label():\n    return '新标签'"
    nbformat.write(notebook, source)
    preview = learner_exports.preview_export(source, ["mine"], ["label"], target, "")
    assert preview["status"] == "update" and "新标签" in preview["diff"]
    assert target.read_text() == original
    with pytest.raises(FileExistsError, match="先preview"):
        learner_exports.export_definitions(source, ["mine"], ["label"], target, "")
    learner_exports.export_definitions(
        source, ["mine"], ["label"], target, "", expected_previous_sha=preview["current_sha"]
    )
    assert "新标签" in target.read_text()
    history = target.parent / ".export-history/label" / preview["current_sha"] / target.name
    assert history.read_text() == original


def test_export_preserves_project_edits_made_after_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(learner_exports, "ROOT", tmp_path)
    source = make_lesson(tmp_path, "def label():\n    return '旧标签'")
    target = tmp_path / "project/label.py"
    learner_exports.export_definitions(source, ["mine"], ["label"], target, "")
    notebook = nbformat.read(source, as_version=4)
    notebook.cells[0].source = "def label():\n    return 'Notebook修订'"
    nbformat.write(notebook, source)
    preview = learner_exports.preview_export(source, ["mine"], ["label"], target, "")
    target.write_text("# 本人在project继续开发\n")
    with pytest.raises(FileExistsError, match="独立改动"):
        learner_exports.export_definitions(
            source, ["mine"], ["label"], target, "", expected_previous_sha=preview["current_sha"]
        )
    assert target.read_text() == "# 本人在project继续开发\n"


def test_origin_cannot_authorize_update_from_another_notebook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(learner_exports, "ROOT", tmp_path)
    source = make_lesson(tmp_path, "def label():\n    return '旧标签'")
    target = tmp_path / "project/label.py"
    learner_exports.export_definitions(source, ["mine"], ["label"], target, "")
    other = source.with_name("other.ipynb")
    notebook = nbformat.read(source, as_version=4)
    notebook.cells[0].source = "def label():\n    return '其他委托'"
    nbformat.write(notebook, other)
    assert learner_exports.preview_export(other, ["mine"], ["label"], target, "")["status"] == (
        "conflict"
    )
