"""整理课程路线、规则与模块接待台；不运行本人答案或登记通关。"""

from __future__ import annotations

import ast
from typing import Any

import nbformat

from instructor.author_course import RECIPES, cell, write_json
from instructor.check import ROOT, load_catalog
from instructor.course_atlas import CONCEPTS, MODULE_CONCEPTS
from instructor.extension_specs import LESSONS

# 保留教学正文和代码模板原段落。
# ruff: noqa: E501

LIVE_EXTRAS = {
    "M02-T04": [
        (
            "teacher-middleware",
            '''from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
@wrap_tool_call
async def guard_demo(request, handler):
    """教师工具边界只允许实际登记的座位读取。"""
    if request.tool_call['name'] != 'read_seat_card':
        return ToolMessage(content='这把钥匙不能办理这项操作，请找林禾确认。',
                           tool_call_id=request.tool_call['id'])
    return await handler(request)
guarded_agent = create_agent(model, [read_seat_card], system_prompt=SYSTEM_PROMPT,
    middleware=[guard_demo, ModelCallLimitMiddleware(run_limit=3)])
async with asyncio.timeout(60):
    guarded_state = await guarded_agent.ainvoke({'messages': [HumanMessage('请先取座位卡再答复今天有几个座位。')]})
print(guarded_state['messages'][-1].text)
save_public('teacher-middleware.json', {'answer': guarded_state['messages'][-1].text,
                                     'scope': '真实create_agent工具钩子'})''',
        ),
    ],
    "M03-T04": [
        (
            "teacher-subgraph",
            """outer = StateGraph(ShelfState)
outer.add_node('shelves', demo_graph)
outer.add_edge(START, 'shelves')
outer.add_edge('shelves', END)
subgraph_result = await outer.compile().ainvoke({'receipts': []})
print('同一真实子图接入外层后：', subgraph_result)
assert set(subgraph_result['receipts']) == set(demo_state['receipts'])""",
        ),
    ],
    "M05-T05": [
        (
            "teacher-bm25",
            '''import math
from collections import Counter
def bm25_demo(query: str, texts: list[str]) -> list[float]:
    """计算教师英文座位资料的真实关键词分数。
    Args:
        query: 空格分词查询；texts: 受控英文资料。
    Returns:
        与资料同序的BM25分数。
    Raises:
        无；空资料返回空列表。
    """
    docs = [text.lower().split() for text in texts]
    terms = set(query.lower().split())
    average = sum(map(len, docs)) / len(docs) if docs else 1
    scores = []
    for doc in docs:
        score = 0.0
        counts = Counter(doc)
        for term in terms:
            df = sum(term in other for other in docs)
            idf = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
            tf = counts[term]
            denom = tf + 1.2 * (1 - 0.75 + 0.75 * len(doc) / (average or 1))
            score += idf * tf * 2.2 / denom if denom else 0
        scores.append(score)
    return scores''',
        ),
        (
            "teacher-bm25-observe",
            """texts = ['seat reservation deadline saturday', 'seat book shelf', 'lamp repair guide']
scores = bm25_demo('reservation deadline', texts)
print(list(zip(texts, scores, strict=True)))
assert scores[0] > scores[1] and scores[1] == scores[2]
print('真实词频公式；这份小语料不证明所有语言或生产检索效果。')""",
        ),
        (
            "teacher-mmr",
            '''def mmr_demo(relevance: list[float], similarities: list[list[float]], k: int) -> list[int]:
    """用受控相似度矩阵演示相关性与重复的取舍。
    Args:
        relevance: 与问题相关度；similarities: 候选两两相似度；k: 选出数。
    Returns:
        选中下标，矩阵是受控数据而非本次真实embedding。
    Raises:
        无。
    """
    selected = []
    remaining = set(range(len(relevance)))
    while remaining and len(selected) < k:
        def score(index: int) -> float:
            duplicate = max((similarities[index][j] for j in selected), default=0)
            return 0.5 * relevance[index] - 0.5 * duplicate
        best = max(sorted(remaining), key=score)
        selected.append(best)
        remaining.remove(best)
    return selected
picked = mmr_demo([1.0, 0.95, 0.8], [[1, .99, .1], [.99, 1, .1], [.1, .1, 1]], 2)
print('相关但重复的第2页被让开：', picked)
assert picked == [0, 2]''',
        ),
    ],
    "M07-T05": [
        (
            "teacher-mcp-server",
            '''server_file = OUTPUT_DIR / 'teacher_resources.py'
server_source = """from mcp.server.fastmcp import FastMCP
server = FastMCP('雾岛教师资源窗')
@server.resource('fog://seat/current')
def seat_notice() -> str:
    return '[SEAT-DEMO] 本周六开放两个座位。'
@server.prompt()
def reader_question(day: str) -> str:
    return '林禾请问读者：你想了解' + day + '哪项馆务？'
if __name__ == '__main__':
    server.run(transport='stdio')
"""
server_file.write_text(server_source, encoding='utf-8')
print('完整教师服务源码：\\n', server_source)''',
        ),
        (
            "teacher-mcp-client",
            """from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
params = StdioServerParameters(command=sys.executable, args=[str(server_file)])
async with asyncio.timeout(30):
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            resources = await session.list_resources()
            prompts = await session.list_prompts()
            resource = await session.read_resource('fog://seat/current')
            chosen_prompt = await session.get_prompt('reader_question', arguments={'day': '周六'})
            resource_text = resource.contents[0].text
            prompt_text = chosen_prompt.messages[0].content.text
print('发现资源：', [str(r.uri) for r in resources.resources])
print('发现模板：', [p.name for p in prompts.prompts])
print('实际read/get：', resource_text, prompt_text)
assert '两个座位' in resource_text and '周六' in prompt_text
save_public('teacher-mcp-read-get.json', {'resource': resource_text, 'prompt': prompt_text})""",
        ),
    ],
    "M09-T02": [
        (
            "teacher-cache-live",
            """key = seat_cache_key('本周六几点闭馆？', NOTICE_B, 'current-prompt')
actual_cache = {}
actual_calls = 0
if key not in actual_cache:
    actual_calls += 1
    actual_cache[key] = await lab.ask(model, SYSTEM_PROMPT,
        '读者问本周六几点闭馆，依据本次公告：\\n' + NOTICE_B)
first_answer = actual_cache[key]
second_answer = actual_cache[key]
assert first_answer == second_answer and actual_calls == 1
save_public('teacher-cache-live.json', {'answer': second_answer, 'actual_calls': actual_calls,
                                     'cache_hit_second': True, 'key': key})""",
        ),
    ],
    "M09-T03": [
        (
            "teacher-interface-live",
            """class ContractProbe(BaseModel):
    answer: str = Field(description='给读者的自然答复')
    source_ids: list[str] = Field(description='实际公告编号')
probe = model.with_structured_output(ContractProbe, method='json_mode')
async with asyncio.timeout(30):
    result = await probe.ainvoke([SystemMessage(SYSTEM_PROMPT),
        HumanMessage('按JSON answer/source_ids答复：本周六几点闭馆？\\n' + NOTICE_B)])
print(result.model_dump())
assert 'NOTICE-B' in result.source_ids
save_public('teacher-interface-probe.json', {'structured': True, 'result': result.model_dump(),
                                         'tools': '另见M02实际轨迹', 'stream': '另见M09-T01'})""",
        ),
    ],
    "M09-T04": [
        (
            "teacher-http-server",
            '''import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class LocalGate(BaseHTTPRequestHandler):
    """只用于本地HTTP边界演练，不是本人服务实现。"""
    def do_GET(self) -> None:
        supplied = self.headers.get('Authorization', '')
        allowed = check_demo_token(supplied, 'Bearer local-example')
        payload = {'allowed': allowed, 'status': 'ready' if allowed else 'unauthorized'}
        self.send_response(200 if allowed else 401)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
    def log_message(self, *args: Any) -> None:
        return  # 教师设施不输出请求头或凭据。
server = ThreadingHTTPServer(('127.0.0.1', 0), LocalGate)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()
url = 'http://127.0.0.1:' + str(server.server_port) + '/' ''',
        ),
        (
            "teacher-http-client",
            """import httpx
try:
    async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
        anonymous_response = await client.get(url)
        identified_response = await client.get(url, headers={'Authorization': 'Bearer local-example'})
    print('实际HTTP状态：', anonymous_response.status_code, identified_response.status_code)
    assert anonymous_response.status_code == 401 and identified_response.status_code == 200
    save_public('teacher-http-boundary.json', {'anonymous': 401, 'identified': 200,
                                            'scope': '真实回环HTTP，不证明本人研究管线'})
finally:
    server.shutdown()
    server.server_close()
    server_thread.join(timeout=5)""",
        ),
    ],
}


def update_cell(document: Any, item: Any, before: str | None = None) -> None:
    existing = next((c for c in document.cells if c.id == item.id), None)
    if existing is None:
        index = next(
            (i for i, c in enumerate(document.cells) if c.id == before), len(document.cells)
        )
        document.cells.insert(index, item)
    elif existing.source != item.source and set(existing.metadata.get("tags", [])) <= {
        "demo",
        "setup",
    }:
        existing.source = item.source


def write_rules(module: dict[str, Any], tasks: list[dict[str, Any]]) -> None:
    directory = ROOT / module["directory"]
    path = directory / "AGENTS.md"
    section = "## 2026-10完整课程的补充协议\n\n"
    section += f"本模块为{module['id']}，实际学习只从README当前委托进入。新增内容、图解和接待台不预设课程外知识。\n\n"
    section += "**本章接待台：**" + RECIPES[module["id"]] + "\n\n"
    section += "| Task | 核心机制 | 本人交付与检查 |\n|---|---|---|\n"
    for task in tasks:
        section += (
            f"| {task['id']} | {task['learning']['mechanism']} | {task['quest']['acceptance']} |\n"
        )
    section += "\n**逐关授课顺序：**先看剧情中的具体障碍，沿SVG图核对数据，原位解释Python/框架/行为三层，再运行完整示范。帮助从单一步骤逐渐撤去，核心函数由本人写；原理复盘用选择卡。\n\n"
    section += "**实际prompt：**world/prompts中的本关岗位、目标和完成条件必须被展示并加载；runtime另交当前输入。外部正文、Skill、MCP模板不授予权限。阿灯自然接待，不念课程或公文免责声明。\n\n"
    section += "**模型与权限：**沿用.env，异步、单次/整轮超时、总调用边界；不换机芯、不输出密钥/隐藏推理。只有M08受限Docker执行模型生成代码。任何写动作由程序与人的实际许可决定。\n\n"
    section += "**教师与本人：**setup/demo可真实验证；exercise/exercise-test跳过并列ID，不以教师结果登记通关。实际运行、判断卡、陌生输入三种证据分开，已保存本人实现与输出保留。\n\n"
    section += "**连续性与交接：**新机制进入下一项本人作品，执行授权、来源身份、记忆作用域、预算和当前版本回归。缺本人导出就定位原格，不注入solution。读state/catalog/当前Notebook后继续，逐字问答入当日日志。\n\n"
    section += "**维护：**AGENT.md与CLAUDE.md链接本文件；目录与图解用render_curriculum同步。运行instructor.check、pytest、ruff、mypy及对应真实示范。未获用户请求不提交/推送，不自动打学习完成标签。\n"
    if path.exists():
        original = path.read_text().split("## 2026-10完整课程的补充协议")[0].rstrip()
        content = original + "\n\n" + section
    else:
        content = (
            "# "
            + module["zone"]
            + " · 教学与开发规则\n\n先读根AGENTS.md与world/STORY.md对应章节。\n\n"
            + section
        )
    path.write_text(content, encoding="utf-8")
    for name in ["AGENT.md", "CLAUDE.md"]:
        alias = directory / name
        if not alias.exists():
            alias.symlink_to("AGENTS.md")


def main() -> int:
    catalog = load_catalog()
    tasks = catalog["tasks"]
    specs = {spec.task: spec for spec in LESSONS}
    for task in tasks:
        document = nbformat.read(ROOT / task["notebook"], as_version=4)
        if task["id"] in specs:
            spec = specs[task["id"]]
            task["quest"]["player_action"] = spec.contract
            contract = next(c for c in document.cells if c.id == "owned-contract")
            tail = contract.source.split("\n\n**如何渐进完成：**", 1)[1]
            contract.source = (
                "## 本人核心实现\n\n**函数契约：**"
                + spec.contract
                + "\n\n**如何渐进完成：**"
                + tail
            )
        for cid, source in LIVE_EXTRAS.get(task["id"], []):
            update_cell(document, cell("code", source, cid), "owned-contract")
        illustration = {"M02": "agent-loop", "M04": "memory-layers", "M05": "rag-workflow"}.get(
            task["module"]
        )
        if illustration:
            update_cell(
                document,
                cell(
                    "markdown",
                    f"### 把这一章的层次摆开\n\n![{illustration}](../../assets/{illustration}.svg)\n\n这张图补充本关数据流；请在本页实际输入、观察、返回中核对对应位置。",
                    "chapter-layer-illustration",
                ),
                "python-before-code",
            )
        owned_funcs = []
        for c in document.cells:
            if c.cell_type == "code" and "exercise" in c.metadata.get("tags", []):
                for node in ast.parse(c.source).body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        owned_funcs.append(node.name)
        task["owned_symbols"] = owned_funcs
        task.setdefault(
            "pacing",
            {
                "sessions": 4 if task["module"] in {"M05", "M06", "M08"} else 3,
                "session_minutes": 60,
            },
        )
        nbformat.write(document, ROOT / task["notebook"])
    # 补齐M01公告卡与M02完整循环的本人导出，不运行或补写定义。
    config = "from pathlib import Path\nfrom typing import Any, Literal\nimport asyncio\nimport sys\nfrom langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage\nfrom pydantic import BaseModel, Field\nfrom langchain_core.tools import BaseTool\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / 'modules/05-deep-research'))\nfrom library_facilities import configure\n"
    additions = [
        (
            "M01-T02",
            ["learner-schema", "learner-answer-function"],
            ["NoticeAnswer", "answer_for_board"],
            "m01_board",
            config
            + "model, STORY_PROMPT = configure(ROOT, 'M01-T02')\n"
            + "SYSTEM_PROMPT = STORY_PROMPT\n"
            + "structured_model = model.model_copy()\n"
            + "structured_model.extra_body = dict(model.extra_body or {})\n"
            + "structured_model.extra_body['thinking'] = {'type': 'disabled'}\n",
        ),
        (
            "M02-T03",
            ["m02-t03-27"],
            ["run_with_recovery"],
            "m02_runner",
            config
            + "from project.m02_recovery import execute_calls_safely\nmodel, SYSTEM_PROMPT = configure(ROOT, 'M02-T03')\n",
        ),
    ]
    mcp_imports = (
        "from langchain.agents import create_agent\n"
        "from langchain.agents.middleware import ModelCallLimitMiddleware\n"
        "from langchain.messages import AnyMessage\n"
        "from mcp import ClientSession, StdioServerParameters\n"
        "from mcp.client.stdio import stdio_client\n"
        "from langchain_mcp_adapters.tools import load_mcp_tools\nimport yaml\n"
    )
    for tid, ids, names, target, facilities in [
        (
            "M07-T01",
            ["m07-t01-21"],
            ["ask_branch"],
            "m07_client",
            ["server_parameters", "tool_text", "public_trace"],
        ),
        (
            "M07-T02",
            ["m07-t02-17"],
            ["answer_using_method"],
            "m07_methods",
            ["discover_methods", "public_trace"],
        ),
        (
            "M07-T03",
            ["m07-t03-16", "m07-t03-17"],
            ["select_tool_names", "run_with_discovery"],
            "m07_discovery",
            ["public_trace"],
        ),
    ]:
        task = next(t for t in tasks if t["id"] == tid)
        original = nbformat.read(ROOT / task["notebook"], as_version=4)
        supplied = ""
        for c in original.cells:
            if c.cell_type != "code" or not set(c.metadata.get("tags", [])) & {"setup", "demo"}:
                continue
            for node in ast.parse(c.source).body:
                if isinstance(node, ast.ClassDef) or (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name in facilities
                ):
                    segment = ast.get_source_segment(c.source, node)
                    supplied += "# 本课已展示的设施：" + c.id + "\n" + str(segment) + "\n"
        additions.append(
            (
                tid,
                ids,
                names,
                target,
                config
                + mcp_imports
                + f"model, SYSTEM_PROMPT = configure(ROOT, {tid!r})\n"
                + supplied,
            )
        )
    for tid, ids, names, target, prelude in additions:
        task = next(t for t in tasks if t["id"] == tid)
        path = ROOT / task["notebook"]
        document = nbformat.read(path, as_version=4)
        source = (
            "from instructor.learner_exports import export_definitions\nprelude = "
            + repr(prelude)
            + "\nprint('导入与模型设施：\\n', prelude)\nexport_definitions(ROOT / "
            + repr(task["notebook"])
            + ", "
            + repr(ids)
            + ", "
            + repr(names)
            + ", ROOT / 'project/"
            + target
            + ".py', prelude)\n"
        )
        update_cell(
            document,
            cell(
                "markdown",
                "### 保存本人成果供后续模块使用\n\n先完成本页本人检查并保存Notebook，再运行下面导出格。这里只提取指定本人定义，导入设施在格中完整展示；缺实现或已有不同本人文件时明确拒绝。",
                "additional-owned-export-guide",
            ),
            "course-choice-intro",
        )
        update_cell(
            document,
            cell("code", source, "additional-owned-export", "exercise-test"),
            "course-choice-intro",
        )
        nbformat.write(document, path)
    for module in catalog["modules"]:
        group = [t for t in tasks if t["module"] == module["id"]]
        last = group[-1]
        document = nbformat.read(ROOT / last["notebook"], as_version=4)
        recipe = RECIPES[module["id"]]
        intro = "## 本章完整交互：把本人能力留在接待台\n\n" + recipe
        intro += "\n\n下面的界面由教师提供，你组织module_agent把已有本人组件接进来。每次从controls读取匿名身份、办理方式和一次性许可；模型不能改变这些控件。返回answer/evidence/artifacts/status，可加trace与memory；只链接真实outputs产物。先做一种正常办理，再补未完成/取消与陌生输入。\n\n"
        intro += "<details><summary>接线提示：先接一条箭头</summary>先确认原本人导出存在，选一次当前输入，实际调用一个已完成函数，把真实返回映射到界面字段。再逐一加权限、记忆、来源和预算；缺组件明确失败。不要重新实现一套教师agent或写死本题答复。</details>\n"
        update_cell(
            document, cell("markdown", intro, "module-workspace-contract"), "course-choice-intro"
        )
        stub = '''async def module_agent(question: str, selection: str | None, controls: dict[str, Any]) -> dict[str, Any]:
    """接到本章本人作品的自由办理入口。
    Args:
        question: 当前问题；selection: 当前依据；controls: 实际匿名身份/办理/一次性许可。
    Returns:
        answer/evidence/artifacts/status及可选公开trace/memory。
    Raises:
        NotImplementedError: 本人接线未完成；缺组件、模型和工具错误保留。
    """
    raise NotImplementedError("请按紧邻本章接线契约组织已有本人组件")'''
        update_cell(document, cell("code", stub, "module-agent", "exercise"), "course-choice-intro")
        binding = f"from instructor.course_workspace import show_module_workspace\nworkspace = show_module_workspace({module['id']!r}, module_agent, ROOT)\n"
        update_cell(
            document,
            cell("code", binding, "module-workspace-binding", "exercise-test"),
            "course-choice-intro",
        )
        nbformat.write(document, ROOT / last["notebook"])
        write_rules(module, group)
    # 生命周期与混合检索的显式衔接格；它们只调用本人机制，不填实现。
    m4 = next(t for t in tasks if t["id"] == "M04-T06")
    document = nbformat.read(ROOT / m4["notebook"], as_version=4)
    update_cell(
        document,
        cell(
            "markdown",
            "### 较新版本撤回，不复活较旧版本\n\n同key先定位最高版本，再检查它是否同意、未撤回、未到期。先过滤撤回记录再找最高版本，会把旧偏好重新带回来。`{**记录, 新键:新值}`复制字典并覆盖指定字段，不修改原对象。",
            "latest-memory-guide",
        ),
        "replay-guide",
    )
    update_cell(
        document,
        cell(
            "code",
            "retired_versions = [records[0], {**records[0], 'id': 'p3', 'version': 2, 'withdrawn': True}]\nassert select_memory(retired_versions, 'reader-a', 20) == [], '新版本撤回后不能复活旧偏好'\n",
            "owned-latest-withdrawal",
            "exercise-test",
        ),
        "replay-guide",
    )
    update_cell(
        document,
        cell(
            "markdown",
            "### 林禾的有效期提议\n\n原M04-T03数据库使用confirmed/active/updated_at，本关输入契约使用consent/withdrawn/expires_at。后续研究会明确转换这些字段，再调用本人select_memory。这里请你选择是否允许本课匿名读者A已确认的偏好在接下来一天使用；不选择或选择拒绝时，后续保持缺口，不默认同意。",
            "memory-policy-proposal",
        ),
        "owned-export",
    )
    update_cell(
        document,
        cell(
            "code",
            "import ipywidgets as widgets\npolicy_choice = widgets.ToggleButtons(\n    options=[('同意本课匿名偏好有效期一天', True), ('暂不使用这些偏好', False)],\n    value=None, description='你的决定')\ndisplay(policy_choice)\n",
            "memory-policy-choice",
            "exercise-test",
        ),
        "owned-export",
    )
    update_cell(
        document,
        cell(
            "code",
            "import time\nif policy_choice.value is None:\n    raise ValueError('请先在上面的按钮选择；模型不会替你确认')\npolicy = {'user_id': 'reader-a', 'approved': policy_choice.value,\n          'created_at': int(time.time()), 'ttl_seconds': 86400}\nlab.save_json(ROOT / 'project/artifacts/memory-policy.json', policy)\nprint('记录本次决定与有效期，不记录真实身份。')\n",
            "memory-policy-save",
            "exercise-test",
        ),
        "owned-export",
    )
    nbformat.write(document, ROOT / m4["notebook"])
    m5 = next(t for t in tasks if t["id"] == "M05-T01")
    document = nbformat.read(ROOT / m5["notebook"], as_version=4)
    update_cell(
        document,
        cell(
            "markdown",
            "### 值班室的政策现在进入简报\n\n先读取你在M04-T06亲自选择的有效期。confirmed映射为consent，active映射为未撤回，expiry来自那次明确决定；未知确认字段按未确认处理。下面转换格式的设施不筛选结果，筛选由本人的select_memory完成。它的返回值实际交给scope_request，不保存在旁边。",
            "memory-policy-handoff",
        ),
        "owned-live",
    )
    source = """import time
policy_path = ROOT / 'project/artifacts/memory-policy.json'
if not policy_path.is_file() or not (ROOT / 'project/m04_policy.py').is_file():
    raise FileNotFoundError('请完成M04-T06本人select_memory导出及有效期选择格')
from project.m04_policy import select_memory
policy = json.loads(policy_path.read_text())
if policy['user_id'] != 'reader-a':
    raise ValueError('记忆政策不属于本次匿名读者')
normalized = [{**row, 'id': 'reader-a:' + row['key'], 'user_id': 'reader-a',
    'consent': bool(row.get('confirmed', False)) and policy['approved'],
    'withdrawn': not bool(row.get('active', False)),
    'expires_at': policy['created_at'] + policy['ttl_seconds']} for row in preferences]
preferences = select_memory(normalized, 'reader-a', int(time.time()))
print('本人政策筛选后实际进入scope_request的偏好：', preferences)
"""
    update_cell(
        document, cell("code", source, "memory-policy-apply", "exercise-test"), "owned-live"
    )
    nbformat.write(document, ROOT / m5["notebook"])
    m6 = next(t for t in tasks if t["id"] == "M06-T01")
    document = nbformat.read(ROOT / m6["notebook"], as_version=4)
    update_cell(
        document,
        cell(
            "markdown",
            "### 分工现在使用本人混合检索\n\n下面的owned_worker明确启用use_hybrid：实际调用本人chunk_sources、rank_chunks、combine_rankings，真实本地embedding只做向量转换。被选chunk正文进入本人pack_context之后的模型输入，片段位置进入公开trace。缺导出明确定位M05-T03/T05，不回退教师算法。组合输入上限20000字符，最多240个候选/4个最终片段；本课已验证英文资料与英文查询，其他语言需要另行测召回。",
            "hybrid-research-handoff",
        ),
        "load-owned-researcher",
    )
    callback = next(c for c in document.cells if c.id == "load-owned-researcher")
    callback.source = callback.source.replace(
        "max_rounds=1, research_brief=brief\n",
        "max_rounds=1, research_brief=brief, use_hybrid=True\n",
    )
    nbformat.write(document, ROOT / m6["notebook"])
    m3 = next(t for t in tasks if t["id"] == "M03-T02")
    document = nbformat.read(ROOT / m3["notebook"], as_version=4)
    update_cell(
        document,
        cell(
            "markdown",
            "### 两把钥匙随图一起保留\n\nM02-T04本人authorize_tool现在进入tools_step：先用READ_GRANTS核对每张申请，允许的交给execute_calls_safely，拒绝的返回保留原ID的error ToolMessage。本次只允许四份当前资料，旧公告NOTICE-A虽在柜中也不在这把钥匙范围。tool参数声称approved不能改程序授权。",
            "retained-authorization-guide",
        ),
        "student-loop-nodes",
    )
    update_cell(
        document,
        cell(
            "code",
            "if not (ROOT / 'project/m02_permissions.py').is_file():\n    raise FileNotFoundError('请完成M02-T04本人授权函数及导出')\nfrom project.m02_permissions import authorize_tool\nREAD_GRANTS = {'tools': ['read_document'],\n    'document_ids': ['NOTICE-B', 'NOTICE-C', 'VOL-01', 'RAIN-01'],\n    'write_approved': False}\n",
            "retained-authorization-import",
            "exercise-test",
        ),
        "student-loop-nodes",
    )
    source = """denied_call = {'name': 'read_document', 'args': {'document_id': 'NOTICE-A', 'approved': True},
               'id': 'authorization-regression'}
assert not authorize_tool(denied_call, READ_GRANTS)['allowed']
denied_state = {'messages': [AIMessage(content='', tool_calls=[denied_call])],
                'calls': 0, 'visited': [], 'stop_reason': ''}
denied_update = await tools_step(denied_state)
denied_receipts = [m for m in denied_update['messages'] if isinstance(m, ToolMessage)]
assert len(denied_receipts) == 1
assert denied_receipts[0].tool_call_id == denied_call['id']
assert denied_receipts[0].status == 'error', '未获本次钥匙，不能执行后报成功'
print('本人图保留授权拒绝、原申请身份与失败观察。')
"""
    update_cell(
        document,
        cell("code", source, "retained-authorization-check", "exercise-test"),
        "student-live-run",
    )
    export_cell = next(c for c in document.cells if c.id == "export")
    if "# 本次授权设施" not in export_cell.source:
        lines = export_cell.source.splitlines(keepends=True)
        node = next(
            n
            for n in ast.parse(export_cell.source).body
            if isinstance(n, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "prelude" for target in n.targets)
        )
        extra = "from project.m02_permissions import authorize_tool\nREAD_GRANTS = {'tools': ['read_document'], 'document_ids': ['NOTICE-B', 'NOTICE-C', 'VOL-01', 'RAIN-01'], 'write_approved': False}\n"
        lines.insert(
            node.end_lineno or node.lineno, "# 本次授权设施\nprelude += " + repr(extra) + "\n"
        )
        export_cell.source = "".join(lines)
    nbformat.write(document, ROOT / m3["notebook"])
    m9 = next(t for t in tasks if t["id"] == "M09-T02")
    document = nbformat.read(ROOT / m9["notebook"], as_version=4)
    source = '''async def actual_model_text(messages: list) -> str:
    """把实际模型返回转为调用政策需要的普通文字，不实现缓存或重试。
    Args:
        messages: 本次实际消息。
    Returns:
        AIMessage.text。
    Raises:
        模型错误原样保留。
    """
    async with asyncio.timeout(20):
        response = await model.ainvoke(messages)
    return response.text
live_budget = {'remaining': 2, 'attempts': 0}
live_cache = {}
live_payload = {'key': seat_cache_key('周六几点闭馆？', NOTICE_B, SYSTEM_PROMPT),
    'messages': [SystemMessage(SYSTEM_PROMPT), HumanMessage('周六几点闭馆？\\n' + NOTICE_B)]}
live_policy = await invoke_with_policy(actual_model_text, live_payload, live_cache, live_budget)
cached_policy = await invoke_with_policy(actual_model_text, live_payload, live_cache, live_budget)
assert live_budget['attempts'] == 1 and cached_policy['cache_hit']
save_public('owned-live-policy.json', {'first': live_policy, 'second': cached_policy, 'budget': live_budget})
'''
    update_cell(
        document, cell("code", source, "owned-real-policy", "exercise-test"), "replay-guide"
    )
    nbformat.write(document, ROOT / m9["notebook"])
    write_json(ROOT / "instructor/catalog.json", catalog)
    route = "# 从第一行Python到完整数字馆\n\n这份路线供选读；学习入口始终是README当前Notebook。单位是module/task，每次约一小时，按休息点多次完成。时间是可调整的教学估计，不是保证多久掌握。\n\n"
    route += "主线：消息与结构 → 工具反馈循环 → 状态图 → 持久化与记忆 → RAG/自适应研究 → 协作与评估 → MCP/Skills → 隔离维修 → 日常运行 → 完整交付。\n\n"
    route += "## 学习节奏\n\n工作日一次约一小时，完成一个可观察小步便保存。起步月优先门厅、问询台和委托台的基础任务；完整课程跨多个学习阶段，复杂研究与独立交付允许多次完成，不把一个月当强制终点。\n\n"
    route += "| Module | 具体成长 | 任务数 | 约一小时次数 | 章末作品 |\n|---|---|---:|---:|---|\n"
    for module in catalog["modules"]:
        group = [t for t in tasks if t["module"] == module["id"]]
        route += f"| [{module['id']} · {module['title']}](../{module['directory']}/README.md) | {module['story_goal']} | {len(group)} | {sum(t['pacing']['sessions'] for t in group)} | 本人组件、实际回执与统一接待台 |\n"
    for module in catalog["modules"]:
        route += f"\n## {module['id']} · {module['zone']}\n\n{module['story_goal']}\n\n"
        route += "| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |\n|---|---|---|---:|\n"
        for task in tasks:
            if task["module"] == module["id"]:
                route += f"| [{task['id']}](../{task['notebook']}) | {task['learning']['mechanism']} | {', '.join(task['owned_symbols']) or '本页本人定义'} | {task['pacing']['sessions']} |\n"
        route += "\n**交互交付：**" + RECIPES[module["id"]] + "\n"
    route += "\n## 核心能力覆盖\n\n| 能力 | 本人机制与真实验收位置 |\n|---|---|\n"
    coverage = {
        "消息/结构化/提示边界": ["M01-T01", "M01-T02", "M01-T03"],
        "工具循环/失败/权限": ["M02-T01", "M02-T02", "M02-T03", "M02-T04", "M03-T02"],
        "LangGraph/并发/子图/取消": ["M03-T01", "M03-T02", "M03-T03", "M03-T04"],
        "持久化/审核/长期记忆/上下文": [
            "M04-T01",
            "M04-T02",
            "M04-T03",
            "M04-T04",
            "M04-T05",
            "M04-T06",
        ],
        "RAG/切块/embedding/混合检索": ["M05-T02", "M05-T03", "M05-T05"],
        "研究/规划/补证/协作": ["M05-T01", "M05-T04", "M06-T01"],
        "评估/消融/trace/裁判": ["M06-T02", "M06-T03", "M06-T05", "M10-T02"],
        "MCP/Resources/Prompts/Skills": ["M07-T01", "M07-T02", "M07-T03", "M07-T04", "M07-T05"],
        "代码维修/隔离/恢复/补丁": ["M08-T01", "M08-T02", "M08-T03", "M08-T04"],
        "流式/预算/缓存/服务边界": ["M06-T04", "M09-T01", "M09-T02", "M09-T03", "M09-T04"],
        "完整应用/独立设计/回归/交付": ["M10-T01", "M10-T02", "M10-T03", "M10-T04"],
    }
    for topic, positions in coverage.items():
        route += f"| {topic} | {', '.join(positions)} |\n"
    route += "\n多模态暂不进入主线。协议升级、模型后训练/RL与开放互联网生产部署作为以后独立扩展，当前不标成已实训能力。\n"
    (ROOT / "instructor/LEARNING_ROUTE.md").write_text(route, encoding="utf-8")
    write_json(
        ROOT / "instructor/coverage.json",
        {
            "date": "2026-10-03",
            "coverage": coverage,
            "modules": 10,
            "tasks": len(tasks),
            "multimodal": "deferred_by_user",
            "learner_completion": "由实际证据单独记录",
        },
    )
    glossary = "# 术语查阅\n\n必要定义已同步到每关原位；本页选读，不增加前置阅读。\n\n"
    for mid, terms in MODULE_CONCEPTS.items():
        glossary += (
            "## "
            + mid
            + "\n\n"
            + "\n\n".join("**" + term + "：**" + CONCEPTS[term] for term in terms)
            + "\n\n"
        )
    (ROOT / "instructor/GLOSSARY.md").write_text(glossary, encoding="utf-8")
    print("路线、核心覆盖、逐关规则与10个模块接待台已整理；不登记本人完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
