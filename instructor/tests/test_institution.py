"""验证真实业务环境的身份、事务、版本与HTTP歧义，不给学生算法解答。"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx
import pytest

from instructor.check import ROOT
from instructor.institution import Institution, ScopeDenied, VersionConflict, lin_he, reader_a
from instructor.institution_http import FaultHTTP


@pytest.fixture
def service() -> Institution:
    import uuid

    return Institution(ROOT, ROOT / "outputs/enterprise-unit-tests" / uuid.uuid4().hex)


def test_authorization_and_version_bound_approval(service: Institution) -> None:
    with pytest.raises(ScopeDenied):
        service.document(reader_a(), "KB-B-01")
    approval = service.approve(lin_he(), "KB-A-06", 1)
    service.update_document(lin_he(), "KB-A-06", "新版内容", 1)
    with pytest.raises(VersionConflict):
        service.publish(lin_he(), "KB-A-06", 1, "old-approval", approval)
    assert service.publication_count() == 0


def test_concurrent_duplicate_publication_commits_once(service: Institution) -> None:
    approval = service.approve(lin_he(), "KB-A-06", 1)

    def publish(_: int) -> dict[str, Any]:
        return service.publish(lin_he(), "KB-A-06", 1, "same-input-key", approval)

    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(publish, range(8)))
    assert service.publication_count() == 1
    assert len({r["receipt"] for r in receipts}) == 1
    assert sum(not r["reused"] for r in receipts) == 1
    with pytest.raises(VersionConflict):
        service.publish(lin_he(), "KB-A-01", 1, "same-input-key", approval)


def test_memory_cas_and_latest_withdrawal(service: Institution) -> None:
    service.write_preference(reader_a(), "style", "简短", 0, True, 100)
    service.write_preference(reader_a(), "style", "详细", 1, True, 100)
    with pytest.raises(VersionConflict):
        service.write_preference(reader_a(), "style", "过期写入", 1, True, 100)
    service.write_preference(reader_a(), "style", "", 2, True, 100, withdrawn=True)
    assert service.current_preference(reader_a(), "style", 20) is None


@pytest.mark.asyncio
async def test_real_http_timeout_does_not_undo_service_execution(service: Institution) -> None:
    endpoint = FaultHTTP(service).start()
    endpoint.script = ["delay"]
    try:
        async with httpx.AsyncClient(timeout=0.03, trust_env=False) as client:
            with pytest.raises(httpx.TimeoutException):
                await client.post(
                    endpoint.url + "/document",
                    headers={"Authorization": "Bearer classroom-a"},
                    json={"document_id": "KB-A-01", "tenant": "branch-b"},
                )
        await asyncio.sleep(0.25)
        assert endpoint.calls[0]["tenant"] == "branch-a"
        assert endpoint.calls[0]["status"] == "executed"
    finally:
        endpoint.close()


@pytest.mark.asyncio
async def test_http_auth_shape_and_controlled_errors(service: Institution) -> None:
    endpoint = FaultHTTP(service).start()
    endpoint.script = ["503", "bad_json", "ok"]
    try:
        async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
            denied = await client.post(endpoint.url + "/document", json={"document_id": "KB-A-01"})
            assert denied.status_code == 401
            headers = {"Authorization": "Bearer classroom-a"}
            unavailable = await client.post(
                endpoint.url + "/document", headers=headers, json={"document_id": "KB-A-01"}
            )
            malformed = await client.post(
                endpoint.url + "/document", headers=headers, json={"document_id": "KB-A-01"}
            )
            crossed = await client.post(
                endpoint.url + "/document",
                headers=headers,
                json={"document_id": "KB-B-01", "approved": True},
            )
        assert unavailable.status_code == 503 and malformed.status_code == 200
        with pytest.raises(ValueError):
            malformed.json()
        assert crossed.status_code == 403
        assert [r["status"] for r in endpoint.calls] == [
            "unauthorized",
            "injected_failure",
            "malformed_response",
            "denied",
        ]
    finally:
        endpoint.close()
