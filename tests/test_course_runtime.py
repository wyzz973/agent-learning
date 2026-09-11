"""只验证教师装配，不用替身结果冒充学习者完成。"""

from types import SimpleNamespace

import pytest
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool

from agentlab import course_runtime as runtime


def test_tool_schemas_are_stable() -> None:
    tools = runtime.build_tools()
    assert [item.name for item in tools] == ["repository_search", "read_repository_file"]
    assert tools[0].get_input_schema().model_json_schema()["required"] == ["keyword"]
    assert tools[1].get_input_schema().model_json_schema()["required"] == ["path"]


def test_unreadable_evidence_is_not_silently_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    def read_error(root, name):
        return {"ok": False, "error": "fixture failed"}

    monkeypatch.setattr(runtime, "_lesson", lambda name: SimpleNamespace(read_text_tool=read_error))
    with pytest.raises(RuntimeError, match="fixture failed"):
        runtime.read_records()


async def test_langchain_wiring_executes_actual_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    @tool
    def probe(value: str) -> str:
        """教师探针，记录实参并返回固定观察。"""
        calls.append(value)
        return "observed"

    monkeypatch.setattr(runtime, "build_tools", lambda: [probe])
    model = runtime.ScriptedModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[{"name": "probe", "args": {"value": "input"}, "id": "p1"}],
                ),
                AIMessage(content="done"),
            ]
        )
    )
    result = await runtime.run_app("langchain", model)
    assert calls == ["input"]
    assert isinstance(result["result"]["messages"][2], ToolMessage)
    assert result["result"]["messages"][2].content == "observed"


async def test_unknown_mode_fails_clearly() -> None:
    with pytest.raises(ValueError, match="未知"):
        await runtime.run_app("not-a-mode", runtime.replay_model())
