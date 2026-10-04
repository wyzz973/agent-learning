"""真实本地HTTP故障设施；故障受控，正常answer回调可以调用当前真实模型。"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from collections.abc import Awaitable, Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from instructor.institution import Institution, Principal, ScopeDenied

AnswerCallback = Callable[[dict[str, Any]], Awaitable[str]]


async def await_callback(callback: AnswerCallback, payload: dict[str, Any]) -> str:
    """在本次服务事件循环中等待明确传入的真实回调。"""
    return await callback(payload)


class FaultHTTP:
    """提供可观察的HTTP响应、延迟与服务端执行账。

    正常回调真实调用模型时另行说明；bad_json/503/delay属于故障设施。
    """

    def __init__(self, institution: Institution, responder: AnswerCallback | None = None) -> None:
        self.institution, self.responder = institution, responder
        self.calls: list[dict[str, Any]] = []
        self.script: list[str] = []
        self.lock = threading.Lock()
        self.identities = {
            "Bearer classroom-a": Principal("branch-a", "reader-a", frozenset({"doc:read"})),
            "Bearer classroom-b": Principal("branch-b", "reader-b", frozenset({"doc:read"})),
        }
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path == "/health":
                    self.reply(200, {"status": "alive", "scope": "进程响应，不证明模型质量"})
                else:
                    self.reply(404, {"error": "没有这项接口"})

            def do_POST(self) -> None:
                principal = owner.identities.get(self.headers.get("Authorization", ""))
                with owner.lock:
                    mode = owner.script.pop(0) if principal and owner.script else "ok"
                    row: dict[str, Any] = {
                        "attempt": len(owner.calls) + 1,
                        "mode": mode,
                        "tenant": principal.tenant if principal else None,
                        "started": time.time(),
                        "status": "running",
                    }
                    owner.calls.append(row)
                try:
                    self.connection.settimeout(3)
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 20000:
                        row["status"] = "invalid_input"
                        self.reply(413, {"error": "问题纸大小超出这次入口范围"})
                        return
                    # 先收完有界请求体，避免关闭连接时未读数据使客户端收不到401。
                    raw_body = self.rfile.read(size)
                    if principal is None:
                        row["status"] = "unauthorized"
                        self.reply(401, {"error": "请先确认本次读者身份"})
                        return
                    body = json.loads(raw_body)
                    if not isinstance(body, dict):
                        raise ValueError("问题纸需要对象字段")
                    if mode in {"503", "429"}:
                        row["status"] = "injected_failure"
                        self.reply(
                            int(mode), {"error": "资料柜这会儿忙，稍后再试。"}
                        )
                        return
                    if mode == "bad_json":
                        row["status"] = "malformed_response"
                        self.reply(200, b"{not-json")
                        return
                    if mode == "delay":
                        time.sleep(0.18)  # 真实HTTP等待；客户端可先超时，服务端随后继续。
                    document_id = body.get("document_id", "KB-A-01")
                    document = owner.institution.document(principal, document_id)
                    if self.path == "/answer" and owner.responder is not None:
                        text = asyncio.run(
                            await_callback(
                                owner.responder,
                                {"question": body.get("question", ""), "document": document},
                            )
                        )
                        payload: Any = {
                            "answer": text,
                            "source": document["id"],
                            "version": document["version"],
                        }
                    elif self.path == "/document":
                        payload = document
                    else:
                        self.reply(404, {"error": "没有这项已接入能力"})
                        row["status"] = "not_found"
                        return
                    row["status"] = "executed"
                    row["finished"] = time.time()
                    owner.institution.trace(
                        "http.request",
                        "executed",
                        tenant=principal.tenant,
                        attempt=row["attempt"],
                        mode=mode,
                    )
                    self.reply(200, payload)
                except ScopeDenied as error:
                    row["status"] = "denied"
                    self.reply(403, {"error": str(error), "type": type(error).__name__})
                except (KeyError, ValueError) as error:
                    row["status"] = "invalid_input"
                    self.reply(400, {"error": str(error), "type": type(error).__name__})
                except Exception as error:
                    row["status"] = "failed"
                    self.reply(
                        500,
                        {
                            "error": "本次办理没有完成，请核对公开错误类别",
                            "type": type(error).__name__,
                        },
                    )

            def reply(self, status: int, payload: Any) -> None:
                data = (
                    payload
                    if isinstance(payload, bytes)
                    else json.dumps(payload, ensure_ascii=False).encode()
                )
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    if status == 429:
                        self.send_header("Retry-After", "0")  # 本地实训，不代表提供方真实限流值。
                    self.end_headers()
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # 服务端已记录执行；连接断开不反过来伪造未执行。

            def log_message(self, *args: Any) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = False
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.url = "http://127.0.0.1:" + str(self.server.server_port)

    def start(self) -> FaultHTTP:
        """启动独立本地服务；调用者finally中close。"""
        self.thread.start()
        return self

    def close(self) -> None:
        """等待HTTP线程和已开始的请求退出，不把连接断开当任务回滚。"""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
