"""雾岛本地服务运输设施：HTTP、持久队列与生命周期；研究处理由本人函数提供。"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
import inspect
import json
import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--mode", choices=["teacher", "learner"], required=True)
    parser.add_argument("--hold", action="store_true")
    args = parser.parse_args()
    root, run = args.root.resolve(), args.run.resolve()
    if not run.is_relative_to((root / "outputs").resolve()):
        raise ValueError("服务状态只能写入本课程outputs")
    run.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "modules/05-deep-research"))
    import library_facilities as lab

    database = run / "jobs.sqlite3"
    lock = threading.Lock()
    pool = ThreadPoolExecutor(max_workers=2)
    active: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Task]] = {}

    def input_fingerprint(question: str) -> str:
        source = (
            run / "sources.json"
            if args.mode == "teacher"
            else root / "project/artifacts/team-run.json"
        )
        payload = {
            "mode": args.mode,
            "question": question,
            "sources_sha": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def connect() -> sqlite3.Connection:
        db = sqlite3.connect(database, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    with connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, question TEXT, "
            "status TEXT, result TEXT, events TEXT, attempts INTEGER, input_sha TEXT)"
        )
        if "input_sha" not in {column[1] for column in db.execute("PRAGMA table_info(jobs)")}:
            db.execute("ALTER TABLE jobs ADD COLUMN input_sha TEXT")
            db.execute("UPDATE jobs SET status='failed' WHERE input_sha IS NULL")
        db.execute("UPDATE jobs SET status='queued' WHERE status='running' AND attempts<2")
        db.execute("UPDATE jobs SET status='failed' WHERE status='running' AND attempts>=2")
        db.execute("UPDATE jobs SET status='cancelled' WHERE status='cancelling'")

    def emit(job_id: str, event: dict) -> None:
        with lock, connect() as db:
            row = db.execute("SELECT events FROM jobs WHERE id=?", (job_id,)).fetchone()
            events = json.loads(row["events"])
            events.append(event)
            db.execute(
                "UPDATE jobs SET events=? WHERE id=?",
                (json.dumps(events, ensure_ascii=False), job_id),
            )

    async def handle(job_id: str, question: str) -> dict:
        if args.mode == "teacher":
            model, role = lab.configure(root, "M06-T04")
            sources = json.loads((run / "sources.json").read_text(encoding="utf-8"))
            emit(job_id, {"stage": "answer_started"})
            answer = await lab.ask(
                model,
                role,
                "林禾请你根据这份原文回答：" + question + "\n原文：" + lab.snapshot_input(sources),
            )
            emit(job_id, {"stage": "answer_finished"})
            return {
                "status": "reported",
                "answer": answer,
                "calls": 1,
                "source_urls": [s["url"] for s in sources],
            }
        if not (root / "project/m06_service.py").is_file():
            raise FileNotFoundError("请先完成M06-T04本人服务处理函数导出")
        for relative in [
            "project/m06_team.py",
            "project/m06_evaluation.py",
            "project/m04_context.py",
        ]:
            if not (root / relative).is_file():
                raise FileNotFoundError("服务缺少本人组件：" + relative)
        owned = importlib.import_module("project.m06_service")
        team = importlib.import_module("project.m06_team")
        evaluation = importlib.import_module("project.m06_evaluation")
        component_calls = {"workers": 0, "merge": 0, "grade": 0}
        research_attempts, research_results, grades = [], [], []
        merges, planned_counts, research_phases, session_keys = [], [], [], set()

        async def tracked_researcher(*values: object, **options: object) -> dict:
            # 本人服务明确消费M05新增的切块、向量排序与RRF，不只保存检索产物。
            options["use_hybrid"] = True
            if len(research_attempts) >= 3:
                raise RuntimeError("完整服务最多两个研究模块和一次汇总")
            arguments = inspect.signature(lab.run_owned_graph).bind(*values, **options)
            arguments.apply_defaults()
            params = arguments.arguments
            session = params["session_id"]
            database_path = params["db_path"]
            resolved_database = (
                await asyncio.to_thread(Path(database_path).resolve) if database_path else None
            )
            if (
                resolved_database is None
                or not resolved_database.is_relative_to(run)
                or not session.startswith(job_id)
                or session in session_keys
            ):
                raise ValueError("分工与汇总须使用本job下不同持久session_id与允许的checkpoint路径")
            session_keys.add(session)
            research_phases.append("synthesis" if merges else "worker")
            if merges:
                expected = {(s["url"], s["sha256"]) for s in merges[0]["sources"]}
                actual = {(s["url"], s["sha256"]) for s in params["sources"]}
                if (
                    not expected.issubset(actual)
                    or params["source_conflicts"] != merges[0]["conflicts"]
                ):
                    raise ValueError("汇总必须实际消费本人合并的新证据与冲突，不能只保存旁支结果")
            if len(research_attempts) >= 3:
                raise RuntimeError("完整服务最多两个研究模块和一次汇总")
            research_attempts.append(True)
            result = await lab.run_owned_graph(*values, **options)
            research_results.append(result)
            return result

        async def tracked_workers(
            questions: list[str], worker: object, max_workers: int = 2
        ) -> list:
            component_calls["workers"] += 1
            if component_calls["workers"] != 1 or not 1 <= len(questions) <= 2:
                raise ValueError("分工只能调用一次，并处理最多两个子题")
            planned_counts.append(len(questions))
            return await team.run_workers(questions, worker, max_workers)

        def tracked_merge(seed: list[dict], results: list[dict]) -> dict:
            component_calls["merge"] += 1
            merged = team.merge_worker_sources(seed, results)
            merges.append(merged)
            return merged

        def tracked_grade(result: dict, case: dict) -> dict:
            component_calls["grade"] += 1
            grade = evaluation.grade_run(result, case)
            grades.append(grade)
            return grade

        result = await owned.handle_research(
            root,
            question,
            job_id,
            run / (job_id + ".checkpoints.sqlite3"),
            tracked_researcher,
            lambda event: emit(job_id, event),
            tracked_workers,
            tracked_merge,
            tracked_grade,
        )
        if component_calls != {"workers": 1, "merge": 1, "grade": 1}:
            raise ValueError("本人服务必须实际运行分工、合并和评估，不能省略后假报完成")
        if research_phases != ["worker"] * planned_counts[0] + ["synthesis"]:
            raise ValueError("实际研究调用没有形成本人分工后再汇总的完整路径")
        if result.get("conflicts") != merges[0]["conflicts"]:
            raise ValueError("服务结果丢掉了本人合并的来源冲突")
        if not grades or result.get("quality") != grades[0]:
            raise ValueError("服务返回的quality不是本人grader的实际结果")
        observed_calls = sum(row["calls"] for row in research_results)
        if len(research_results) != len(research_attempts):
            # 失败调用可能已经消费模型，但未交回计数；不能将未知成本写成零。
            result["calls"] = None
            result["status"] = "needs_review"
            result["unobserved_failed_runs"] = len(research_attempts) - len(research_results)
        elif result.get("calls") != observed_calls or not 0 <= observed_calls <= 24:
            raise ValueError("管线总calls必须等于worker与汇总的实际累计数，且不超过24")
        if result.get("status") == "reported" and not grades[0]["passed"]:
            result["status"] = "needs_review"
        return {
            **result,
            "component_calls": component_calls,
            "research_attempts": len(research_attempts),
            "finished_research_calls": [row["calls"] for row in research_results],
            "observed_calls": observed_calls,
            "model_call_bound": 24,
        }

    async def tracked_handle(job_id: str, question: str) -> dict:
        current = asyncio.current_task()
        assert current is not None
        with lock, connect() as db:
            row = db.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row["status"] in {"cancelled", "cancelling"}:
                raise asyncio.CancelledError
            active[job_id] = (asyncio.get_running_loop(), current)
        try:
            async with asyncio.timeout(300):
                return await handle(job_id, question)
        finally:
            with lock:
                active.pop(job_id, None)

    def execute(job_id: str) -> None:
        with lock, connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row["status"] != "queued":
                return
            if row["attempts"] >= 2:
                db.execute("UPDATE jobs SET status='failed' WHERE id=?", (job_id,))
                return
            db.execute(
                "UPDATE jobs SET status='running', attempts=attempts+1 WHERE id=?", (job_id,)
            )
        try:
            if row["input_sha"] != input_fingerprint(row["question"]):
                raise ValueError("任务提交后的问题或来源身份改变，请创建新任务")
            # 独立服务器工作线程中创建事件循环，不在Notebook现有循环中嵌套。
            result = asyncio.run(tracked_handle(job_id, row["question"]))
            if result["status"] not in {"reported", "needs_evidence", "needs_review"}:
                raise ValueError("研究器没有返回受支持的明确终态")
            status = "complete" if result["status"] == "reported" else result["status"]
        except asyncio.CancelledError:
            status = "cancelled"
            result = {"status": "cancelled", "answer": "这项咨询已停止，尚未完成的部分不再继续。"}
        except Exception as error:
            status = "failed"
            result = {
                "error_type": type(error).__name__,
                "hint": "请检查本人导出、来源登记、模型连接或任务身份；失败不会伪报完成",
            }
        with lock, connect() as db:
            current = db.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
            if current["status"] in {"cancelled", "cancelling"}:
                status = "cancelled"
                result = {"status": "cancelled", "answer": "这项咨询已停止，未登记为完成。"}
            db.execute(
                "UPDATE jobs SET status=?, result=? WHERE id=?",
                (status, json.dumps(result, ensure_ascii=False), job_id),
            )
        lab.save_json(run / (job_id + "-result.json"), result)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *values: object) -> None:
            return  # 本地请求日志不打印问题、请求头或凭证；进度保存在任务记录。

        def respond(self, code: int, data: dict) -> None:
            raw = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path == "/health":
                self.respond(200, {"ok": True})
                return
            if not self.path.startswith("/jobs/"):
                self.respond(404, {"error": "路径不存在"})
                return
            job_id = self.path.removeprefix("/jobs/")
            with connect() as db:
                row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None:
                self.respond(404, {"error": "任务不存在"})
                return
            data = dict(row)
            data["events"] = json.loads(data["events"])
            data["result"] = json.loads(data["result"]) if data["result"] else None
            self.respond(200, data)

        def do_POST(self) -> None:
            if self.path.startswith("/jobs/") and self.path.endswith("/cancel"):
                job_id = self.path.removeprefix("/jobs/").removesuffix("/cancel")
                with lock, connect() as db:
                    row = db.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
                    if row is None:
                        self.respond(404, {"error": "任务不存在"})
                        return
                    if row["status"] not in {"queued", "running", "cancelling", "cancelled"}:
                        self.respond(409, {"error": "任务已有终态，不能取消已经完成的工作"})
                        return
                    cancel_status = (
                        "cancelling" if row["status"] in {"running", "cancelling"} else "cancelled"
                    )
                    db.execute("UPDATE jobs SET status=? WHERE id=?", (cancel_status, job_id))
                    target = active.get(job_id)
                    if target is not None:
                        target[0].call_soon_threadsafe(target[1].cancel)
                emit(job_id, {"stage": "cancel_requested"})
                self.respond(200, {"job_id": job_id, "status": cancel_status})
                return
            if self.path != "/jobs":
                self.respond(404, {"error": "路径不存在"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 6000:
                    raise ValueError("请求过大或为空")
                payload = json.loads(self.rfile.read(size))
                question = payload["question"]
                if (
                    set(payload) != {"question"}
                    or not isinstance(question, str)
                    or not question.strip()
                    or len(question) > 1200
                ):
                    raise ValueError("只接受1至1200字符的question")
            except (ValueError, KeyError, TypeError):
                self.respond(400, {"error": "需要合法的question字符串"})
                return
            job_id = uuid4().hex
            try:
                fingerprint = input_fingerprint(question)
            except OSError:
                self.respond(409, {"error": "研究来源尚未准备，不能创建没有输入身份的任务"})
                return
            with connect() as db:
                db.execute(
                    "INSERT INTO jobs VALUES (?,?,'queued',NULL,'[]',0,?)",
                    (job_id, question, fingerprint),
                )
            self.respond(202, {"job_id": job_id, "status": "queued"})
            if not args.hold:
                pool.submit(execute, job_id)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    (run / "ready.json").write_text(
        json.dumps({"url": f"http://127.0.0.1:{server.server_port}"}), encoding="utf-8"
    )
    if not args.hold:
        with connect() as db:
            queued = db.execute("SELECT id FROM jobs WHERE status='queued'").fetchall()
        for row in queued:
            pool.submit(execute, row["id"])
    try:
        server.serve_forever()
    finally:
        server.server_close()
        pool.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()
