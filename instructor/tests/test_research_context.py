"""验证来源限制和完成标准确实进入研究模型输入，不生成学生研究图。"""

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def facilities() -> ModuleType:
    root = Path(__file__).resolve().parents[2]
    path = root / "modules/05-deep-research/library_facilities.py"
    spec = importlib.util.spec_from_file_location("research_context_test_facilities", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_scope_constraints_reach_assessment_and_writing() -> None:
    lab = facilities()

    class InputRecorder:
        """仅记录输入，断言设施没有丢掉简报；不证明模型能力。"""

        def __init__(self) -> None:
            self.requests: list[Any] = []
            self.structured = False

        def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
            self.structured = True
            return self

        async def ainvoke(self, messages: Any) -> Any:
            self.requests.append(messages)
            if self.structured:
                self.structured = False
                return lab.GapCheck(missing=[], query="")
            from langchain.messages import AIMessage

            return AIMessage(content="林禾，已收到范围与完成标准。")

    recorder = InputRecorder()
    state = {
        "question": "怎样恢复委托？",
        "brief": {
            "constraints": ["只使用允许的馆务资料"],
            "done_when": ["明确仍缺少的批准信息"],
            "subquestions": ["怎样继续？"],
        },
        "sources": [],
        "events": [],
        "calls": 0,
        "max_calls": 3,
    }
    nodes = lab.make_gap_nodes(recorder, "你是雾岛图书馆阿灯。")
    await nodes["assess"](state)
    await nodes["write"](state)
    assert len(recorder.requests) == 2
    for request in recorder.requests:
        text = request[-1].text
        assert "只使用允许的馆务资料" in text
        assert "明确仍缺少的批准信息" in text
        assert "怎样恢复委托？" in text


@pytest.mark.asyncio
async def test_live_index_layout_variation_uses_discovered_python_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lab = facilities()
    calls = []
    current = "https://docs.langchain.com/_llms/agent-development-lifecycle/build/python.md"

    async def fetch_fixture(url: str) -> dict[str, Any]:
        calls.append(url)
        if url.endswith("/llms.txt"):
            text = f"- [Lifecycle / Build / Python (241 pages)]({current})\n" * 2
        elif url == current:
            text = "- [Memory](https://docs.langchain.com/oss/python/langchain/memory.md)"
        else:
            raise AssertionError("不能编造索引路径")
        return {"ok": True, "text": text, "retrieved_at": "fixture-time"}

    monkeypatch.setattr(lab, "fetch_public", fetch_fixture)
    rows = await lab.search_official("memory", 2)
    assert len(rows) == 1 and rows[0]["index_url"] == current
    assert calls == ["https://docs.langchain.com/llms.txt", current]
