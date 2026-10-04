"""交互设施的可重复替身测试；不调用真实模型，也不登记学生掌握。"""

import asyncio
import json
from pathlib import Path

import pytest

from instructor.interaction import show_desk, show_quiz


def _quiz_root(tmp_path: Path) -> Path:
    directory = tmp_path / "instructor"
    directory.mkdir()
    item = {
        "id": "input-evidence",
        "prompt": "公告在哪一步进入模型输入？",
        "options": [
            {
                "id": "printed",
                "label": "只打印公告",
                "feedback": "打印只让人看到，尚未发送给模型。",
            },
            {"id": "message", "label": "放进实际消息", "feedback": "这一轮请求确实包含公告正文。"},
        ],
        "correct": "message",
        "concept": "本地数据与请求上下文不同",
    }
    (directory / "course_enrichment.json").write_text(
        json.dumps({"tasks": {"M01-T01": {"quiz": [item]}}}, ensure_ascii=False),
        encoding="utf-8",
    )
    return tmp_path


def test_quiz_no_default_and_no_submission_without_choice(tmp_path: Path) -> None:
    controller = show_quiz("M01-T01", _quiz_root(tmp_path), display_ui=False)
    assert controller.questions["input-evidence"].value is None
    assert controller.submit_buttons["input-evidence"].disabled
    assert controller.submit("input-evidence") is None
    assert not controller.attempts_path.exists()


def test_quiz_feedback_retry_and_choice_records_are_not_mastery(tmp_path: Path) -> None:
    controller = show_quiz("M01-T01", _quiz_root(tmp_path), display_ui=False)
    controller.choose("input-evidence", "printed")
    wrong = controller.submit("input-evidence")
    assert wrong is not None and wrong["matched_expected"] is False
    assert "打印只让人看到" in controller.feedback["input-evidence"].value
    assert "这一轮请求确实包含" in controller.feedback["input-evidence"].value
    controller.retry("input-evidence")
    assert controller.questions["input-evidence"].value is None
    assert controller.feedback["input-evidence"].value == ""
    controller.choose("input-evidence", "message")
    correct = controller.submit("input-evidence")
    assert correct is not None and correct["matched_expected"] is True
    records = [json.loads(line) for line in controller.attempts_path.read_text().splitlines()]
    assert [row["selected"] for row in records] == ["printed", "message"]
    assert records[0]["attempt_id"] != records[1]["attempt_id"]
    assert all("mastery" not in row and "completed" not in row for row in records)
    assert not (tmp_path / "instructor/state.json").exists()


async def test_desk_calls_only_provided_handler_with_selection_and_saves_artifact(
    tmp_path: Path,
) -> None:
    calls = []
    artifact = tmp_path / "outputs/my-answer.md"
    artifact.parent.mkdir()
    artifact.write_text("周六下午两点开门。", encoding="utf-8")

    async def learner_handler(question: str, selection: str | None) -> dict:
        calls.append((question, selection))
        return {
            "answer": "周六下午两点开门。[NOTICE-B]",
            "evidence": [{"source_id": "NOTICE-B", "title": "临时公告", "text": "14:00开门"}],
            "artifacts": [{"label": "本人答复", "path": artifact}],
            "trace": [{"tool": "read_notice", "ok": True}],
        }

    desk = show_desk(
        "M01",
        learner_handler,
        tmp_path,
        display_ui=False,
        selections={"B": {"label": "临时公告", "evidence": ["14:00开门"]}},
    )
    record = await desk.submit(" 周六几点开门？ ", "B")
    assert calls == [("周六几点开门？", "B")]
    assert record is not None and record["status"] == "completed"
    assert desk.state == "completed" and desk.last_result["answer"].startswith("周六")
    assert "14:00开门" in desk.output_evidence.value
    assert "/files/outputs/my-answer.md" in desk.artifacts.value
    assert desk.run_dir is not None
    saved = json.loads((desk.run_dir / "result.json").read_text())
    assert saved["result"]["artifacts"][0]["path"] == "outputs/my-answer.md"
    assert (desk.run_dir / "request.json").is_file()
    assert "mastery" not in saved and not (tmp_path / "instructor/state.json").exists()


async def test_blank_question_and_missing_selection_never_call_handler(tmp_path: Path) -> None:
    calls = []

    async def handler(question: str, selection: str | None) -> dict:
        calls.append(question)
        return {"answer": "答复"}

    desk = show_desk("M01", handler, tmp_path, display_ui=False, selections={"A": "公告A"})
    assert await desk.submit("   ") is None
    assert await desk.submit("有问题但没选公告") is None
    assert calls == []
    assert desk.state == "idle"
    assert not (tmp_path / "outputs/interactive").exists()


async def test_repeated_send_is_rejected_and_button_event_is_real(tmp_path: Path) -> None:
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def handler(question: str, selection: str | None) -> dict:
        calls.append(question)
        entered.set()
        await release.wait()
        return {"answer": "办好了这次问答。"}

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    desk.question.value = "第一张问题纸"
    desk.send_button.click()
    await entered.wait()
    assert desk.state == "running" and desk.send_button.disabled
    assert await desk.submit("不应并发发出的第二张") is None
    release.set()
    await desk.wait_idle()
    assert calls == ["第一张问题纸"]
    assert desk.state == "completed" and not desk.send_button.disabled


async def test_cancel_waits_for_actual_handler_cancellation_and_saves_no_answer(
    tmp_path: Path,
) -> None:
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def handler(question: str, selection: str | None) -> dict:
        entered.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    desk.start("请查这件事")
    await entered.wait()
    assert await desk.cancel() is True
    assert cancelled.is_set()
    assert desk.state == "cancelled" and desk.last_result is None
    assert desk.last_record["status"] == "cancelled" and "result" not in desk.last_record
    assert desk.run_dir is not None
    assert json.loads((desk.run_dir / "result.json").read_text())["status"] == "cancelled"
    assert await desk.cancel() is False


async def test_immediate_cancel_does_not_leave_controls_stuck(tmp_path: Path) -> None:
    async def handler(question: str, selection: str | None) -> dict:
        await asyncio.Event().wait()
        return {"answer": "不应出现"}

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    desk.start("立即停止")
    assert await desk.cancel() is True
    assert desk.state == "cancelled"
    assert not desk.send_button.disabled and desk.cancel_button.disabled
    assert desk.last_record is not None and desk.last_record["status"] == "cancelled"


async def test_timeout_is_real_cancellation_and_error_not_success(tmp_path: Path) -> None:
    exited = asyncio.Event()

    async def handler(question: str, selection: str | None) -> dict:
        try:
            await asyncio.Event().wait()
        finally:
            exited.set()

    desk = show_desk("M01", handler, tmp_path, display_ui=False, timeout_seconds=0.01)
    record = await desk.submit("等不到回复")
    assert exited.is_set()
    assert record["status"] == "error" and record["diagnostic"]["type"] == "TimeoutError"
    assert desk.last_result is None and not desk.send_button.disabled


async def test_student_placeholder_surfaces_without_fallback(tmp_path: Path) -> None:
    async def student(question: str, selection: str | None) -> dict:
        raise NotImplementedError("answer_reader尚未完成")

    desk = show_desk("M01", student, tmp_path, display_ui=False)
    record = await desk.submit("请回答")
    assert record["status"] == "error"
    assert record["diagnostic"]["type"] == "NotImplementedError"
    assert "本人代码格" in desk.conversation.value
    assert desk.last_result is None


async def test_private_fields_secrets_and_html_are_not_rendered_or_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "test-provider-key-should-not-be-shown"
    monkeypatch.setenv("EXAMPLE_API_KEY", secret)

    async def handler(question: str, selection: str | None) -> dict:
        return {
            "answer": "<script>do_bad()</script> " + secret,
            "evidence": [{"title": "<img src=x>", "text": "正文", "url": "javascript:alert(1)"}],
            "trace": [
                {"tool": "read", "authorization": secret, "reasoning_content": "private-thought"}
            ],
            "memory": {"preference": "简短", "api_key": secret},
            "raw_response": secret,
        }

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    record = await desk.submit("请查")
    serialized = json.dumps(record, ensure_ascii=False)
    assert secret not in serialized and "private-thought" not in serialized
    assert "authorization" not in serialized and "raw_response" not in serialized
    assert "<script>" not in desk.conversation.value and "&lt;script&gt;" in desk.conversation.value
    assert 'href="javascript:' not in desk.output_evidence.value
    assert "&lt;img" in desk.output_evidence.value


async def test_error_diagnostic_redacts_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "provider-secret-in-exception"
    monkeypatch.setenv("MODEL_API_KEY", secret)

    async def handler(question: str, selection: str | None) -> dict:
        raise RuntimeError("请求失败 " + secret)

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    record = await desk.submit("请查")
    assert record["status"] == "error"
    assert secret not in json.dumps(record, ensure_ascii=False)
    assert secret not in desk.diagnostics.value
    assert "RuntimeError" in desk.diagnostics.value


async def test_missing_or_outside_artifacts_are_not_falsely_linked(tmp_path: Path) -> None:
    async def missing(question: str, selection: str | None) -> dict:
        return {"answer": "我生成了一份文件", "artifacts": ["outputs/not-created.md"]}

    desk = show_desk("M01", missing, tmp_path, display_ui=False)
    record = await desk.submit("生成文件")
    assert record["status"] == "error" and desk.artifacts.value == ""

    async def outside(question: str, selection: str | None) -> dict:
        return {"answer": "文件", "artifacts": [str(tmp_path / ".env")]}

    desk2 = show_desk("M01", outside, tmp_path, display_ui=False)
    record2 = await desk2.submit("请看文件")
    assert record2["status"] == "error" and record2["diagnostic"]["type"] == "ValueError"


async def test_budget_exhausted_stays_incomplete_and_new_runs_have_unique_directories(
    tmp_path: Path,
) -> None:
    async def handler(question: str, selection: str | None) -> dict:
        return {"answer": "还缺一份原文，暂时没法办妥。", "status": "budget_exhausted"}

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    first = await desk.submit("请查")
    assert first["status"] == "incomplete" and desk.state == "incomplete"
    first_dir = desk.run_dir
    second = await desk.submit("再查一次")
    assert desk.run_dir != first_dir and second["run_id"] != first["run_id"]
    assert (first_dir / "result.json").exists()


def test_styles_have_keyboard_focus_narrow_layout_and_reduced_motion() -> None:
    css = (Path(__file__).resolve().parents[1] / "assets/fog-desk.css").read_text()
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert "max-width: 560px" in css
    assert "#f5f1e6" in css and "#203e42" in css and "#9b7939" in css


@pytest.mark.parametrize(
    ("handler_status", "expected_state", "visible_text"),
    [
        ("needs_evidence", "incomplete", "还没办完"),
        ("failed", "failed", "没能办成"),
        ("error", "failed", "没能办成"),
        ("cancelled", "cancelled", "已停下"),
        ("needs_confirmation", "needs_confirmation", "等你确认"),
        ("awaiting_approval", "needs_confirmation", "等你确认"),
        ("pending", "incomplete", "还没办完"),
        ("new_workflow_state", "unrecognized", "状态还需要核对"),
    ],
)
async def test_handler_business_status_does_not_become_request_success(
    tmp_path: Path, handler_status: str, expected_state: str, visible_text: str
) -> None:
    async def handler(question: str, selection: str | None) -> dict:
        return {"answer": "这里是当前能确认的信息。", "status": handler_status}

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    record = await desk.submit("请办理")
    assert record["request_status"] == "returned"
    assert record["handler_status"] == handler_status
    assert record["status"] == expected_state and record["status"] != "completed"
    assert desk.state == expected_state and visible_text in desk.status.value
    assert handler_status in desk.diagnostics.value
    assert desk.run_dir is not None
    saved = json.loads((desk.run_dir / "result.json").read_text())
    assert saved["request_status"] == "returned" and saved["handler_status"] == handler_status
    if expected_state == "unrecognized":
        assert record["diagnostic"]["type"] == "UnrecognizedHandlerStatus"


async def test_explicit_handler_status_and_unspecified_business_state_are_distinct(
    tmp_path: Path,
) -> None:
    async def awaiting_confirmation(question: str, selection: str | None) -> dict:
        return {"answer": "请林禾核对后再发出。", "handler_status": "needs_confirmation"}

    desk = show_desk("M01", awaiting_confirmation, tmp_path, display_ui=False)
    record = await desk.submit("请准备通知")
    assert record["request_status"] == "returned"
    assert record["handler_status"] == "needs_confirmation"
    assert record["status"] == "needs_confirmation"

    async def no_claim(question: str, selection: str | None) -> dict:
        return {"answer": "这是本次答复，没有额外声明业务完成。"}

    plain = show_desk("M01", no_claim, tmp_path, display_ui=False)
    plain_record = await plain.submit("请回复")
    assert plain_record["request_status"] == "returned"
    assert plain_record["handler_status"] is None
    assert plain.last_result["handler_status"] is None


@pytest.mark.parametrize(
    "status_fields",
    [
        {"handler_status": "needs_confirmation", "status": "completed"},
        {"status": ["completed"]},
        {"handler_status": ""},
    ],
)
async def test_conflicting_or_invalid_handler_status_is_invalid_response(
    tmp_path: Path, status_fields: dict
) -> None:
    async def handler(question: str, selection: str | None) -> dict:
        return {"answer": "这份状态声明无法确定。", **status_fields}

    desk = show_desk("M01", handler, tmp_path, display_ui=False)
    record = await desk.submit("请办理")
    assert record["request_status"] == "invalid_response"
    assert record["status"] == "error"
    assert desk.last_result is None


async def test_exception_and_user_cancellation_use_request_status_not_handler_status(
    tmp_path: Path,
) -> None:
    async def failed_request(question: str, selection: str | None) -> dict:
        raise RuntimeError("请求连接断开")

    failed = show_desk("M01", failed_request, tmp_path, display_ui=False)
    record = await failed.submit("请查")
    assert record["request_status"] == "failed" and record["handler_status"] is None

    entered = asyncio.Event()

    async def waiting(question: str, selection: str | None) -> dict:
        entered.set()
        await asyncio.Event().wait()
        return {"answer": "不应完成"}

    cancelled = show_desk("M01", waiting, tmp_path, display_ui=False)
    cancelled.start("请查")
    await entered.wait()
    assert await cancelled.cancel()
    assert cancelled.last_record["request_status"] == "cancelled"
    assert cancelled.last_record["handler_status"] is None


@pytest.mark.parametrize("revision", ["reorder", "reword_and_reassign"])
def test_quiz_attempt_retains_original_meaning_after_question_revision(
    tmp_path: Path, revision: str
) -> None:
    import hashlib

    root = _quiz_root(tmp_path)
    controller = show_quiz("M01-T01", root, display_ui=False)
    assert controller.feedback["input-evidence"].value == ""
    assert controller.questions["input-evidence"].value is None
    controller.choose("input-evidence", "printed")
    original = controller.submit("input-evidence")
    assert original is not None
    assert original["schema_version"] == 2
    snapshot = original["question_snapshot"]
    serialized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert original["question_sha256"] == hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    assert original["selected_label"] == "只打印公告"
    assert original["expected_label"] == "放进实际消息"

    file = root / "instructor/course_enrichment.json"
    config = json.loads(file.read_text())
    revised = config["tasks"]["M01-T01"]["quiz"][0]
    revised["options"].reverse()
    if revision == "reword_and_reassign":
        revised["prompt"] = "修订后的另一种表达"
        revised["options"][0]["label"] = "修订的显示选项"
        revised["options"][1]["label"] = "修订的请求选项"
        revised["correct"] = "printed"
    file.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    updated = show_quiz("M01-T01", root, display_ui=False)
    assert updated.questions["input-evidence"].value is None
    assert updated.feedback["input-evidence"].value == ""
    updated.choose("input-evidence", "printed")
    updated.submit("input-evidence")

    attempts = [json.loads(line) for line in controller.attempts_path.read_text().splitlines()]
    old, new = attempts
    assert old["question_sha256"] != new["question_sha256"]
    assert old["question_snapshot"]["prompt"] == "公告在哪一步进入模型输入？"
    assert old["question_snapshot"]["options"][0]["label"] == "只打印公告"
    assert old["question_snapshot"]["options"][0]["feedback"] == "打印只让人看到，尚未发送给模型。"
    assert old["question_snapshot"]["correct"] == "message"
    assert old["selected_label"] == "只打印公告" and old["expected_label"] == "放进实际消息"
    assert old["matched_expected"] is False
    assert not (root / "instructor/state.json").exists()
