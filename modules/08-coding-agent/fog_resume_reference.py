"""固定引用窗口案例的跨进程恢复参照；不调用或替代学生控制函数。"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fog_coding_runtime import CodingWorkspace
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain.tools import tool


def _trace(messages: list[Any]) -> list[dict[str, Any]]:
    rows = []
    for message in messages:
        row = {"role": message.type, "text": message.text}
        if isinstance(message, AIMessage):
            row["tool_calls"] = message.tool_calls
        if isinstance(message, ToolMessage):
            row["tool_name"] = message.name
            row["tool_call_id"] = message.tool_call_id
        rows.append(row)
    return rows


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("session", type=Path)
    args = parser.parse_args()
    root = await asyncio.to_thread(lambda: Path(__file__).resolve().parents[2])
    allowed = root / "outputs/fog-island/M08-T02"
    if not args.session.resolve().is_relative_to(allowed.resolve()):
        raise ValueError("参照只能读取本关工作单")
    record = json.loads(args.session.read_text(encoding="utf-8"))
    if record.get("kind") != "teacher-reference" or record.get("status") != "paused":
        raise ValueError("固定参照只接受本关教师paused记录，不替代学生实现")
    work = CodingWorkspace.reopen(Path(record["workspace"]), allowed)
    if work.meta["workspace_id"] != record["workspace_id"]:
        raise ValueError("恢复到另一工作区")
    if (
        work.source_sha() != record["candidate_sha"]
        or work.meta["tests_sha"] != record["tests_sha"]
    ):
        raise ValueError("候选或测试已改变，不能直接沿用恢复记录")
    if record.get("allow_write") is not True or work.meta["write_allowed"] is not True:
        raise ValueError("本工单没有允许写入")
    load_dotenv(root / ".env", override=False)
    options: dict[str, Any] = {"temperature": 0, "timeout": 20, "max_retries": 0}
    model_id = os.environ["DEFAULT_MODEL"]
    if model_id.startswith("deepseek:"):
        options["extra_body"] = {"thinking": {"type": "disabled"}}
    model = init_chat_model(model_id, **options)
    prompt = (root / "world/prompts/M08-T02.md").read_text(encoding="utf-8")

    @tool
    def read_code() -> dict[str, Any]:
        """领取candidate.py与固定测试，核对当前候选和许可。"""
        return work.read()

    @tool
    def edit_code(content: str) -> dict[str, Any]:
        """把完整源码存入获准的candidate.py，不能改固定测试，保存后须复查。"""
        return work.edit(content)

    @tool
    async def run_tests() -> dict[str, Any]:
        """在隔离维修台运行固定检查，回传当前版本的结果与指纹。"""
        return await work.run_tests()

    app = create_agent(
        model,
        tools=[read_code, edit_code, run_tests],
        system_prompt=prompt,
        middleware=[ModelCallLimitMiddleware(run_limit=6, exit_behavior="error")],
    )
    question = (
        record["goal"]
        + "\n林禾留下的工单摘要："
        + record["handoff_note"]
        + "\n允许文件candidate.py；固定test_candidate.py不可改。请重新取当前代码并验证。"
    )
    async with asyncio.timeout(90):
        result = await app.ainvoke({"messages": [HumanMessage(question)]})
    latest_tool_test = None
    for message in result["messages"]:
        if isinstance(message, ToolMessage) and message.name == "run_tests":
            try:
                latest_tool_test = json.loads(message.text)
            except json.JSONDecodeError:
                latest_tool_test = None
    observed = bool(
        latest_tool_test
        and latest_tool_test.get("ok")
        and latest_tool_test.get("source_sha") == work.source_sha()
    )
    after = await work.run_tests()
    new_record = dict(record)
    new_record.update(
        {
            "status": "verified" if observed and work.latest_verified() else "needs_attention",
            "resumed_pid": os.getpid(),
            "final_candidate_sha": work.source_sha(),
            "latest_test": after,
            "agent_observed_current": observed,
            "trace": _trace(result["messages"]),
            "diff": work.diff(),
            "restoration_source_sha": hashlib.sha256(args.session.read_bytes()).hexdigest(),
        }
    )
    result_file = args.session.parent / "teacher-resumed-result.json"
    result_file.write_text(json.dumps(new_record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"status": new_record["status"], "pid": os.getpid(), "result": str(result_file)},
            ensure_ascii=False,
        )
    )
    return 0 if new_record["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
