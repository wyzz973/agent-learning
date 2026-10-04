"""雾岛引用工作台的文件与容器设施，不包含模型控制循环。"""

from __future__ import annotations

import asyncio
import difflib
import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def _drain(stream: asyncio.StreamReader) -> str:
    kept = bytearray()
    total = 0
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            break
        total += len(chunk)
        kept.extend(chunk[: max(0, 6000 - len(kept))])
    return kept.decode("utf-8", errors="replace") + ("\n[输出已截断]" if total > len(kept) else "")


async def _remove_container(name: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "docker",
        "rm",
        "-f",
        name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
    except TimeoutError as error:
        proc.kill()
        await asyncio.wait_for(proc.wait(), timeout=5)
        raise RuntimeError("容器回收超时，需要确认：" + name) from error
    detail = stderr.decode("utf-8", errors="replace")
    if proc.returncode and "No such container" not in detail:
        raise RuntimeError("容器回收失败：" + name + "；" + detail)


async def _cleanup(proc: asyncio.subprocess.Process | None, name: str) -> None:
    try:
        await _remove_container(name)
    finally:
        if proc is not None and proc.returncode is None:
            proc.kill()
            await asyncio.wait_for(proc.wait(), timeout=5)


class CodingWorkspace:
    """独立的引用组件工作目录。

    Args:
        run_dir: 当前工作目录，其work只包含候选源码和固定测试。
        image: 已在本机准备好的Python镜像，不自动拉取。
    """

    def __init__(self, run_dir: Path, image: str = "python:3.12-alpine") -> None:
        self.run_dir = run_dir.resolve()
        self.work = self.run_dir / "work"
        self.image = image
        self.meta_path = self.run_dir / "workspace.json"
        self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        self._check_integrity()

    @classmethod
    def create(cls, parent: Path, source: str, tests: str, label: str = "desk") -> CodingWorkspace:
        """创建新工作区，默认不允许写入候选。

        Args:
            parent: 本次任务的产物目录；source: Python文本；tests: 固定测试文本。
            label: 仅字母数字和连字符组成的目录前缀。
        Returns:
            独立工作台对象，不覆盖已存在的文件。
        Raises:
            ValueError: 文本或标签不合法；OSError: 文件创建失败。
        """
        if not re.fullmatch(r"[A-Za-z0-9-]+", label) or not source or not tests:
            raise ValueError("标签或源码/测试文本不合法")
        run_dir = parent / (label + "-" + uuid.uuid4().hex[:12])
        work = run_dir / "work"
        work.mkdir(parents=True, exist_ok=False)
        (work / "candidate.py").write_text(source, encoding="utf-8")
        (work / "test_candidate.py").write_text(tests, encoding="utf-8")
        (run_dir / "original.py.txt").write_text(source, encoding="utf-8")
        meta = {
            "workspace_id": run_dir.name,
            "write_allowed": False,
            "tests_sha": _sha(tests),
            "original_sha": _sha(source),
        }
        (run_dir / "workspace.json").write_text(json.dumps(meta), encoding="utf-8")
        work.chmod(0o755)
        (work / "candidate.py").chmod(0o644)
        (work / "test_candidate.py").chmod(0o444)
        return cls(run_dir)

    @classmethod
    def reopen(cls, run_dir: Path, allowed_root: Path) -> CodingWorkspace:
        """从磁盘重新打开工作台，限制在允许的产物目录。

        Args:
            run_dir: 已保存的工作台目录；allowed_root: 当前课程产物边界。
        Returns:
            新对象，状态来自实际磁盘记录。
        Raises:
            ValueError: 路径越界或完整性失败；OSError: 文件不可读取。
        """
        if not run_dir.resolve().is_relative_to(allowed_root.resolve()):
            raise ValueError("工作区越出允许目录")
        return cls(run_dir)

    def _check_integrity(self) -> None:
        if self.work.is_symlink():
            raise ValueError("工作目录不能是符号链接")
        for filename in ("candidate.py", "test_candidate.py"):
            if (self.work / filename).is_symlink():
                raise ValueError("源码或测试不能是符号链接")
        current_tests = (self.work / "test_candidate.py").read_text(encoding="utf-8")
        if _sha(current_tests) != self.meta["tests_sha"]:
            raise ValueError("固定测试已被改变，拒绝运行")

    def set_write_permission(self, allowed: bool) -> None:
        """保存本次工作台的明确写入授权。

        Args:
            allowed: 必须是bool，不接受模型传入的任意字符串。
        Returns:
            无，保存到不向容器挂载的权限记录。
        Raises:
            ValueError: 参数不是bool；OSError: 写入失败。
        """
        if type(allowed) is not bool:
            raise ValueError("授权必须明确为True或False")
        self.meta["write_allowed"] = allowed
        self.meta_path.write_text(json.dumps(self.meta), encoding="utf-8")

    def source_sha(self) -> str:
        """取得当前候选源码指纹。

        Args:
            无。
        Returns:
            SHA-256字符串。
        Raises:
            OSError: 文件不可读。
        """
        return _sha((self.work / "candidate.py").read_text(encoding="utf-8"))

    def read(self) -> dict[str, Any]:
        """领取候选源码与不可改动的测试。

        Args:
            无。
        Returns:
            source、tests、指纹与写入许可，不提供宿主机目录浏览。
        Raises:
            ValueError: 测试完整性失败；OSError: 文件不可读。
        """
        self._check_integrity()
        return {
            "source": (self.work / "candidate.py").read_text(encoding="utf-8"),
            "tests": (self.work / "test_candidate.py").read_text(encoding="utf-8"),
            "source_sha": self.source_sha(),
            "write_allowed": self.meta["write_allowed"],
        }

    def edit(self, content: str) -> dict[str, Any]:
        """只保存candidate.py的完整候选文本，绝不在宿主机执行。

        Args:
            content: 1～30000字符的完整Python源码，不能指定文件名。
        Returns:
            写入结果与指纹；拒绝时返回原因。
        Raises:
            ValueError: 固定测试被改动；OSError: 文件系统错误。
        """
        self._check_integrity()
        if not self.meta["write_allowed"]:
            return {"ok": False, "error": "林禾尚未允许这次工作台写入。"}
        if not content or len(content) > 30000 or "\x00" in content:
            return {"ok": False, "error": "候选源码为空、过长或包含空字符。"}
        (self.work / "candidate.py").write_text(content, encoding="utf-8")
        return {"ok": True, "source_sha": self.source_sha(), "note": "候选已保存，仍须运行测试。"}

    def docker_arguments(self, name: str) -> list[str]:
        """生成固定容器测试命令。

        Args:
            name: 程序创建的唯一容器名。
        Returns:
            不经shell的参数列表，容器只能读取本工作台work目录。
        Raises:
            ValueError: 完整性检查失败。
        """
        self._check_integrity()
        return [
            "docker",
            "run",
            "--rm",
            "--name",
            name,
            "--pull=never",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "64",
            "--memory",
            "256m",
            "--cpus",
            "1",
            "--user",
            "65534:65534",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,noexec,size=16m",
            "--mount",
            "type=bind,source=" + str(self.work) + ",target=/work,readonly",
            "--workdir",
            "/work",
            self.image,
            "python",
            "-B",
            "-m",
            "unittest",
        ]

    async def run_tests(self) -> dict[str, Any]:
        """在受限容器运行固定测试，停止时回收自己的容器。

        Args:
            无。
        Returns:
            退出码、测试数、有界日志与源码指纹；超时返回失败。
        Raises:
            RuntimeError: 容器回收失败；OSError: Docker启动失败；CancelledError: 整段取消。
        """
        name = "fog-coding-" + uuid.uuid4().hex[:16]
        before = self.source_sha()
        active_file = self.run_dir / "active-container.json"
        active_file.write_text(json.dumps({"name": name}), encoding="utf-8")
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *self.docker_arguments(name),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            assert proc.stdout is not None and proc.stderr is not None
            stdout, stderr, code = await asyncio.wait_for(
                asyncio.gather(_drain(proc.stdout), _drain(proc.stderr), proc.wait()), timeout=20
            )
            match = re.search(r"Ran (\d+) tests?", stderr)
            count = int(match.group(1)) if match else 0
            stable = before == self.source_sha()
            result = {
                "ok": code == 0 and count > 0 and stable,
                "exit_code": code,
                "test_count": count,
                "stdout": stdout,
                "stderr": stderr,
                "source_sha": before,
                "stable_source": stable,
                "container": name,
            }
        except TimeoutError:
            result = {
                "ok": False,
                "error": "工作台测试超过20秒。",
                "test_count": 0,
                "stderr": "",
                "source_sha": before,
                "container": name,
            }
        finally:
            cleanup = asyncio.create_task(_cleanup(proc, name))
            try:
                await asyncio.shield(cleanup)
            except asyncio.CancelledError:
                await cleanup
                active_file.unlink(missing_ok=True)
                raise
            active_file.unlink(missing_ok=True)
        result["container_removed"] = True
        (self.run_dir / ("test-" + uuid.uuid4().hex[:8] + ".json")).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (self.run_dir / "latest-test.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

    def latest_verified(self) -> bool:
        """核对最近一次测试是否覆盖当前候选。

        Args:
            无。
        Returns:
            最近测试通过且源码指纹一致才为True。
        Raises:
            ValueError: 固定测试完整性失败；OSError: 记录不可读。
        """
        self._check_integrity()
        path = self.run_dir / "latest-test.json"
        if not path.exists():
            return False
        last = json.loads(path.read_text(encoding="utf-8"))
        return bool(last.get("ok") and last.get("source_sha") == self.source_sha())

    def diff(self) -> str:
        """比较最初源码与当前候选。

        Args:
            无。
        Returns:
            unified diff文本，没变则为空。
        Raises:
            OSError: 文件不可读。
        """
        original = (self.run_dir / "original.py.txt").read_text().splitlines(keepends=True)
        current = (self.work / "candidate.py").read_text().splitlines(keepends=True)
        return "".join(
            difflib.unified_diff(original, current, fromfile="before.py", tofile="candidate.py")
        )
