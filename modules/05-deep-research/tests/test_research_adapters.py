"""研究衔接的设施规格；替身只验证契约与调用，不提供本人算法。"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "tested_research_lab", ROOT / "modules/05-deep-research/library_facilities.py"
)
assert SPEC is not None and SPEC.loader is not None
lab = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lab
SPEC.loader.exec_module(lab)


def source() -> dict:
    text = "受控原文：检查点保存同一任务状态。"
    return {
        "ok": True,
        "source_id": "S1",
        "url": "https://docs.python.org/3/library/sqlite3.html",
        "text": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "retrieved_at": "fixture-time",
        "selected_windows": [{"start": 0, "end": 10}],
    }


def state() -> dict:
    return {
        "question": "林禾想核对恢复",
        "brief": {"constraints": ["来源可核对"]},
        "sources": [source()],
        "calls": 0,
        "max_calls": 8,
        "events": [],
    }


def context_module() -> SimpleNamespace:
    # 返回固定测试回执，不实现学生的摘要、归档或选择算法。
    async def canned_pack(question, documents, archive, limit, model=None, role=None):
        if documents:
            await model.ainvoke([lab.HumanMessage("受控摘要请求")])
        return {
            "question": question,
            "model_text": "本人接口的受控返回",
            "chars": len("本人接口的受控返回"),
            "archives": {"S1": str(archive / "fixed.txt")},
        }

    original = source()
    return SimpleNamespace(
        pack_context=AsyncMock(side_effect=canned_pack),
        fetch_archived=Mock(
            return_value={"source_id": "S1", "text": original["text"], "sha256": original["sha256"]}
        ),
    )


@pytest.mark.asyncio
async def test_owned_context_is_called_and_provenance_preserved(tmp_path):
    module = context_module()
    model = SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(text="摘要")))
    context = lab.OwnedContext(module, model, "阿灯", tmp_path)
    result = await context.build(state())
    assert result["context_calls"] == 1
    assert result["manifest"][0]["url"] == source()["url"]
    assert result["manifest"][0]["sha256"] == source()["sha256"]
    assert result["manifest"][0]["selected_windows"] == source()["selected_windows"]
    module.fetch_archived.assert_called_once()
    model.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_ignored_injected_model_is_rejected(tmp_path):
    module = context_module()
    module.pack_context.side_effect = None
    instruction = (
        state()["question"]
        + "\n林禾确认的委托："
        + json.dumps(state()["brief"], ensure_ascii=False)
        + "\n来源版本冲突：[]"
    )
    module.pack_context.return_value = {
        "question": instruction,
        "model_text": "空",
        "chars": 1,
        "archives": {},
    }
    with pytest.raises(ValueError, match="注入模型"):
        await lab.OwnedContext(module, None, "阿灯", tmp_path).build(state())


@pytest.mark.asyncio
async def test_summary_and_reasoning_are_both_charged(tmp_path, monkeypatch):
    class Model:
        def with_structured_output(self, *args, **kwargs):
            return self

        async def ainvoke(self, messages):
            return lab.GapCheck(missing=[], query="")

    context = lab.OwnedContext(context_module(), Model(), "阿灯", tmp_path)
    monkeypatch.setattr(lab, "snapshot_input", Mock(side_effect=AssertionError("不能回退教师快照")))
    nodes = lab.make_gap_nodes(Model(), "阿灯", context=context)
    current = state()
    current.update(await nodes["assess"](current))
    assert current["calls"] == 2 and current["context_calls"] == current["reasoning_calls"] == 1
    current["calls"] = 7
    with pytest.raises(RuntimeError, match="额度"):
        await nodes["write"](current)


@pytest.mark.asyncio
async def test_archive_mismatch_and_extra_summary_are_rejected(tmp_path):
    module = context_module()
    module.fetch_archived.return_value["text"] = "换了原文"
    model = SimpleNamespace(ainvoke=AsyncMock())
    with pytest.raises(ValueError, match="原文"):
        await lab.OwnedContext(module, model, "阿灯", tmp_path).build(state())
    counted = lab.CountedContextModel(model)
    await counted.ainvoke([])
    with pytest.raises(RuntimeError, match="最多允许一次"):
        await counted.ainvoke([])


def test_missing_owned_context_has_no_fallback(tmp_path):
    with pytest.raises(FileNotFoundError, match="M04-T04"):
        lab.owned_context(tmp_path, None, "阿灯", tmp_path / "archive")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://docs.python.org/x",
        "https://other.invalid/x",
        "https://user:pass@docs.python.org/x",
        "https://docs.python.org:444/x",
    ],
)
async def test_unregistered_network_targets_are_rejected(url, monkeypatch):
    monkeypatch.setattr(lab.httpx, "AsyncClient", Mock(side_effect=AssertionError("不得发请求")))
    assert (await lab.fetch_public(url))["ok"] is False


def test_twelve_distinct_cases_and_holdout_have_explicit_layers():
    development = lab.evaluation_cases(ROOT, [source()])
    assert len(development) == 9 and all(c["partition"] == "development" for c in development)
    cases = development + lab.evaluation_cases(ROOT, [source()], "holdout")
    assert len(cases) == len({case["question"] for case in cases}) == 12
    assert sum(case["partition"] == "holdout" for case in cases) == 3
    assert {case["kind"] for case in cases} == {"research", "boundary", "recovery"}
    assert all(case["max_calls"] == 8 for case in cases)
    assert next(c for c in cases if c["id"] == "D05")["sources"][0]["url"] == source()["url"]


@pytest.mark.asyncio
async def test_collection_search_discovers_other_registered_hosts(monkeypatch):
    monkeypatch.setattr(lab, "search_official", AsyncMock(return_value=[]))

    async def index_fetch(url):
        if "docs.python.org" in url:
            return {
                "ok": True,
                "text": "index",
                "raw_text": '<html><a href="asyncio-task.html">asyncio task</a></html>',
                "retrieved_at": "now",
            }
        return {
            "ok": True,
            "text": "[Tools](https://modelcontextprotocol.io/spec/tools)",
            "retrieved_at": "now",
        }

    monkeypatch.setattr(lab, "fetch_public", index_fetch)
    found = await lab.search_official_collection("asyncio task", 2)
    assert found[0]["url"] == "https://docs.python.org/3/library/asyncio-task.html"
    assert found[0]["host"] == "docs.python.org"


def test_holdout_candidate_cannot_change_after_release(tmp_path):
    (tmp_path / "project").mkdir()
    names = ["m04_context.py", "m05_gap_graph.py", "m06_team.py", "m06_evaluation.py"]
    for name in names:
        (tmp_path / "project" / name).write_text("# 候选指纹夹具，不包含学习者答案\n")
    before = lab.lock_holdout_candidate(tmp_path)
    assert lab.lock_holdout_candidate(tmp_path) == before
    (tmp_path / "project/m06_evaluation.py").write_text("# 改过的候选指纹\n")
    with pytest.raises(ValueError, match="独立留出"):
        lab.lock_holdout_candidate(tmp_path)
