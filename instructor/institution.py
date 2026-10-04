"""实训业务环境：真实SQLite、身份边界、版本与事务，不包含学生Agent算法。"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class BoundaryError(ValueError):
    """公开业务错误，保留类别而不暴露凭据。"""


class ScopeDenied(BoundaryError):
    """本次身份缺少访问范围。"""


class VersionConflict(BoundaryError):
    """并发或恢复使用了旧输入版本。"""


@dataclass(frozen=True)
class Principal:
    """由环境确定的可信身份；请求正文不能修改它。"""

    tenant: str
    user: str
    scopes: frozenset[str]


class Institution:
    """机构知识服务的可读业务设施，所有写入限定在本次run目录。"""

    def __init__(self, root: Path, run_dir: Path) -> None:
        self.root, self.run_dir = root.resolve(), run_dir.resolve()
        if not self.run_dir.is_relative_to(self.root / "outputs"):
            raise ValueError("实训数据只能保存到课程outputs")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.database = self.run_dir / "institution.sqlite3"
        self.trace_lock = threading.Lock()
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                  id TEXT PRIMARY KEY,tenant TEXT,text TEXT,title TEXT,
                  version INTEGER,sha TEXT,active INTEGER);
                CREATE TABLE IF NOT EXISTS approvals (
                  token_sha TEXT PRIMARY KEY,tenant TEXT,document_id TEXT,
                  version INTEGER,expires REAL,used INTEGER);
                CREATE TABLE IF NOT EXISTS publications (
                  receipt TEXT PRIMARY KEY,tenant TEXT,document_id TEXT,
                  version INTEGER,input_sha TEXT,
                  idempotency_key TEXT UNIQUE,created REAL);
                CREATE TABLE IF NOT EXISTS preferences (
                  tenant TEXT,user TEXT,key TEXT,value TEXT,version INTEGER,consent INTEGER,
                  withdrawn INTEGER,expires REAL,PRIMARY KEY(tenant,user,key,version));
            """)
            corpus = json.loads((self.root / "world/institution/corpus.json").read_text())
            for row in corpus["documents"]:
                db.execute(
                    "INSERT OR IGNORE INTO documents VALUES (?,?,?,?,?,?,1)",
                    (
                        row["id"],
                        row["tenant"],
                        row["text"],
                        row["title"],
                        row["version"],
                        hashlib.sha256(row["text"].encode()).hexdigest(),
                    ),
                )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """建立事务连接，退出时提交或回滚并明确关闭。"""
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def trace(self, operation: str, status: str, **facts: Any) -> None:
        """记录实际公开业务事件，不保存请求头或批准token。"""
        row = {
            "event_id": uuid.uuid4().hex,
            "operation": operation,
            "status": status,
            "at": time.time(),
            **facts,
        }
        if any(key.lower() in {"authorization", "token", "api_key", "headers"} for key in row):
            raise ValueError("业务trace不接受凭据字段")
        with (
            self.trace_lock,
            (self.run_dir / "business-events.jsonl").open("a", encoding="utf-8") as out,
        ):
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    def document(self, principal: Principal, document_id: str) -> dict[str, Any]:
        """取得当前身份可访问的完整原文。

        Args:
            principal: 服务确定的身份；document_id: 当前资料ID。
        Returns:
            原文、版本、内容SHA与作用域。
        Raises:
            ScopeDenied: 越界；KeyError: 无当前资料。
        """
        if "doc:read" not in principal.scopes:
            raise ScopeDenied("这把钥匙还不能取资料")
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM documents WHERE id=? AND active=1", (document_id,)
            ).fetchone()
        if "doc:read" not in principal.scopes or row is None or row["tenant"] != principal.tenant:
            self.trace("document.read", "denied", tenant=principal.tenant, document_id=document_id)
            if row is None:
                raise KeyError("手头目录没有这份当前资料")
            raise ScopeDenied("这份资料不在本次分馆范围，请找林禾确认")
        self.trace(
            "document.read",
            "returned",
            tenant=principal.tenant,
            document_id=document_id,
            version=row["version"],
            source_sha=row["sha"],
        )
        return dict(row)

    def visible_documents(self, principal: Principal) -> list[dict[str, Any]]:
        """只取得可信分馆的当前候选；不做排名或生成。"""
        if "doc:read" not in principal.scopes:
            raise ScopeDenied("这把钥匙还不能取资料")
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM documents WHERE tenant=? AND active=1 ORDER BY id",
                (principal.tenant,),
            ).fetchall()
        documents = [dict(row) for row in rows]
        self.trace(
            "documents.list",
            "returned",
            tenant=principal.tenant,
            documents=[{"id": d["id"], "version": d["version"]} for d in documents],
        )
        return documents

    def update_document(
        self, principal: Principal, document_id: str, text: str, expected_version: int
    ) -> dict[str, Any]:
        """在当前版本匹配时更新实训原文；并发冲突不覆盖。

        Args:
            principal: 可信编辑身份；document_id/text: 目标与内容。
            expected_version: 读取时版本。
        Returns:
            新版本与当前SHA。
        Raises:
            ScopeDenied: 未获编辑范围；VersionConflict: 已变化。
        """
        if "doc:edit" not in principal.scopes:
            raise ScopeDenied("本次尚未允许修改原文")
        sha = hashlib.sha256(text.encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute(
                "UPDATE documents SET text=?,sha=?,version=version+1 "
                "WHERE id=? AND tenant=? AND version=?",
                (text, sha, document_id, principal.tenant, expected_version),
            ).rowcount
            if changed != 1:
                raise VersionConflict("资料已被改版，请先重新读取")
        self.trace(
            "document.update",
            "committed",
            document_id=document_id,
            version=expected_version + 1,
            source_sha=sha,
        )
        return {"id": document_id, "version": expected_version + 1, "sha": sha}

    def retire_document(
        self, principal: Principal, document_id: str, expected_version: int
    ) -> None:
        """按当前版本撤下实训资料，旧索引仍需调用者失效处理。"""
        if "doc:edit" not in principal.scopes:
            raise ScopeDenied("这次尚未允许撤下资料")
        with self.connect() as db:
            changed = db.execute(
                "UPDATE documents SET active=0,version=version+1 "
                "WHERE id=? AND tenant=? AND version=?",
                (document_id, principal.tenant, expected_version),
            ).rowcount
            if changed != 1:
                raise VersionConflict("撤下的资料版本已改变")
        self.trace(
            "document.retire", "committed", document_id=document_id, version=expected_version + 1
        )

    def approve(self, principal: Principal, document_id: str, version: int) -> str:
        """由林禾的可信身份批准指定资料版本，返回不进日志的短时凭据。"""
        if "notice:approve" not in principal.scopes:
            raise ScopeDenied("需要林禾确认这次内容")
        current = self.document(principal, document_id)
        if current["version"] != version:
            raise VersionConflict("批准要对应当前资料版本")
        token = uuid.uuid4().hex
        with self.connect() as db:
            db.execute(
                "INSERT INTO approvals VALUES (?,?,?,?,?,0)",
                (
                    hashlib.sha256(token.encode()).hexdigest(),
                    principal.tenant,
                    document_id,
                    version,
                    time.time() + 120,
                ),
            )
        self.trace("notice.approve", "confirmed", document_id=document_id, version=version)
        return token

    def publish(
        self,
        principal: Principal,
        document_id: str,
        version: int,
        idempotency_key: str,
        approval: str,
    ) -> dict[str, Any]:
        """在同一事务中检查批准、登记幂等键并保存实际发布。

        Args:
            principal: 可信发布身份；document_id/version: 当前版本；idempotency_key: 绑定输入的键。
            approval: 林禾已发出的批准凭据，参数自称approved不替代它。
        Returns:
            实际receipt及是否复用旧回执，不伪造新发布。
        Raises:
            ScopeDenied: 缺权限/批准；VersionConflict: 同键异输入或旧版本。
        """
        if "notice:publish" not in principal.scopes or not idempotency_key:
            raise ScopeDenied("这次尚未允许贴公告")
        fingerprint = hashlib.sha256(
            json.dumps([principal.tenant, document_id, version]).encode()
        ).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT * FROM publications WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
            if old:
                if old["input_sha"] != fingerprint:
                    raise VersionConflict("这张登记键已属于另一份输入，不能覆盖")
                self.trace(
                    "notice.publish", "reused", receipt=old["receipt"], input_sha=fingerprint
                )
                return {**dict(old), "reused": True}
            approved = db.execute(
                "SELECT * FROM approvals WHERE token_sha=?",
                (hashlib.sha256(approval.encode()).hexdigest(),),
            ).fetchone()
            current = db.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
            if (
                not approved
                or approved["used"]
                or approved["expires"] < time.time()
                or approved["tenant"] != principal.tenant
                or approved["document_id"] != document_id
                or approved["version"] != version
            ):
                raise ScopeDenied("还没有这份当前内容的有效批准，请找林禾确认")
            if (
                not current
                or not current["active"]
                or current["version"] != version
                or current["tenant"] != principal.tenant
            ):
                raise VersionConflict("内容已改变，旧批准不能继续用")
            receipt = uuid.uuid4().hex
            db.execute(
                "INSERT INTO publications VALUES (?,?,?,?,?,?,?)",
                (
                    receipt,
                    principal.tenant,
                    document_id,
                    version,
                    fingerprint,
                    idempotency_key,
                    time.time(),
                ),
            )
            db.execute("UPDATE approvals SET used=1 WHERE token_sha=?", (approved["token_sha"],))
        self.trace(
            "notice.publish",
            "committed",
            document_id=document_id,
            version=version,
            receipt=receipt,
            input_sha=fingerprint,
        )
        return {
            "receipt": receipt,
            "tenant": principal.tenant,
            "document_id": document_id,
            "version": version,
            "input_sha": fingerprint,
            "idempotency_key": idempotency_key,
            "reused": False,
        }

    def publication_count(self) -> int:
        """读取真实已提交发布条数。"""
        with self.connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM publications").fetchone()[0])

    def write_preference(
        self,
        principal: Principal,
        key: str,
        value: str,
        expected_version: int,
        consent: bool,
        expires: float,
        withdrawn: bool = False,
    ) -> dict[str, Any]:
        """按可信用户和当前版本追加偏好，撤回也保留新版本。

        Args:
            principal: 可信本人身份；key/value: 偏好；expected_version: 当前版本，首次0。
            consent/expires/withdrawn: 人的明确输入与有效期。
        Returns:
            实际提交版本，不保存身份猜测。
        Raises:
            ScopeDenied: 未获本人写入；VersionConflict: 并发覆盖风险。
        """
        if "pref:write" not in principal.scopes:
            raise ScopeDenied("这次尚未允许更改读者偏好")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT MAX(version) FROM preferences WHERE tenant=? AND user=? AND key=?",
                (principal.tenant, principal.user, key),
            ).fetchone()
            if (row[0] or 0) != expected_version:
                raise VersionConflict("这项偏好已有新版本，请重新核对")
            version = expected_version + 1
            db.execute(
                "INSERT INTO preferences VALUES (?,?,?,?,?,?,?,?)",
                (
                    principal.tenant,
                    principal.user,
                    key,
                    value,
                    version,
                    int(consent),
                    int(withdrawn),
                    expires,
                ),
            )
        self.trace(
            "preference.write",
            "committed",
            tenant=principal.tenant,
            key=key,
            version=version,
            withdrawn=withdrawn,
        )
        return {"version": version, "withdrawn": withdrawn, "expires": expires}

    def current_preference(
        self, principal: Principal, key: str, now: float
    ) -> dict[str, Any] | None:
        """先定位最新版本，再核对同意、撤回和有效期，不复活旧记录。"""
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM preferences WHERE tenant=? AND user=? AND key=? "
                "ORDER BY version DESC LIMIT 1",
                (principal.tenant, principal.user, key),
            ).fetchone()
        valid = bool(row and row["consent"] and not row["withdrawn"] and row["expires"] > now)
        self.trace(
            "preference.read",
            "valid" if valid else "inactive",
            tenant=principal.tenant,
            key=key,
            version=row["version"] if row else None,
        )
        if not valid:
            return None
        return dict(row)


def reader_a() -> Principal:
    """取得教学环境中明确的匿名A身份，不由请求正文推导。"""
    return Principal("branch-a", "reader-a", frozenset({"doc:read", "pref:write"}))


def lin_he() -> Principal:
    """取得教学环境中的林禾权限；只用于公开虚构实训。"""
    return Principal(
        "branch-a",
        "lin-he",
        frozenset({"doc:read", "doc:edit", "notice:approve", "notice:publish"}),
    )
