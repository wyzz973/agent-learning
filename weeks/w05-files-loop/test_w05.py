"""本周行为规格，学习者占位符应明确失败。"""

from pathlib import Path
from typing import Any

import pytest
from ex1_files import read_text_tool, safe_path, successful_paths
from ex2_loop import execute_call, index_tools, run_agent
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


@tool
def echo(text: str) -> str:
    """返回输入文本，供测试工具调用。"""
    return text


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self


def test_demo_safe_path(tmp_path: Path) -> None:
    assert safe_path(tmp_path, "a.md") == tmp_path / "a.md"
    with pytest.raises(ValueError):
        safe_path(tmp_path, "../outside.md")
    with pytest.raises(ValueError):
        safe_path(tmp_path, str(tmp_path / "a.md"))


def test_demo_safe_path_rejects_external_symlink(tmp_path: Path) -> None:
    (tmp_path / "link.md").symlink_to(tmp_path.parent / "outside.md")
    with pytest.raises(ValueError):
        safe_path(tmp_path, "link.md")


def test_read_text_tool_success(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("中文内容", encoding="utf-8")
    assert read_text_tool(tmp_path, "a.md") == {
        "ok": True,
        "path": "a.md",
        "content": "中文内容",
        "error": None,
    }


def test_read_text_tool_errors(tmp_path: Path) -> None:
    (tmp_path / "bad.md").write_bytes(b"\xff")
    (tmp_path / "large.md").write_text("x" * 40000)
    for name in ["missing.md", "../outside.md", "bad.md", "large.md"]:
        result = read_text_tool(tmp_path, name)
        assert result["ok"] is False
        assert result["content"] == ""
        assert result["error"]


def test_successful_paths() -> None:
    rows = [{"ok": True, "path": "a.md"}, {"ok": False, "path": "b.md"}]
    assert successful_paths(rows) == ["a.md"]
    assert successful_paths([]) == []


async def test_demo_execute_call() -> None:
    result = await execute_call(
        {"echo": echo}, {"name": "echo", "args": {"text": "hello"}, "id": "c1", "type": "tool_call"}
    )
    assert isinstance(result, ToolMessage)
    assert result.content == "hello"
    assert result.tool_call_id == "c1"


async def test_demo_execute_call_error() -> None:
    result = await execute_call(
        {}, {"name": "missing", "args": {}, "id": "c2", "type": "tool_call"}
    )
    assert result.status == "error"
    assert result.tool_call_id == "c2"


def test_index_tools() -> None:
    assert index_tools([echo]) == {"echo": echo}
    assert index_tools([]) == {}


async def test_run_agent_returns_after_final_reply() -> None:
    model = ScriptedModel(messages=iter([AIMessage(content="done")]))
    messages = await run_agent(model, {}, "hello")
    assert messages[-1].text == "done"
    assert len(messages) == 2


async def test_run_agent_calls_tool_then_model() -> None:
    model = ScriptedModel(
        messages=iter(
            [
                AIMessage(
                    content="", tool_calls=[{"name": "echo", "args": {"text": "hello"}, "id": "c1"}]
                ),
                AIMessage(content="done"),
            ]
        )
    )
    messages = await run_agent(model, {"echo": echo}, "hello")
    assert isinstance(messages[2], ToolMessage)
    assert messages[2].content == "hello"
    assert messages[-1].text == "done"


async def test_run_agent_has_call_limit() -> None:
    reply = AIMessage(
        content="", tool_calls=[{"name": "echo", "args": {"text": "hello"}, "id": "c1"}]
    )
    model = ScriptedModel(messages=iter([reply, reply]))
    with pytest.raises(RuntimeError, match="上限"):
        await run_agent(model, {"echo": echo}, "hello", max_calls=1)
