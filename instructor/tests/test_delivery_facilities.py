"""验证原生传输边界、学习证据版本与作品交付缺口。"""

import hashlib
import json
from pathlib import Path

import httpx
import nbformat
import pytest
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from instructor.learning_evidence import inspect_attempt, record_attempt
from instructor.native_gateway import NativeGateway, validate_wire_messages
from instructor.portfolio import inspect_portfolio, summarize_workflow_trial


def test_wire_requires_tool_pairing_and_does_not_promote_external_roles() -> None:
    history = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "read", "arguments": "{}"},
                }
            ],
        }
    ]
    with pytest.raises(ValueError, match="齐全"):
        validate_wire_messages(history)
    validate_wire_messages(
        [*history, {"role": "tool", "tool_call_id": "call-1", "content": "原文"}]
    )
    with pytest.raises(ValueError, match="配对"):
        validate_wire_messages([{"role": "tool", "tool_call_id": "wrong", "content": ""}])


@pytest.mark.asyncio
async def test_native_gateway_counts_failures_and_returns_only_public_fields() -> None:
    model = ChatDeepSeek(
        model="test-model",
        api_key=SecretStr("fixture-only"),
        base_url="https://example.invalid",
        extra_body={"thinking": {"type": "disabled"}},
    )
    gateway = NativeGateway(model, 1)

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "test-model" and body["thinking"]["type"] == "disabled"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "公开答复", "reasoning_content": "不得保存的内部内容"}}
                ],
                "usage": {"total_tokens": 7},
            },
        )

    result = await gateway.chat(
        [{"role": "user", "content": "问话"}], transport=httpx.MockTransport(handler)
    )
    assert result["calls"] == 1 and result["message"]["content"] == "公开答复"
    assert "内部内容" not in json.dumps(result, ensure_ascii=False)
    with pytest.raises(RuntimeError, match="耗尽"):
        await gateway.chat([{"role": "user", "content": "问话"}])


def test_evidence_retains_help_and_detects_changed_artifact_without_progress_write(
    tmp_path: Path,
) -> None:
    (tmp_path / "instructor").mkdir()
    lesson = tmp_path / "modules/lesson.ipynb"
    lesson.parent.mkdir()
    (tmp_path / "instructor/catalog.json").write_text(
        json.dumps({"tasks": [{"id": "M01-T01", "notebook": "modules/lesson.ipynb"}]})
    )
    nbformat.write(
        nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_code_cell(
                    "label = '本人标签'", id="mine", metadata={"tags": ["exercise"]}
                )
            ]
        ),
        lesson,
    )
    output = tmp_path / "outputs/result.json"
    output.parent.mkdir()
    output.write_text('{"status":"returned"}')
    record = record_attempt(
        tmp_path,
        "M01-T01",
        lesson,
        ["mine"],
        output,
        signal="program",
        help_level="teacher_takeover",
    )
    assert not record["independent_work_claim"] and record["mastery"] == "not_inferred"
    assert inspect_attempt(tmp_path, record)["current_content_matches"]
    output.write_text('{"status":"changed"}')
    assert inspect_attempt(tmp_path, record)["changed"] == ["artifact"]
    assert not (tmp_path / "instructor/state.json").exists()


def test_portfolio_requires_each_current_file_and_real_handover_locations(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text("label = '已保存'\n")
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    packet = {
        "files": [{"path": "module.py", "sha256": sha}],
        "checks": [{"path": "module.py", "sha256": sha, "passed": True}],
    }
    result = inspect_portfolio(tmp_path, packet)
    assert result["status"] == "incomplete" and "缺交付依据：runbook" in result["issues"]
    for field in ["acceptance", "demo", "runbook", "failure_case"]:
        target = tmp_path / (field + ".md")
        target.write_text("实际交付位置")
        packet[field] = target.name
    assert inspect_portfolio(tmp_path, packet)["status"] == "ready_for_review"
    source.write_text("label = '新版'\n")
    assert inspect_portfolio(tmp_path, packet)["status"] == "incomplete"
    packet["runbook"] = ".env"
    with pytest.raises(ValueError, match="秘密"):
        inspect_portfolio(tmp_path, packet)


def test_workflow_quality_failure_blocks_release_despite_time_saving() -> None:
    result = summarize_workflow_trial(
        [
            {
                "before_seconds": 100,
                "after_seconds": 20,
                "quality_ok": True,
                "critical_failure": False,
            },
            {
                "before_seconds": None,
                "after_seconds": None,
                "quality_ok": False,
                "critical_failure": True,
            },
        ]
    )
    assert result["mean_seconds_saved"] == 80 and result["unmeasured_pairs"] == 1
    assert not result["release_allowed"]
