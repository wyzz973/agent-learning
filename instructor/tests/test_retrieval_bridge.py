"""验证后续模型输入消费本人检索结果；向量与算法替身不冒称质量验收。"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from instructor import retrieval_bridge


@pytest.mark.asyncio
async def test_selected_student_chunks_reach_model_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = []

    class BaseFixture:
        async def build(self, state: dict[str, Any]) -> dict[str, Any]:
            called.append("context")
            return {"model_text": "本人上下文", "context_calls": 1, "manifest": []}

    def chunk_fixture(
        sources: list[dict[str, Any]], size: int, overlap: int
    ) -> list[dict[str, Any]]:
        called.append("chunk")
        return [
            {
                "chunk_id": s["source_id"] + "-1",
                "source_id": s["source_id"],
                "url": s["url"],
                "start": 0,
                "end": len(s["text"]),
                "text": s["text"],
            }
            for s in sources
        ]

    def rank_fixture(
        query: list[float], vectors: list[list[float]], chunks: list[dict[str, Any]], k: int
    ) -> list[dict[str, Any]]:
        called.append("rank")
        return chunks

    def fusion_fixture(rankings: list[list[str]], k: int, offset: int) -> list[str]:
        called.append("fusion")
        return ["B-1"]

    monkeypatch.setattr(
        retrieval_bridge, "embed_current", lambda root, texts: [[1.0, 0.0]] * len(texts)
    )
    bridge = retrieval_bridge.RAGContext(
        tmp_path,
        BaseFixture(),
        SimpleNamespace(chunk_sources=chunk_fixture, rank_chunks=rank_fixture),
        SimpleNamespace(combine_rankings=fusion_fixture),
    )
    sources = [
        {"source_id": "A", "url": "https://example.com/a", "text": "未选择的句子", "ok": True},
        {"source_id": "B", "url": "https://example.com/b", "text": "真正选择的句子", "ok": True},
    ]
    result = await bridge.build(
        {
            "question": "second topic",
            "brief": {
                "subquestions": ["first topic", "second topic"],
                "queries": ["query one", "query two"],
            },
            "sources": sources,
        }
    )
    assert result["retrieval_query"] == "query two"
    assert called == ["context", "chunk", "rank", "fusion"]
    assert "真正选择的句子" in result["model_text"]
    assert "未选择的句子" not in result["model_text"]
    assert result["context_calls"] == 1 and result["retrieval_chunks"][0]["chunk_id"] == "B-1"


def test_missing_owned_algorithms_do_not_fall_back(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="M05-T03/T05"):
        retrieval_bridge.connect_owned_retrieval(tmp_path, object())
