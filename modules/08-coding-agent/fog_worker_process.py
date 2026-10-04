"""Notebook的有限子进程运行设施，超时清理明确登记的本次容器。"""

from __future__ import annotations

import asyncio
import json
import re
import signal
import sys
from pathlib import Path
from typing import Any

from fog_coding_runtime import _remove_container


def _session_workspace(session_file: Path, allowed_root: Path) -> Path:
    allowed_root = allowed_root.resolve()
    if not session_file.resolve().is_relative_to(allowed_root):
        raise ValueError("工单路径越界")
    record = json.loads(session_file.read_text(encoding="utf-8"))
    workspace = Path(record["workspace"]).resolve()
    if not workspace.is_relative_to(allowed_root):
        raise ValueError("工作台路径越界")
    return workspace


async def run_worker(
    script: Path, session_file: Path, allowed_root: Path, wait_seconds: int = 130
) -> dict[str, Any]:
    """运行明确指定的静态工作进程，不执行模型生成的宿主机脚本。

    Args:
        script: 本页展示并确定的教师或本人编排脚本；session_file: 本次工单。
        allowed_root: 工单和工作区必须位于此边界；wait_seconds: 整个子进程等待秒数。
    Returns:
        exit_code/stdout/stderr，内容来自真实子进程。
    Raises:
        ValueError: 路径或容器登记不合法；TimeoutError: 子进程超时；RuntimeError: 回收失败。
    """
    workspace = await asyncio.to_thread(_session_workspace, session_file, allowed_root)
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script),
        str(session_file),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    communication = asyncio.create_task(process.communicate())
    try:
        stdout, stderr = await asyncio.wait_for(asyncio.shield(communication), timeout=wait_seconds)
        return {
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace")[-6000:],
            "stderr": stderr.decode("utf-8", errors="replace")[-6000:],
        }
    except (TimeoutError, asyncio.CancelledError):
        if process.returncode is None:
            process.send_signal(signal.SIGINT)
        try:
            await asyncio.wait_for(asyncio.shield(communication), timeout=20)
        except TimeoutError:
            if process.returncode is None:
                process.kill()
            await asyncio.wait_for(communication, timeout=5)
        raise
    finally:
        active = workspace / "active-container.json"
        if active.exists():
            data = json.loads(active.read_text(encoding="utf-8"))
            name = data.get("name", "")
            if not re.fullmatch(r"fog-coding-[0-9a-f]{16}", name):
                raise ValueError("容器登记不合法，不执行任意名称回收")
            cleanup = asyncio.create_task(_remove_container(name))
            try:
                await asyncio.shield(cleanup)
            except asyncio.CancelledError:
                await cleanup
                raise
            active.unlink(missing_ok=True)
