"""雾岛研究课的可读教师设施：网络、模型连接、记录；不包含本人图路由答案。"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import os
import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import urljoin, urlparse

import httpx
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

SOURCE_MANIFEST = Path(__file__).resolve().parents[2] / "world/research/official-sources.json"
OFFICIAL_ORIGINS = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))["origins"]
OFFICIAL_HOSTS = {row["host"] for row in OFFICIAL_ORIGINS}


class ReadableHTML(HTMLParser):
    """只做HTML文本和链接提取，跳过脚本与样式，不运行页面代码。"""

    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.skip = 0
        self.href = ""
        self.label: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.skip += 1
        if tag == "a":
            self.href = dict(attrs).get("href") or ""
            self.label = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag == "a" and self.href:
            self.links.append((" ".join(self.label), self.href))
            self.href = ""

    def handle_data(self, data: str) -> None:
        if not self.skip and data.strip():
            self.text.append(data.strip())
            if self.href:
                self.label.append(data.strip())


class GapCheck(BaseModel):
    """阿灯交给林禾的证据缺口与下一条查询。"""

    missing: list[str] = Field(description="回答林禾问题仍缺的具体依据；足够时为空")
    query: str = Field(description="用于官方技术资料索引的简短英文查询；足够时为空")


class GapState(TypedDict, total=False):
    question: str
    brief: dict[str, Any]
    sources: list[dict[str, Any]]
    missing: list[str]
    query: str
    rounds: int
    max_rounds: int
    calls: int
    max_calls: int
    answer: str
    status: str
    events: list[dict[str, Any]]
    source_conflicts: list[dict[str, Any]]
    context_calls: int
    reasoning_calls: int
    input_fingerprint: str


def configure(root: Path, task_id: str) -> tuple[Any, str]:
    """创建本关模型对象并读取实际情景prompt。

    Args:
        root: 仓库根目录；task_id: 已登记的本关编号。
    Returns:
        模型对象与完整角色提示，不打印凭证。
    Raises:
        KeyError: 模型未配置；OSError: 提示文件缺失。
    """
    load_dotenv(root / ".env", override=False)
    name = os.environ["DEFAULT_MODEL"]
    options: dict[str, Any] = {"timeout": 20, "max_retries": 0}
    if name.startswith("deepseek:"):
        options["extra_body"] = {"thinking": {"type": "disabled"}}
    return init_chat_model(name, **options), (root / "world/prompts" / f"{task_id}.md").read_text(
        encoding="utf-8"
    )


async def ask(model: Any, role: str, request: str) -> str:
    """异步执行一次有超时的阿灯请求。

    Args:
        model: 已配置模型；role: 当前情景prompt；request: 用户问题和实际输入。
    Returns:
        普通回答文本，不导出原始元数据。
    Raises:
        TimeoutError: 超过20秒；模型错误原样保留。
    """
    async with asyncio.timeout(20):
        result = await model.ainvoke([SystemMessage(role), HumanMessage(request)])
    return result.text


async def fetch_public(url: str) -> dict[str, Any]:
    """读取登记的有限官方站点原文，不跟随重定向。

    Args:
        url: HTTPS默认端口的登记域名，无用户名密码；不跟随重定向。
    Returns:
        成功含原文、URL、时间和指纹；失败含ok=False与原因。
    Raises:
        无：预期网络与内容错误返回失败，不伪造原文。
    """
    try:
        parsed = urlparse(url)
        allowed = (
            parsed.scheme == "https"
            and parsed.hostname in OFFICIAL_HOSTS
            and not parsed.username
            and not parsed.password
            and parsed.port in {None, 443}
        )
    except ValueError:
        allowed = False
    if not allowed:
        return {"ok": False, "url": url, "error": "这个来源不在允许读取的官方资料范围内"}
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                if response.status_code != 200:
                    raise ValueError("页面没有返回完整原文")
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 240_000:
                        raise ValueError("页面超过240KB读取上限")
        original = bytes(raw).decode("utf-8")
        text = original
        if "<html" in original[:1000].lower():
            parser = ReadableHTML()
            parser.feed(original)
            text = "\n".join(parser.text)
        if not text.strip():
            raise ValueError("原文为空")
    except (httpx.HTTPError, ValueError, UnicodeError) as error:
        return {"ok": False, "url": url, "error": type(error).__name__ + "：本次未能取得原文"}
    return {
        "ok": True,
        "source_id": hashlib.sha256(url.encode()).hexdigest()[:12],
        "url": url,
        "text": text,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "raw_sha256": hashlib.sha256(bytes(raw)).hexdigest(),
        "raw_text": original,
    }


def index_entries(text: str) -> list[dict[str, str]]:
    """从官方Markdown索引取出候选标题和URL。

    Args:
        text: 本次实际取得的llms.txt原文。
    Returns:
        候选列表；这不是已抓取的页面正文。
    Raises:
        无。
    """
    return [
        {"title": title, "url": url}
        for title, url in re.findall(r"\[([^\]]+)\]\((https://[^)]+)\)", text)
    ]


async def search_official(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """在实时官方站点索引中发现页面，不能称为全网搜索。

    Args:
        query: 非空英文关键词；limit: 返回1至5个候选。
    Returns:
        含title/url/score/discovered_at的候选，不含页面正文。
    Raises:
        ValueError: 参数非法；RuntimeError: 索引获取失败。
    """
    if not query.strip() or not 1 <= limit <= 5:
        raise ValueError("查询不能为空，候选数量必须为1至5")
    root = await fetch_public("https://docs.langchain.com/llms.txt")
    if not root["ok"]:
        raise RuntimeError(root["error"])
    rows = index_entries(root["text"])
    legacy = [
        r
        for r in rows
        if r["url"].endswith(("/oss/python/langchain/llms.txt", "/oss/python/langgraph/llms.txt"))
    ]
    # 新版官方入口将Python文档集中到/_llms索引；入口仍必须来自本次实际发现。
    current = [
        r
        for r in rows
        if "/_llms/" in r["url"]
        and ("/build/python.md" in r["url"] or " / python" in r["title"].lower())
    ]
    chosen = list({r["url"]: r for r in (legacy or current)}.values())
    direct = [r for r in rows if "/oss/python/" in r["url"] and r["url"].endswith(".md")]
    if not chosen and not direct:
        raise RuntimeError("官方索引结构改变，请导师核对，不能编造候选页")
    candidates = []
    indexes = chosen[:4] or [{"url": "https://docs.langchain.com/llms.txt"}]
    for entry in indexes:
        index = (
            root
            if entry["url"].endswith("/llms.txt") and not chosen
            else await fetch_public(entry["url"])
        )
        if not index["ok"]:
            raise RuntimeError(index["error"])
        for page in index_entries(index["text"]):
            if not page["url"].startswith("https://docs.langchain.com/oss/python/"):
                continue
            words = (page["title"] + " " + page["url"]).lower()
            score = sum(word in words for word in query.lower().split())
            if score and page["url"].endswith(".md"):
                candidates.append(
                    {
                        **page,
                        "score": score,
                        "discovered_at": index["retrieved_at"],
                        "index_url": entry["url"],
                    }
                )
    candidates = list({row["url"]: row for row in candidates}.values())
    candidates.sort(key=lambda item: (-item["score"], item["url"]))
    return candidates[:limit]


async def search_official_collection(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """在三个登记的官方站点索引内发现候选，记录索引失败。

    Args:
        query: 非空关键词；limit: 1至5，按标题与URL词法匹配排序。
    Returns:
        候选含URL、来源域名、发现时间、索引限制；不包含假造页面正文。
    Raises:
        ValueError: 参数非法；RuntimeError: 所有索引都不可用。
    """
    if not query.strip() or not 1 <= limit <= 5:
        raise ValueError("查询不能为空，候选数量必须为1至5")
    candidates, failures = [], []
    successes = 0
    try:
        candidates.extend(await search_official(query, 5))
        successes += 1
    except RuntimeError as error:
        failures.append({"host": "docs.langchain.com", "error": str(error)})
    for origin in OFFICIAL_ORIGINS:
        if origin["host"] == "docs.langchain.com":
            continue
        index = await fetch_public(origin["index"])
        if not index["ok"]:
            failures.append({"host": origin["host"], "error": index["error"]})
            continue
        successes += 1
        if origin["format"] == "html":
            parser = ReadableHTML()
            parser.feed(index["raw_text"])
            entries = [
                {"title": title, "url": urljoin(origin["index"], href).split("#")[0]}
                for title, href in parser.links
            ]
        else:
            entries = index_entries(index["text"])
        for entry in entries:
            parsed = urlparse(entry["url"])
            if parsed.hostname != origin["host"] or parsed.scheme != "https":
                continue
            score = sum(
                word in (entry["title"] + " " + entry["url"]).lower()
                for word in query.lower().split()
            )
            if score:
                candidates.append({**entry, "score": score, "discovered_at": index["retrieved_at"]})
    if not successes:
        raise RuntimeError("所有官方索引获取失败：" + json.dumps(failures, ensure_ascii=False))
    unique = {item["url"]: item for item in candidates}
    ranked = sorted(unique.values(), key=lambda row: (-row["score"], row["url"]))[:limit]
    return [
        {**row, "host": urlparse(row["url"]).hostname, "index_failures": failures} for row in ranked
    ]


class CountedContextModel:
    """只计数本人打包函数实际发出的摘要请求，超过一次立即拒绝。"""

    def __init__(self, model: Any) -> None:
        self.model = model
        self.attempts = 0

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        if self.attempts >= 1:
            raise RuntimeError("一次上下文打包最多允许一次摘要模型请求")
        self.attempts += 1
        async with asyncio.timeout(20):
            return await self.model.ainvoke(*args, **kwargs)


class OwnedContext:
    """连接本人pack_context与fetch_archived；不包含打包算法或教师回退。"""

    def __init__(self, module: Any, model: Any, role: str, archive: Path) -> None:
        self.module, self.model, self.role, self.archive = module, model, role, archive

    async def build(self, state: dict[str, Any]) -> dict[str, Any]:
        """为一次研究模型输入调用本人打包与原文取回。

        Args:
            state: 当前问题、完整brief、真实sources；window定位附在记录中。
        Returns:
            model_text、实际摘要调用数及来源manifest；chars明确是字符。
        Raises:
            ValueError: 原文取回、字符数或字段不一致；本人未完成明确失败。
        """
        instruction = (
            state["question"]
            + "\n林禾确认的委托："
            + json.dumps(state.get("brief", {}), ensure_ascii=False)
            + "\n来源版本冲突："
            + json.dumps(state.get("source_conflicts", []), ensure_ascii=False)
        )
        sources = [source for source in state["sources"] if source.get("ok")]
        documents = [
            {
                "id": source["source_id"],
                "title": source.get("title", source["url"]),
                "text": source["text"],
                "url": source["url"],
                "selected_windows": source.get("selected_windows", []),
            }
            for source in sources
        ]
        counter = CountedContextModel(self.model)
        packed = await self.module.pack_context(
            instruction, documents, self.archive, 12000, model=counter, role=self.role
        )
        if packed["question"] != instruction:
            raise ValueError("本人资料夹丢失或改写了当前问题与研究约束")
        if packed["chars"] != len(packed["model_text"]) or packed["chars"] > 12000:
            raise ValueError("本人资料夹的字符预算或统计不一致")
        if counter.attempts != (1 if sources else 0):
            raise ValueError("有资料须用注入模型摘要一次；空资料不需要摘要，不得漏计或另建模型")
        manifest = []
        for source in sources:
            original = self.module.fetch_archived(
                source["source_id"], packed["archives"], self.archive
            )
            sha = hashlib.sha256(original["text"].encode()).hexdigest()
            if (
                original["text"] != source["text"]
                or original["sha256"] != sha
                or source["sha256"] != sha
            ):
                raise ValueError("本人取回的原文与输入快照不一致")
            manifest.append(
                {
                    "source_id": source["source_id"],
                    "url": source["url"],
                    "sha256": sha,
                    "raw_sha256": source.get("raw_sha256"),
                    "retrieved_at": source.get("retrieved_at"),
                    "selected_windows": source.get("selected_windows", []),
                    "archive": packed["archives"][source["source_id"]],
                }
            )
        text = (
            packed["model_text"] + "\n可核对的来源位置：" + json.dumps(manifest, ensure_ascii=False)
        )
        if len(text) > 16000:
            raise ValueError("摘要与来源清单超过本关输入字符预算，不能静默截断")
        return {
            "model_text": text,
            "chars": len(text),
            "context_calls": counter.attempts,
            "manifest": manifest,
        }


def owned_context(root: Path, model: Any, role: str, archive: Path) -> OwnedContext:
    """加载本课程本人上下文模块，缺失明确定位，不用snapshot_input回退。

    Args:
        root: 仓库；model/role: 本关模型与岗位；archive: 本次独立归档位置。
    Returns:
        只负责契约衔接的适配器。
    Raises:
        FileNotFoundError: M04本人导出缺失。
    """
    if not (root / "project/m04_context.py").is_file():
        raise FileNotFoundError("请完成M04-T04上下文打包/原文取回及导出格；研究不能回退教师输入")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return OwnedContext(importlib.import_module("project.m04_context"), model, role, archive)


def snapshot_input(sources: list[dict[str, Any]], chars: int = 6500) -> str:
    """给模型提供有限原文窗口，完整快照留在来源记录中。

    Args:
        sources: 实际成功来源；chars: 每份最多显示字符数。
    Returns:
        带来源身份和实际窗口范围的JSON文本。
    Raises:
        无。
    """
    rows = []
    for source in sources:
        if not source.get("ok"):
            continue
        windows = source.get(
            "selected_windows", [{"start": 0, "end": min(chars, len(source["text"]))}]
        )
        for window in windows:
            start, end = window["start"], window["end"]
            rows.append(
                {
                    "source_id": source["source_id"],
                    "url": source["url"],
                    "start": start,
                    "end": end,
                    "text": source["text"][start:end],
                }
            )
    return json.dumps(rows, ensure_ascii=False)


def save_json(path: Path, value: Any) -> Path:
    """保存公开实验记录，不自动登记本人完成。

    Args:
        path: 本次run内的目标；value: 不含密钥/内部推理的数据。
    Returns:
        写出的路径。
    Raises:
        OSError: 文件写入失败。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def require_artifact(root: Path, name: str, task_id: str) -> dict[str, Any]:
    """读取本课程本人已登记产物，无教师备用结果。

    Args:
        root: 项目根目录；name: project/artifacts内名称；task_id: 产物来源任务。
    Returns:
        保存的本人产物。
    Raises:
        FileNotFoundError: 尚未完成相应登记；ValueError: 来源身份不符。
    """
    path = root / "project/artifacts" / name
    if not path.is_file():
        raise FileNotFoundError(f"缺少本人{name}，请回到{task_id}的登记作品格完成并保存。")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("task_id") != task_id or data.get("owner") != "learner":
        raise ValueError("产物来源不是指定任务的本人记录，不能用教师结果替代")
    return data


def make_gap_nodes(
    model: Any, role: str, context: OwnedContext | None = None, search: Callable = search_official
) -> dict[str, Any]:
    """提供研究节点设施；条件路由和整图连接由本人实现。

    Args:
        model: 当前模型；role: 本关提示；context: 本人资料夹适配器，教师窄示范才省略。
        search: 明确范围的异步来源发现入口。
    Returns:
        assess/research/write/stop节点，每段设施在Notebook中展示。
    Raises:
        节点实际执行时，预算、网络与模型错误明确保留。
    """

    async def assess(state: GapState) -> dict[str, Any]:
        cost = 1 + int(context is not None and bool(state["sources"]))
        if state["calls"] + cost > state["max_calls"]:
            raise RuntimeError("阿灯已用完这项委托的摘要与研究模型调用额度")
        start = time.monotonic()
        packed = (
            await context.build(state)
            if context
            else {
                "model_text": snapshot_input(state["sources"]),
                "context_calls": 0,
                "manifest": [],
            }
        )
        checker = model.with_structured_output(GapCheck, method="function_calling")
        request = (
            "林禾需要你检查当前问题还有哪些依据缺口。已有原文足够就missing=[]，"
            "否则列一个最关键缺口并给一个简短英文官方资料查询。不要把缺口藏进完整结论。\n"
            + state["question"]
            + "\n实际资料窗口："
            + packed["model_text"]
        )
        if state.get("brief"):
            request += (
                "\n林禾确认的完整研究委托："
                + json.dumps(state["brief"], ensure_ascii=False)
                + "\n当前问题若是其中一项分工，只检查这项的证据缺口，"
                "同时遵守constraints与相关done_when；subquestions说明整体分工，"
                "不能因只拿到问题标题就丢掉来源边界或擅自扩大当前任务。"
            )
        async with asyncio.timeout(20):
            result = await checker.ainvoke([SystemMessage(role), HumanMessage(request)])
        event = {
            "stage": "assess",
            "calls": state["calls"] + 1 + packed["context_calls"],
            "missing": result.missing,
            "elapsed": time.monotonic() - start,
            "source_ids": [s["source_id"] for s in state["sources"]],
            "context_calls": packed["context_calls"],
            "context_manifest": packed["manifest"],
            "retrieval_chunks": [
                {key: chunk[key] for key in ["chunk_id", "source_id", "url", "start", "end"]}
                for chunk in packed.get("retrieval_chunks", [])
            ],
        }
        return {
            "missing": result.missing,
            "query": result.query,
            "context_calls": state.get("context_calls", 0) + packed["context_calls"],
            "reasoning_calls": state.get("reasoning_calls", 0) + 1,
            "calls": state["calls"] + 1 + packed["context_calls"],
            "events": state["events"] + [event],
        }

    async def research(state: GapState) -> dict[str, Any]:
        start = time.monotonic()
        hits = await search(state["query"], 2)
        sources = {s["source_id"]: s for s in state["sources"]}
        failures = []
        for hit in hits:
            source = await fetch_public(hit["url"])
            if source["ok"]:
                previous = sources.get(source["source_id"])
                if previous and previous["sha256"] != source["sha256"]:
                    raise ValueError(
                        "同一来源在研究中已变化；保留已有版本，需显式重建来源账本后重试"
                    )
                sources[source["source_id"]] = source
            else:
                failures.append(source["error"])
        event = {
            "stage": "research",
            "query": state["query"],
            "candidate_urls": [h["url"] for h in hits],
            "source_ids": list(sources),
            "failures": failures,
            "elapsed": time.monotonic() - start,
        }
        return {
            "sources": list(sources.values()),
            "rounds": state["rounds"] + 1,
            "events": state["events"] + [event],
        }

    async def write(state: GapState) -> dict[str, Any]:
        cost = 1 + int(context is not None and bool(state["sources"]))
        if state["calls"] + cost > state["max_calls"]:
            raise RuntimeError("阿灯没有剩余摘要与写作调用额度")
        start = time.monotonic()
        packed = (
            await context.build(state)
            if context
            else {
                "model_text": snapshot_input(state["sources"]),
                "context_calls": 0,
                "manifest": [],
            }
        )
        request = (
            "请把已取得的依据整理成给林禾的短报告，馆务事实引用通知编号，技术事实附实际URL，"
            "还不知道的地方直说。\n问题："
            + state["question"]
            + "\n原文窗口："
            + packed["model_text"]
        )
        if state.get("brief"):
            request += (
                "\n林禾确认的完整研究委托："
                + json.dumps(state["brief"], ensure_ascii=False)
                + "\n遵守constraints，并按当前问题相关的done_when核对交付；"
                "subquestions保留整体背景。若当前只负责一个子题，就说明本项结果，"
                "不要将其写成全部委托已经完成。"
            )
        answer = await ask(model, role, request)
        return {
            "answer": answer,
            "status": "reported",
            "context_calls": state.get("context_calls", 0) + packed["context_calls"],
            "reasoning_calls": state.get("reasoning_calls", 0) + 1,
            "calls": state["calls"] + 1 + packed["context_calls"],
            "events": state["events"]
            + [
                {
                    "stage": "write",
                    "elapsed": time.monotonic() - start,
                    "context_calls": packed["context_calls"],
                    "context_manifest": packed["manifest"],
                    "retrieval_chunks": [
                        {
                            key: chunk[key]
                            for key in ["chunk_id", "source_id", "url", "start", "end"]
                        }
                        for chunk in packed.get("retrieval_chunks", [])
                    ],
                }
            ],
        }

    def stop(state: GapState) -> dict[str, Any]:
        return {
            "status": "needs_evidence",
            "answer": "林禾，这些问题还需要补充依据：" + "；".join(state["missing"]),
            "events": state["events"] + [{"stage": "stop", "missing": state["missing"]}],
        }

    return {"assess": assess, "research": research, "write": write, "stop": stop}


async def run_owned_graph(
    root: Path,
    question: str,
    sources: list[dict[str, Any]],
    task_id: str,
    max_rounds: int = 1,
    db_path: Path | None = None,
    session_id: str = "research",
    event_sink: Callable | None = None,
    research_brief: dict[str, Any] | None = None,
    source_conflicts: list[dict[str, Any]] | None = None,
    use_hybrid: bool = False,
) -> dict[str, Any]:
    """运行本人研究图，恢复时核对任务与来源身份。

    Args:
        root: 仓库；question/sources: 实际输入；task_id: 当前prompt。
        max_rounds: 0至2；db_path/session_id: 持久会话；event_sink: 可选公开进度接收器。
        research_brief: 本人已确认的完整简报；source_conflicts: 本人合并的冲突版本。
        use_hybrid: 明确启用本人切块/排序/RRF，缺导出时拒绝，不回退算法。
    Returns:
        本人图实际状态；不是教师备用实现。
    Raises:
        FileNotFoundError: 缺本人导出；ValueError: 简报非法或同ID的题目/来源/简报变化。
    """
    if not 0 <= max_rounds <= 2:
        raise ValueError("研究轮数必须在0至2之间")
    if research_brief is not None and not isinstance(research_brief, dict):
        raise ValueError("research_brief必须为本人简报字典或None")
    brief = json.loads(json.dumps(research_brief or {}, ensure_ascii=False))
    if not (root / "project/m05_gap_graph.py").is_file():
        raise FileNotFoundError("请先完成M05-T04的本人图导出格")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    owned = importlib.import_module("project.m05_gap_graph")
    model, role = configure(root, task_id)
    archive = (
        (db_path.parent / (session_id + "-archives"))
        if db_path
        else root / "outputs/fog-island/research-context" / str(time.time_ns())
    )
    context: Any = owned_context(root, model, role, archive)
    retrieval_versions = {}
    if use_hybrid:
        from instructor.retrieval_bridge import connect_owned_retrieval

        context = connect_owned_retrieval(root, context)
        retrieval_versions = {
            name: hashlib.sha256((root / "project" / name).read_bytes()).hexdigest()
            for name in ["m05_retrieval.py", "m05_hybrid.py"]
        }
        retrieval_versions["bridge"] = hashlib.sha256(
            (root / "instructor/retrieval_bridge.py").read_bytes()
        ).hexdigest()
    nodes = make_gap_nodes(model, role, context=context, search=search_official_collection)
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "question": question,
                "brief": brief,
                "source_conflicts": source_conflicts or [],
                "use_hybrid": use_hybrid,
                "retrieval_versions": retrieval_versions,
                "sources": [
                    {
                        "id": s["source_id"],
                        "sha": hashlib.sha256(s["text"].encode()).hexdigest(),
                        "windows": s.get("selected_windows"),
                    }
                    for s in sources
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode()
    ).hexdigest()
    state: GapState = {
        "question": question,
        "brief": brief,
        "source_conflicts": source_conflicts or [],
        "sources": sources,
        "missing": [],
        "query": "",
        "rounds": 0,
        "max_rounds": max_rounds,
        "calls": 0,
        "max_calls": 8,
        "context_calls": 0,
        "reasoning_calls": 0,
        "answer": "",
        "status": "running",
        "events": [],
        "input_fingerprint": fingerprint,
    }
    config = {"recursion_limit": 30, "configurable": {"thread_id": session_id}}
    async with asyncio.timeout(180):
        if db_path is None:
            graph = owned.build_gap_graph(GapState, nodes)
            return await graph.ainvoke(state, config)
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        async with AsyncSqliteSaver.from_conn_string(str(db_path)) as saver:
            graph = owned.build_gap_graph(GapState, nodes, checkpointer=saver)
            saved = await graph.aget_state(config)
            if saved.values:
                if (
                    saved.values.get("question") != question
                    or saved.values.get("input_fingerprint") != fingerprint
                ):
                    raise ValueError(
                        "同一会话ID的研究问题、来源或简报已改变，请用新任务ID，不能返回旧报告"
                    )
                if not saved.next:
                    return saved.values
            async for update in graph.astream(
                None if saved.values else state, config, stream_mode="updates", durability="sync"
            ):
                if event_sink:
                    for name, patch in update.items():
                        event_sink(
                            {
                                "stage": name,
                                "time": time.time(),
                                "calls": patch.get("calls"),
                                "status": patch.get("status"),
                            }
                        )
            return (await graph.aget_state(config)).values


def evaluation_cases(
    root: Path, technical_sources: list[dict], phase: str = "development"
) -> list[dict]:
    """装配固定问题集，馆务原文与公开技术快照分清，不产生答案。

    Args:
        root: 仓库；technical_sources: 本人真实原文；phase: development或holdout。
    Returns:
        开发9题或留出3题，独立文件读取；注明研究/边界/恢复与来源范围。
    Raises:
        ValueError: 固定问题集不完整；OSError: 输入资料缺失。
    """
    if phase not in {"development", "holdout"}:
        raise ValueError("评估阶段必须是development或holdout")
    filename = (
        "evaluation-cases.json" if phase == "development" else "evaluation-holdout-cases.json"
    )
    records = json.loads((root / "world/research" / filename).read_text())
    cabinet = json.loads((root / "world/cabinet/catalog.json").read_text())
    by_id = {row["id"]: row for row in cabinet}
    for case in records:
        sources = []
        for document_id in case["documents"]:
            row = by_id[document_id]
            text = (root / row["path"]).read_text(encoding="utf-8")
            sources.append(
                {
                    "ok": True,
                    "source_id": document_id,
                    "title": row["title"],
                    "url": "world:///" + row["path"],
                    "text": text,
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "retrieved_at": "local-document",
                }
            )
        if case.get("use_technical_sources"):
            sources = json.loads(json.dumps(technical_sources, ensure_ascii=False))
        if case.get("controlled_conflict"):
            sources = [
                {
                    "ok": True,
                    "source_id": f"CONFLICT-{number}",
                    "url": f"world:///controlled/conflict-{number}.md",
                    "text": text,
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "retrieved_at": "controlled-input",
                }
                for number, text in enumerate(["周六16点闭馆。", "周六18点闭馆。"], 1)
            ]
        case["sources"] = sources
        case["max_calls"] = 8
        case["brief"] = {
            "question": case["question"],
            "subquestions": [case["question"]],
            "constraints": ["只按本题实际提供或授权取得的来源判断，不把未知安排补成事实"],
            "done_when": ["回答该问题并保留来源；资料不足明确说明；冲突不能静默选一份"],
        }
    expected = 9 if phase == "development" else 3
    if len(records) != expected or len({row["id"] for row in records}) != expected:
        raise ValueError("开发集与留出集的数量或身份不符")
    return records


async def run_evaluation_case(
    root: Path, case: dict, task_id: str, output: Path, grader: Callable
) -> dict:
    """执行固定集中的一题，区分研究质量、读取边界和恢复证明。

    Args:
        root: 仓库；case: 固定输入；task_id: 当前岗位；output: 本批产物目录。
        grader: 本人规则函数，研究和恢复题真实调用它。
    Returns:
        分层结果与真实状态；语义未审时明确pending。
    Raises:
        本人未实现、运行超时及其他异常保留给批次运行器分类。
    """
    base = {"case": case["id"], "kind": case["kind"], "partition": case["partition"]}
    if case["kind"] == "boundary":
        rejected = await fetch_public("https://not-authorized.invalid/research")
        return {
            **base,
            "passed": rejected["ok"] is False and "text" not in rejected,
            "observation": rejected,
            "model_calls": 0,
            "quality_layer": "tool-boundary",
        }
    kwargs = {"max_rounds": case["max_rounds"], "research_brief": case["brief"]}
    if case["kind"] == "recovery":
        events: list[dict] = []
        kwargs.update(
            db_path=output / (case["id"] + ".sqlite3"),
            session_id=case["id"],
            event_sink=events.append,
        )
        first = await run_owned_graph(root, case["question"], case["sources"], task_id, **kwargs)
        event_count = len(events)
        second = await run_owned_graph(root, case["question"], case["sources"], task_id, **kwargs)
        grade = grader(second, {**case, "expected_status": "reported"})
        recovered = first["input_fingerprint"] == second["input_fingerprint"]
        return {
            **base,
            "passed": bool(grade["passed"] and recovered and len(events) == event_count),
            "result": second,
            "checks": grade["checks"],
            "new_resume_events": len(events) - event_count,
            "quality_layer": "checkpoint-reopen",
            "semantic_review": "pending",
        }
    result = await run_owned_graph(root, case["question"], case["sources"], task_id, **kwargs)
    grade = grader(result, case)
    if set(grade["checks"]) != {"status", "budget", "source_trace", "completion"}:
        raise ValueError("本人grader没有按本页契约返回四个检查")
    if grade["passed"] != all(grade["checks"].values()):
        raise ValueError("总通过状态与各项检查不一致")
    (output / (case["id"] + "-report.md")).write_text(result["answer"], encoding="utf-8")
    return {
        **base,
        "passed": grade["passed"],
        "result": result,
        "checks": grade["checks"],
        "quality_layer": "research-behavior",
        "semantic_review": "pending",
    }


def lock_holdout_candidate(root: Path) -> dict[str, str]:
    """首次留出评估锁定本人候选，后续改代码不得仍声称独立留出成绩。

    Args:
        root: 仓库，读取本人已保存导出，不包含答案。
    Returns:
        源码指纹清单；开发阶段不调用此函数也不读取留出题。
    Raises:
        FileNotFoundError: 本人候选组件未导出；ValueError: 已锁定候选发生改变。
    """
    names = ["m04_context.py", "m05_gap_graph.py", "m06_team.py", "m06_evaluation.py"]
    hashes = {
        name: hashlib.sha256((root / "project" / name).read_bytes()).hexdigest() for name in names
    }
    lock = root / "project/artifacts/holdout-candidate.json"
    if lock.exists() and json.loads(lock.read_text()) != hashes:
        raise ValueError("看过留出结果后候选已修改；原留出题只能做回归，不能继续登记独立留出成绩")
    save_json(lock, hashes)
    return hashes
