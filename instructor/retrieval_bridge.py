"""将本人切块、向量排序和RRF实际接到本人上下文；不提供学生算法兜底。"""

from __future__ import annotations

import asyncio
import importlib
import json
import re
from pathlib import Path
from typing import Any


def embed_current(root: Path, texts: list[str]) -> list[list[float]]:
    """使用本课真实本地模型进行数值转换。

    Args:
        root: 仓库；texts: 查询与实际片段。
    Returns:
        对应的384维向量；不替代本人排序。
    Raises:
        模型缓存或计算错误原样保留。
    """
    from fastembed import TextEmbedding

    engine = TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        threads=1,
        cache_dir=str(root / "outputs/model-cache"),
        local_files_only=True,
    )
    return [vector.tolist() for vector in engine.embed(texts)]


class RAGContext:
    """组合明确传入的本人上下文、检索与融合函数。"""

    def __init__(self, root: Path, base: Any, retrieval: Any, fusion: Any) -> None:
        self.root, self.base, self.retrieval, self.fusion = root, base, retrieval, fusion

    async def build(self, state: dict[str, Any]) -> dict[str, Any]:
        """把实际选中chunk文字交到本次模型输入，而非只保存在旁边。

        Args:
            state: 当前问题、简报与实际sources。
        Returns:
            本人打包文字、实际检索片段与公开位置清单，总字符上限20000。
        Raises:
            ValueError: 片段伪造、身份重复或预算越界；未完成本人实现原样暴露。
        """
        packed = await self.base.build(state)
        sources = [s for s in state["sources"] if s.get("ok")]
        if not sources:
            return {**packed, "retrieval_chunks": []}
        chunks = self.retrieval.chunk_sources(sources, 900, 100)
        if len(chunks) > 240:
            raise ValueError("本次检索片段超过240；先缩小本人简报范围，不能静默截断")
        originals = {source["source_id"]: source for source in sources}
        if len(originals) != len(sources):
            raise ValueError("冲突版本需要不同source_id，不能在检索中静默覆盖")
        identities = {}
        for chunk in chunks:
            origin = originals.get(chunk["source_id"])
            if (
                origin is None
                or chunk["url"] != origin["url"]
                or chunk["text"] != origin["text"][chunk["start"] : chunk["end"]]
                or chunk["chunk_id"] in identities
            ):
                raise ValueError("本人chunk的位置、原文或身份不符合实际来源")
            identities[chunk["chunk_id"]] = chunk
        if not chunks:
            raise ValueError("成功原文未产生任何本人片段")
        brief = state.get("brief", {})
        queries, subquestions = brief.get("queries", []), brief.get("subquestions", [])
        if state.get("query"):
            query = state["query"]  # 本轮已明确的补证查询。
        elif state["question"] in subquestions and queries:
            index = subquestions.index(state["question"])
            if index >= len(queries):
                raise ValueError("本人简报子题与查询不能正确配对")
            query = queries[index]
        else:
            query = " ".join(queries) if queries else state["question"]
        vectors = await asyncio.to_thread(
            embed_current, self.root, [query, *[chunk["text"] for chunk in chunks]]
        )
        semantic = self.retrieval.rank_chunks(vectors[0], vectors[1:], chunks, min(12, len(chunks)))
        terms = set(re.findall(r"[a-z0-9_]+", query.lower()))
        lexical = sorted(
            chunks,
            key=lambda row: (-sum(term in row["text"].lower() for term in terms), row["chunk_id"]),
        )[:12]
        ids = self.fusion.combine_rankings(
            [[row["chunk_id"] for row in semantic], [row["chunk_id"] for row in lexical]],
            min(4, len(chunks)),
            60,
        )
        if (
            not ids
            or len(ids) > 4
            or len(ids) != len(set(ids))
            or any(i not in identities for i in ids)
        ):
            raise ValueError("本人融合结果超出候选身份或本次top-k")
        selected = [identities[i] for i in ids]
        text = (
            packed["model_text"]
            + "\n本次RAG实际选中的原文片段：\n"
            + json.dumps(selected, ensure_ascii=False)
        )
        if len(text) > 20000:
            raise ValueError("本人上下文与检索片段超过20000字符，缩小范围后重试")
        return {
            **packed,
            "model_text": text,
            "chars": len(text),
            "retrieval_chunks": selected,
            "retrieval_query": query,
            "retrieval_limits": {"chunks": 240, "top_k": 4, "chars": 20000},
        }


def connect_owned_retrieval(root: Path, base: Any) -> RAGContext:
    """显式加载本人的两个检索模块，缺失时不回退教师算法。

    Args:
        root: 仓库；base: 本人上下文适配器。
    Returns:
        实际消费本人检索的适配器。
    Raises:
        FileNotFoundError: 指定本人模块尚未导出。
    """
    for relative in ["project/m05_retrieval.py", "project/m05_hybrid.py"]:
        if not (root / relative).is_file():
            raise FileNotFoundError("混合检索缺本人导出，请完成M05-T03/T05：" + relative)
    return RAGContext(
        root,
        base,
        importlib.import_module("project.m05_retrieval"),
        importlib.import_module("project.m05_hybrid"),
    )
