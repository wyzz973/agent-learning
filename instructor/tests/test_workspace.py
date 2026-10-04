"""验证统一接待台只消费本次本人函数、许可与真实事件。"""

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from instructor.course_workspace import OPERATIONS, show_module_workspace
from instructor.interaction import show_desk


def fixture_root(path: Path) -> Path:
    """准备公开界面素材，不提供学生代码或模型答案。"""
    notices = path / "world/notices"
    notices.mkdir(parents=True)
    for name in ["opening.md", "temporary.md", "return-box.md"]:
        (notices / name).write_text("[FIXTURE] 测试素材", encoding="utf-8")
    (path / "instructor").mkdir()
    (path / "instructor/course_enrichment.json").write_text(
        json.dumps(
            {
                "modules": {
                    mid: {"opening": "林禾的委托 <script>不可执行</script>", "desk_title": mid}
                    for mid in OPERATIONS
                }
            }
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.asyncio
async def test_controls_are_captured_and_approval_consumed_once(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    entered = asyncio.Event()
    release = asyncio.Event()
    seen = []

    async def handler(
        question: str, selection: str | None, controls: dict[str, Any]
    ) -> dict[str, Any]:
        seen.append(controls)
        entered.set()
        await release.wait()
        return {"answer": question, "evidence": [], "artifacts": [], "status": "answered"}

    workspace = show_module_workspace("M08", handler, root, display_ui=False)
    workspace.approval.value = True
    workspace.user.value = "reader-b"
    workspace.desk.start("查看当前候选")
    await entered.wait()
    assert workspace.approval.disabled and workspace.user.disabled
    assert workspace.approval.value is False
    assert seen[0]["approved"] is True and seen[0]["user_id"] == "reader-b"
    release.set()
    await workspace.desk.wait_idle()
    assert workspace.desk.last_record is not None
    assert workspace.desk.last_record["trusted_controls"]["approved"] is True
    await workspace.desk.submit("再提一次")
    assert seen[1]["approved"] is False
    assert not workspace.user.disabled


@pytest.mark.asyncio
@pytest.mark.parametrize("module", list(OPERATIONS))
async def test_every_workspace_keeps_missing_student_implementation_visible(
    tmp_path: Path, module: str
) -> None:
    root = fixture_root(tmp_path)

    async def missing(
        question: str, selection: str | None, controls: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError("本人组件尚未完成")

    workspace = show_module_workspace(module, missing, root, display_ui=False)
    record = await workspace.desk.submit("真实接线检查")
    assert record is not None and record["request_status"] == "failed"
    assert record["diagnostic"]["type"] == "NotImplementedError"
    assert record.get("result") is None
    assert not (root / "instructor/state.json").exists()


@pytest.mark.asyncio
async def test_actual_progress_retained_and_late_event_rejected(tmp_path: Path) -> None:
    entered = asyncio.Event()
    release = asyncio.Event()
    desk: Any = None

    async def stream(question: str, selection: str | None) -> dict[str, Any]:
        desk.emit_progress({"stage": "正在答复", "text": "当前"})
        desk.emit_progress({"stage": "正在答复", "text": "原文"})
        entered.set()
        await release.wait()
        return {"answer": "当前原文", "evidence": [], "artifacts": [], "status": "answered"}

    desk = show_desk("M09", stream, tmp_path, display_ui=False)
    desk.start("问话")
    await entered.wait()
    assert "当前原文" in desk.conversation.value
    release.set()
    await desk.wait_idle()
    assert [e["text"] for e in desk.last_record["progress_events"]] == ["当前", "原文"]
    with pytest.raises(RuntimeError, match="停止"):
        desk.emit_progress({"stage": "晚到事件", "text": "不能追加"})
    assert len(desk.progress_events) == 2


@pytest.mark.asyncio
async def test_cancelled_workspace_releases_controls_without_result(tmp_path: Path) -> None:
    root = fixture_root(tmp_path)
    entered = asyncio.Event()
    exited = asyncio.Event()

    async def handler(
        question: str, selection: str | None, controls: dict[str, Any]
    ) -> dict[str, Any]:
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            exited.set()
        return {"answer": "不应返回", "evidence": [], "artifacts": []}

    workspace = show_module_workspace("M10", handler, root, display_ui=False)
    workspace.desk.start("请查资料")
    await entered.wait()
    assert await workspace.desk.cancel()
    assert exited.is_set() and not workspace.operation.disabled
    assert workspace.desk.last_record is not None
    assert workspace.desk.last_record["status"] == "cancelled"
