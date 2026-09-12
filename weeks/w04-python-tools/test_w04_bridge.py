# 教师连接代码的检查｜不用改
"""教师连接代码检查，与学习者练习正确性分开。"""

import asyncio
import json
from typing import Any

import agent_demo
import pytest
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain.messages import AIMessage, ToolMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self


def test_bridge_schema() -> None:
    schema = agent_demo.repository_search.get_input_schema().model_json_schema()
    assert schema["required"] == ["keyword"]
    assert schema["properties"]["keyword"]["type"] == "string"


async def test_bridge_result_in_message_history(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = {"ok": True, "items": [{"path": "demo.py"}], "count": 1, "error": None}
    calls: list[str] = []

    def stub_search(records: list[dict[str, str]], keyword: str) -> dict[str, Any]:
        assert records is agent_demo.FILES
        calls.append(keyword)
        return expected

    monkeypatch.setattr(agent_demo, "search_repository", stub_search)
    model = ScriptedModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {"name": "repository_search", "args": {"keyword": "retry"}, "id": "c1"}
                    ],
                ),
                AIMessage(content="demo.py"),
            ]
        )
    )
    async with asyncio.timeout(5):
        result = await agent_demo.build_demo_agent(model).ainvoke(
            {"messages": [{"role": "user", "content": "find retry"}]}
        )
    assert calls == ["retry"]
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].tool_call_id == "c1"
    assert json.loads(tool_messages[0].content) == expected
    assert result["messages"][-1].text == "demo.py"


async def test_bridge_unfinished_exercise_stays_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    def unfinished(records: list[dict[str, str]], keyword: str) -> dict[str, Any]:
        raise NotImplementedError("learner exercise")

    monkeypatch.setattr(agent_demo, "search_repository", unfinished)
    with pytest.raises(NotImplementedError, match="learner exercise"):
        await agent_demo.repository_search.ainvoke({"keyword": "retry"})


async def test_bridge_execution_error_becomes_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(records: list[dict[str, str]], keyword: str) -> dict[str, Any]:
        raise KeyError("path")

    monkeypatch.setattr(agent_demo, "search_repository", broken)
    result = await agent_demo.repository_search.ainvoke({"keyword": "retry"})
    assert result == {"ok": False, "items": [], "count": 0, "error": "KeyError: 'path'"}


async def test_bridge_stops_repeated_model_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def stub_search(records: list[dict[str, str]], keyword: str) -> dict[str, Any]:
        calls.append(keyword)
        return {"ok": True, "items": [], "count": 0, "error": None}

    monkeypatch.setattr(agent_demo, "search_repository", stub_search)
    replies = []
    for index in range(6):
        replies.append(
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "repository_search", "args": {"keyword": "retry"}, "id": str(index)}
                ],
            )
        )
    model = ScriptedModel(messages=iter(replies))
    with pytest.raises(ModelCallLimitExceededError):
        async with asyncio.timeout(5):
            await agent_demo.build_demo_agent(model).ainvoke(
                {"messages": [{"role": "user", "content": "keep searching"}]}
            )
    assert len(calls) == 4
