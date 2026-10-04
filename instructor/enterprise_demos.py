"""各模块的完整教师实训步骤；编排器将源码原位放入Notebook，不用于学生兜底。"""

import ast
from pathlib import Path
from typing import Any

import nbformat

# 保存完整教学代码模板，执行格另行编译并校验长度。
# ruff: noqa: E501

SETUP = """import uuid
import httpx
import time
from instructor.institution import Institution, ScopeDenied, VersionConflict, reader_a, lin_he
from instructor.institution_http import FaultHTTP
ENTERPRISE_RUN = ROOT / 'outputs/enterprise' / TASK_ID / uuid.uuid4().hex[:12]
service = Institution(ROOT, ENTERPRISE_RUN)
principal = reader_a()
reviewer = lin_he()
enterprise_evidence = {}
print('本次独立业务环境：', ENTERPRISE_RUN)
print('SQLite/HTTP为真实本地设施；馆务语料虚构；故障注入单独标识。')"""

LIVE_SETUP = '''async def enterprise_live_answer(payload: dict) -> str:
    """实际模型只收到本次身份取得的原文，不接收请求头或凭据。
    Args:
        payload: 当前问题与已授权资料。
    Returns:
        当前模型的公开文字。
    Raises:
        模型或超时错误原样保留。
    """
    current_model, current_role = lab.configure(ROOT, TASK_ID)
    packet = {key: payload['document'][key] for key in ('id', 'tenant', 'version', 'sha', 'text')}
    return await lab.ask(current_model, current_role,
        '林禾请你根据手头这份资料回应访客：' + payload['question']
        + '\\n实际原文包：\\n' + json.dumps(packet, ensure_ascii=False)
        + '\\n答复里的出处用这次原文包实际的id，不借用旧公告编号。')'''

LIVE = {
    "M01": ("KB-A-01", "本周六什么时候开门和闭馆？没有说明的日期不要猜。"),
    "M02": ("KB-A-06", "草稿写好就能直接贴吗？请说清楚还需要什么。"),
    "M03": ("KB-A-07", "有检查点是否就能保证发布动作只做一次？"),
    "M04": ("KB-A-08", "最新偏好已经撤回，还能重新用旧偏好吗？"),
    "M05": ("KB-A-05", "资料更新后还能继续用旧片段与缓存吗？"),
    "M06": ("KB-A-11", "有一个研究单元失败，能说报告已经全面完成吗？"),
    "M07": ("KB-A-09", "问题纸里换一个分馆名，是否就可以读取对方资料？"),
    "M08": ("KB-A-12", "代码改过，能拿原来的绿色测试回执交付吗？"),
    "M09": ("KB-A-10", "我这边超时了，是否代表服务没执行？"),
    "M10": ("KB-A-06", "当前公告已修改，还能沿用旧批准发布吗？"),
}

COMMON_LIVE = """endpoint = FaultHTTP(service, enterprise_live_answer).start()
try:
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        response = await client.post(endpoint.url + '/answer',
            headers={'Authorization': 'Bearer classroom-a'},
            json={'question': ENTERPRISE_QUESTION, 'document_id': ENTERPRISE_DOCUMENT})
    response.raise_for_status()
    normal_result = response.json()
    print(normal_result)
    assert normal_result['source'] == ENTERPRISE_DOCUMENT
    assert '[' + ENTERPRISE_DOCUMENT + ']' in normal_result['answer'], '答复没有标出这次实际提供的编号'
    enterprise_evidence['real_model'] = normal_result
finally:
    endpoint.close()
lab.save_json(ENTERPRISE_RUN / 'evidence.json', enterprise_evidence)
print('保存实际数据与局限，不登记本人通关。')"""

DEMOS: dict[str, list[tuple[str, str]]] = {
    "M01": [
        (
            "enterprise-schema",
            """class InstitutionalCard(BaseModel):
    answer: str
    sources: list[str]
    uncertain: bool
try:
    InstitutionalCard(answer='一段文字', sources='KB-A-01', uncertain=False)
except Exception as error:
    print('错误在本地Schema层：', type(error).__name__)
    enterprise_evidence['schema_error'] = type(error).__name__
else:
    raise AssertionError('sources必须是列表，不能把字段名当类型验证')""",
        ),
        (
            "enterprise-bad-json",
            """endpoint = FaultHTTP(service).start()
endpoint.script = ['bad_json']
try:
    async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
        result = await client.post(endpoint.url + '/document',
            headers={'Authorization': 'Bearer classroom-a'}, json={'document_id': 'KB-A-01'})
    assert result.status_code == 200
    try:
        result.json()
    except ValueError as error:
        print('HTTP成功，正文解析失败：', type(error).__name__)
        enterprise_evidence['parse_error'] = {'http_status': 200, 'kind': type(error).__name__}
    else:
        raise AssertionError('这份受控坏正文不应被解析成成功对象')
finally:
    endpoint.close()""",
        ),
    ],
    "M02": [
        (
            "enterprise-idempotence",
            """version = service.document(reviewer, 'KB-A-06')['version']
approval = service.approve(reviewer, 'KB-A-06', version)
first = service.publish(reviewer, 'KB-A-06', version, 'publish-case-02', approval)
retry = service.publish(reviewer, 'KB-A-06', version, 'publish-case-02', approval)
assert first['receipt'] == retry['receipt'] and retry['reused']
assert service.publication_count() == 1
try:
    service.publish(reviewer, 'KB-A-01', version, 'publish-case-02', approval)
except VersionConflict:
    print('同键不同输入明确冲突，不覆盖原回执。')
else:
    raise AssertionError('幂等键不能被新输入借走')
enterprise_evidence['publication'] = {'receipt': first['receipt'], 'rows': 1, 'retry_reused': True}""",
        ),
        (
            "enterprise-denial",
            """before = service.publication_count()
try:
    service.publish(reviewer, 'KB-A-01', 1, 'forged-approval', 'approved=True')
except ScopeDenied:
    print('参数声称批准，服务没有接受它。')
else:
    raise AssertionError('字符串不能给自己本次批准')
assert service.publication_count() == before
try:
    service.document(principal, 'KB-B-01')
except ScopeDenied:
    print('另一分馆的相似资料没有进入观察。')
else:
    raise AssertionError('跨分馆读取必须拒绝')
enterprise_evidence['denials'] = {'forged_approval': True, 'cross_branch': True, 'writes_added': 0}""",
        ),
    ],
    "M03": [
        (
            "enterprise-worker-source",
            """from instructor.graph_crash_fixture import WORKER_SOURCE
worker_file = ENTERPRISE_RUN / 'checkpoint_worker.py'
worker_file.write_text(WORKER_SOURCE, encoding='utf-8')
from IPython.display import Code
display(Code(WORKER_SOURCE, language='python'))
print('完整可信教师进程源码；不生成或运行学生答案。')""",
        ),
        (
            "enterprise-restart",
            """import os
async def run_fixture_process(phase: str) -> dict:
    env = {'PATH': os.environ.get('PATH', ''), 'PYTHONPATH': str(ROOT), 'PYTHONIOENCODING': 'utf-8'}
    process = await asyncio.create_subprocess_exec(sys.executable, str(worker_file),
        str(ROOT), str(ENTERPRISE_RUN), phase, env=env,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        async with asyncio.timeout(30):
            stdout, stderr = await process.communicate()
    finally:
        if process.returncode is None:
            process.kill()
            async with asyncio.timeout(5):
                await process.communicate()
    if process.returncode != 0:
        raise RuntimeError('教师新进程失败：' + stderr.decode()[-300:])
    return json.loads(stdout.decode().splitlines()[-1])
first = await run_fixture_process('start')
second = await run_fixture_process('resume-confirmed')
assert first['pid'] != second['pid']
assert first['status'] == 'interrupted_by_failure' and second['status'] == 'resumed'
assert first['publications'] == second['publications'] == 1
print(first, second)
enterprise_evidence['process_restart'] = {'first': first, 'second': second}""",
        ),
    ],
    "M04": [
        (
            "enterprise-memory-conflict",
            """service.write_preference(principal, 'style', '简短', 0, True, 100)
snapshot = service.current_preference(principal, 'style', 20)
assert snapshot and snapshot['version'] == 1
service.write_preference(principal, 'style', '详细并附出处', 1, True, 100)
try:
    service.write_preference(principal, 'style', '另一项旧版本更正', 1, True, 100)
except VersionConflict:
    print('两个会话读同版本后，旧写入被拒绝。')
else:
    raise AssertionError('不能静默覆盖别人的新版本')
enterprise_evidence['memory_conflict'] = {'first_version': 1, 'current_version': 2}""",
        ),
        (
            "enterprise-memory-withdraw",
            """stale_cache = dict(service.current_preference(principal, 'style', 20))
service.write_preference(principal, 'style', '', 2, True, 100, withdrawn=True)
current = service.current_preference(principal, 'style', 20)
assert current is None
assert stale_cache['value'] == '详细并附出处'
foreign = type(principal)('branch-b', 'reader-b', principal.scopes)
assert service.current_preference(foreign, 'style', 20) is None
print('真实存储已撤回；坏缓存仍有旧值，不能把它继续送给模型。')
enterprise_evidence['withdrawal'] = {'store_current': None, 'stale_cache_version': 2,
                                   'foreign_current': None, 'clock_scope': '受控实训now=20'}""",
        ),
    ],
    "M05": [
        (
            "enterprise-rag-visible",
            """from instructor.retrieval_bridge import embed_current
docs = service.visible_documents(principal)
assert all(d['tenant'] == 'branch-a' for d in docs)
query = 'Branch A Saturday opening and closing schedule'
vectors = await asyncio.to_thread(embed_current, ROOT, [query, *[d['text'] for d in docs]])
def cosine_fixture(a: list[float], b: list[float]) -> float:
    numerator = sum(x*y for x, y in zip(a, b, strict=True))
    denominator = sum(x*x for x in a)**0.5 * sum(y*y for y in b)**0.5
    return numerator / denominator
ranked = sorted(zip(docs, vectors[1:], strict=True),
    key=lambda row: -cosine_fixture(vectors[0], row[1]))
selected = [row[0] for row in ranked[:3]]
print('实际向量召回：', [(d['id'], d['version']) for d in selected])
assert any(d['id'] == 'KB-A-01' for d in selected)
enterprise_evidence['retrieval'] = {'selected_ids': [d['id'] for d in selected],
    'dimensions': len(vectors[0]), 'scope': '真实英文向量，尚非完整本人RAG成绩'}""",
        ),
        (
            "enterprise-rag-refresh",
            """old_index_item = service.document(principal, 'KB-A-01')
changed = service.update_document(reviewer, 'KB-A-01',
    '[KB-A-01] Branch A opens this Saturday at 15:00 and closes at 19:00.', 1)
fresh = service.document(principal, 'KB-A-01')
assert old_index_item['sha'] != fresh['sha'] and fresh['version'] == 2
assert '14:00' in old_index_item['text'] and '15:00' in fresh['text']
service.retire_document(reviewer, 'KB-A-03', 1)
assert not any(d['id'] == 'KB-A-03' for d in service.visible_documents(principal))
print('源已改变，旧索引对象仍存在；调用者需要更新索引与缓存。')
enterprise_evidence['lifecycle'] = {'old_sha': old_index_item['sha'], 'new_sha': changed['sha'],
    'retired_absent': True, 'wrong_index_still_present': True}""",
        ),
    ],
    "M06": [
        (
            "enterprise-release-metrics",
            """trials = [{'ok': True, 'critical': False, 'latency_ms': 20+i} for i in range(19)]
trials.append({'ok': False, 'critical': True, 'latency_ms': 25, 'failure': 'cross_tenant_source'})
rate = sum(row['ok'] for row in trials) / len(trials)
critical = [row for row in trials if row['critical']]
decision = {'pass_rate': rate, 'release_allowed': not critical, 'critical_count': len(critical),
            'scope': '受控验收数据，数值不是模型真实性能或业务SLO'}
assert rate == 0.95 and not decision['release_allowed']
print(decision)
enterprise_evidence['quality_gate'] = decision""",
        ),
        (
            "enterprise-first-deviation",
            """events = [
    {'stage': 'fetch', 'ok': True, 'source_id': 'KB-A-01'},
    {'stage': 'context', 'source_ids': []},
    {'stage': 'answer', 'source_ids': ['KB-A-01']}]
first_bad = next(i for i, row in enumerate(events)
    if row['stage'] == 'context' and 'KB-A-01' not in row['source_ids'])
assert first_bad == 1
print('首个可证偏差在context，不能只把最后回答归因于模型。')
service.trace('evaluation.case', 'blocked', critical='cross_tenant_source', first_bad=first_bad)
enterprise_evidence['trace_diagnosis'] = {'event_index': first_bad, 'public_events': events}""",
        ),
    ],
    "M07": [
        (
            "enterprise-mcp-source",
            """from instructor.mcp_fixture import MCP_SOURCE
server_file = ENTERPRISE_RUN / 'branch_mcp.py'
server_file.write_text(MCP_SOURCE, encoding='utf-8')
from IPython.display import Code
display(Code(MCP_SOURCE, language='python'))""",
        ),
        (
            "enterprise-mcp-sessions",
            """from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
params = StdioServerParameters(command=sys.executable,
    args=[str(server_file), str(ROOT), str(ENTERPRISE_RUN)],
    env={'PYTHONPATH': str(ROOT), 'PYTHONIOENCODING': 'utf-8'})
async with asyncio.timeout(30):
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            good = await session.call_tool('read_branch_document', {'document_id': 'KB-A-01'})
            bad = await session.call_tool('read_branch_document', {'document_id': 'KB-B-01'})
            assert not good.isError and bad.isError
    try:
        await session.list_tools()
    except Exception as error:
        closed_error = type(error).__name__
    else:
        raise AssertionError('已经关闭的session不能继续使用')
print('实际协议与目录：', initialized.protocolVersion, [t.name for t in tools.tools])
print('业务拒绝isError与会话关闭错误：', bad.isError, closed_error)
enterprise_evidence['protocol'] = {'version': initialized.protocolVersion,
    'discovered': [t.name for t in tools.tools], 'business_denied': bad.isError,
    'closed_session_error': closed_error}""",
        ),
    ],
    "M08": [
        (
            "enterprise-workspace-identity",
            """import hashlib
fixture_root = ENTERPRISE_RUN / 'candidate-fixture'
fixture_root.mkdir()
protected = fixture_root / 'test_fixed.py'
candidate = fixture_root / 'component.py'
protected.write_text("assert True\\n", encoding='utf-8')
candidate.write_text("value = 'initial'\\n", encoding='utf-8')
before = hashlib.sha256(candidate.read_bytes()).hexdigest()
protected_before = hashlib.sha256(protected.read_bytes()).hexdigest()
passing_record = {'sha256': before, 'passed': True,
    'scope': '本条用于身份反例，未声称执行了这份文本测试'}
candidate.write_text("value = 'new candidate'\\n", encoding='utf-8')
current_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
assert current_sha != passing_record['sha256']
assert hashlib.sha256(protected.read_bytes()).hexdigest() == protected_before
print('旧证据不对应当前候选；这里只读SHA，不在宿主执行候选。')
enterprise_evidence['stale_test'] = {'before': before, 'current': current_sha,
                                   'old_proof_matches': False, 'protected_unchanged': True}""",
        ),
        (
            "enterprise-real-sandbox",
            """import sys
runtime_dir = ROOT / 'modules/08-coding-agent'
sys.path.insert(0, str(runtime_dir))
from fog_coding_runtime import CodingWorkspace
source = "def matching(a, b):\\n    return a == b\\n"
tests = "import unittest\\nfrom candidate import matching\\nclass Check(unittest.TestCase):\\n    def test_same(self): self.assertTrue(matching('v1','v1'))\\n    def test_different(self): self.assertFalse(matching('v1','v2'))\\n"
work = CodingWorkspace.create(ENTERPRISE_RUN, source, tests, 'production-proof')
assert not work.edit(source)['ok']
work.set_write_permission(True)
green = await work.run_tests()
assert green['ok'] and work.latest_verified()
work.edit("def matching(a, b):\\n    return True\\n")
assert not work.latest_verified()
failed = await work.run_tests()
assert not failed['ok']
work.edit(source)
final = await work.run_tests()
assert final['ok'] and final['source_sha'] == work.source_sha()
print('实际Docker：初版通过、变更后旧绿失效且失败、恢复后当前验证通过。')
enterprise_evidence['sandbox_boundary'] = {'candidate_executed_on_host': False,
    'initial_passed': green['ok'], 'changed_passed': failed['ok'],
    'final_passed': final['ok'], 'final_sha': final['source_sha']}""",
        ),
    ],
    "M09": [
        (
            "enterprise-http-deadline",
            """endpoint = FaultHTTP(service).start()
endpoint.script = ['delay']
try:
    async with httpx.AsyncClient(timeout=0.03, trust_env=False) as client:
        try:
            await client.post(endpoint.url + '/document',
                headers={'Authorization': 'Bearer classroom-a'}, json={'document_id': 'KB-A-01'})
        except httpx.TimeoutException as error:
            timeout_type = type(error).__name__
        else:
            raise AssertionError('真实延迟应晚于本次客户端deadline')
    await asyncio.sleep(0.25)
    assert endpoint.calls[0]['status'] == 'executed'
    print('客户端已超时，服务端仍完成读取：', timeout_type, endpoint.calls[0]['status'])
    enterprise_evidence['deadline'] = {'client': timeout_type, 'server': 'executed',
        'scope': '真实HTTP与受控延迟，不表示远端模型可被取消'}
finally:
    endpoint.close()""",
        ),
        (
            "enterprise-http-budget",
            """endpoint = FaultHTTP(service).start()
endpoint.script = ['503', 'ok']
try:
    async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
        statuses = []
        for attempt in range(2):
            response = await client.post(endpoint.url + '/document',
                headers={'Authorization': 'Bearer classroom-a'}, json={'document_id': 'KB-A-01'})
            statuses.append(response.status_code)
            if response.status_code == 200:
                break
    assert statuses == [503, 200] and len(endpoint.calls) == 2
    print('失败与成功都占一次HTTP尝试：', statuses)
    enterprise_evidence['attempts'] = {'statuses': statuses, 'attempts': 2,
        'scope': '故障由本地设施注入，真实模型调用在下一格单独发生'}
finally:
    endpoint.close()""",
        ),
    ],
    "M10": [
        (
            "enterprise-release-gate",
            """checks = [
    {'name': 'normal_answer', 'passed': True, 'critical': False},
    {'name': 'source_scope', 'passed': False, 'critical': True},
    {'name': 'current_sha', 'passed': True, 'critical': True}]
blocked = [c['name'] for c in checks if c['critical'] and not c['passed']]
release = {'status': 'blocked' if blocked else 'candidate', 'blocking': blocked,
           'scope': '受控发布门禁演练，非本人项目已经通过'}
assert release['status'] == 'blocked' and release['blocking'] == ['source_scope']
print(release)
enterprise_evidence['release_gate'] = release""",
        ),
        (
            "enterprise-version-conflict",
            """current = service.document(reviewer, 'KB-A-06')
approval = service.approve(reviewer, current['id'], current['version'])
service.update_document(reviewer, current['id'], current['text'] + '\\n新版要求重新确认。', current['version'])
try:
    service.publish(reviewer, current['id'], current['version'], 'release-10', approval)
except VersionConflict:
    print('批准后内容变化，实际服务阻止旧版发布。')
else:
    raise AssertionError('当前内容变化必须阻止使用旧批准')
assert service.publication_count() == 0
enterprise_evidence['old_approval_blocked'] = {'writes': 0, 'status': 'needs_review'}""",
        ),
    ],
}


def append_enterprise_demo(notebook_path: Path, module_id: str, handbook: str) -> None:
    """把完整教师步骤原位编入章末，不执行或补写学生函数。"""
    document = nbformat.read(notebook_path, as_version=4)
    desired: list[Any] = [
        nbformat.v4.new_markdown_cell(
            "## 模块生产实训 · 从机制走到真实边界\n\n"
            + handbook
            + "\n\n下面的SQLite、HTTP与协议操作实际发生；可控故障与正常真实模型请求分开记录。"
            "代码在当前页完整呈现，业务设施源见instructor/institution.py，不含本人Agent算法。",
            id="enterprise-lab-intro",
        )
    ]
    for cid, source in [
        ("enterprise-environment", SETUP),
        ("enterprise-live-callback", LIVE_SETUP),
        *DEMOS[module_id],
    ]:
        compile(source, str(notebook_path), "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        if len(source.splitlines()) > 40:
            raise ValueError(cid + "教师格超过40行")
        desired.append(nbformat.v4.new_code_cell(source, id=cid, metadata={"tags": ["demo"]}))
    document_id, question = LIVE[module_id]
    source = (
        f"ENTERPRISE_DOCUMENT = {document_id!r}\nENTERPRISE_QUESTION = {question!r}\n" + COMMON_LIVE
    )
    desired.append(
        nbformat.v4.new_code_cell(
            source, id="enterprise-live-roundtrip", metadata={"tags": ["demo"]}
        )
    )
    for new in desired:
        old = next((c for c in document.cells if c.id == new.id), None)
        if old is not None:
            old.source = new.source
    existing = {c.id for c in document.cells}
    fresh = [c for c in desired if c.id not in existing]
    insert_at = next(
        (i for i, c in enumerate(document.cells) if c.id == "owned-contract"), len(document.cells)
    )
    document.cells[insert_at:insert_at] = fresh
    nbformat.write(document, notebook_path)
