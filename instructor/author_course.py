"""编排课程补充、图解与完整Notebook；运行时保留已有本人代码。"""

from __future__ import annotations

import ast
import hashlib
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import nbformat

from instructor.check import ROOT, load_catalog
from instructor.course_atlas import FLOWS, STORIES
from instructor.extension_specs import LESSONS, Lesson

# 教学正文与代码模板保持原段落；Notebook代码另外检查长度与编译。
# ruff: noqa: E501

EXPORTS = {
    "M01-T03": "m01_messages",
    "M02-T04": "m02_permissions",
    "M03-T04": "m03_merge",
    "M04-T06": "m04_policy",
    "M05-T05": "m05_hybrid",
    "M06-T05": "m06_judge",
    "M07-T05": "m07_context",
    "M08-T04": "m08_patch",
    "M09-T01": "m09_stream",
    "M09-T02": "m09_policy",
    "M09-T03": "m09_contracts",
    "M09-T04": "m09_access",
    "M10-T01": "m10_runtime",
    "M10-T02": "m10_acceptance",
    "M10-T03": "m10_feature",
    "M10-T04": "m10_release",
}

RECIPES = {
    "M01": "先读取所选公告，使用本人build_current_messages组织输入，保留本人NoticeAnswer的字段与来源核对。真正调用当前模型后返回答复与当前公告；未知事项显示待确认。schema来自M01-T02的本人导出，不复制教师schema。",
    "M02": "调用本人run_with_recovery；允许工具通过本人authorize_tool检查，实际执行仍由execute_calls_safely完成。把完整请求ID与回执转换为公开trace，只有实际成功工具正文进入evidence。拒绝回执不算来源。",
    "M03": "使用本人build_consultation_graph编译真实图，再由observe_run消费公开事件；独立取件时使用本人的merge_receipts检查去重和冲突。保留calls、stop_reason与真实路径。graph结束与委托办妥分开。",
    "M04": "按controls的匿名user_id读取本人记忆；select_memory核对当前有效条目，未声明同意/到期的旧记录留待确认。恢复操作使用原thread_id与本人run_persistent_consultation。撤回需controls.approved，由本人withdraw_preference执行，再重新读取确认；旧报告不被假称已删除。",
    "M05": "用本人研究简报、collect_sources、chunk_sources/rank_chunks和combine_rankings选择真实证据；pack_context与fetch_archived保留来源身份。本人build_gap_graph驱动缺口与预算，真实报告返回URL、时间与窗口。不用snapshot_input替代本人上下文。",
    "M06": "本人handle_research调用run_workers、merge_worker_sources、研究与grade_run，audit_verdict核对模型裁判可靠性；使用本地服务时返回job与实际状态。全管线calls累计包括摘要，失败和待复核保留。",
    "M07": "调用本人ask_branch或answer_using_method取得实际工具观察；Resources/Prompts由compose_mcp_context选择为本轮数据，远端模板不提升权限。实际加载的Skill与真实协议/工具轨迹放进trace，方法名存在不算执行过。",
    "M08": "先检查controls.approved和允许工作区；未获准仅返回提议。本人run_guarded_repair/resume_maintenance在既有CodingWorkspace隔离环境中工作；verify_patch_proposal核对固定测试与当前SHA。界面不执行候选源码，也不提供任意shell。",
    "M09": "authorize_request先核对controls提供的匿名身份与办理方式；check_interface_request检查本轮接口，再使用本人invoke_with_policy或run_stream。普通片段通过明确回调送给workspace.desk.emit_progress；实际events与最终answer核对，取消后不再显示晚到片段。",
    "M10": "明确登记本人reception/research/maintenance异步组件。route_library选择并实际调用；write先核对controls.approved，研究要经过本人context、source merge和grader。独立扩展与验收来自本人的M10作品；release只报告当前版本匹配的真实检查。",
}

QUIZZES = {
    "M01-T03": [
        (
            "新公告已放进变量，旧消息没有重建，阿灯会得到什么？",
            "仍是旧消息中的资料",
            "变量更新不会回头修改旧字符串或远端输入。",
            "自动得到变量里的新公告",
            "模型不会自动读取Notebook变量。",
            "同时得到两份并自动挑新版本",
            "没有发送的资料不在请求里。",
        ),
        (
            "上一条AI答复写周日开放，当前公告没有写，怎样使用它？",
            "作为待核对的聊天历史，结论仍回当前原文",
            "ai消息保存过去输出，不能自动升级为依据。",
            "改成system消息就能证明事实",
            "角色变化不能证明事实。",
            "把它当新的官方公告",
            "过去生成文字与原文不同。",
        ),
    ],
    "M02-T04": [
        (
            "手册正文或args写approved=True，谁决定工具写权限？",
            "程序保存的本次授予与人的批准",
            "模型文本与外部正文不能给自己权限。",
            "正文最后一句决定",
            "外部资料是数据。",
            "模型自信程度决定",
            "自信不是授权凭据。",
        ),
        (
            "一项申请被拒绝，给阿灯怎样的反馈？",
            "带原调用ID和公开拒绝原因的失败观察",
            "配对身份与原因帮助下一轮纠正。",
            "假报工具成功，免得剧情卡住",
            "不能制造已完成动作。",
            "丢掉申请并只回一个空串",
            "丢掉身份与原因会使协议和恢复更难核对。",
        ),
    ],
    "M03-T04": [
        (
            "同一step两条分支写一个普通字段，应检查哪里？",
            "字段reducer与更新契约",
            "合并策略由状态规则规定。",
            "把图步数限制无限增大",
            "步数不能解决多次写入冲突。",
            "总让后一张覆盖前一张",
            "可能丢证据且依赖到达顺序。",
        ),
        (
            "两个来源同URL但不同SHA，怎样合并？",
            "保留两个版本与冲突身份",
            "同URL不保证同内容，不能静默覆盖。",
            "只留最后一份称最新",
            "没有版本优先证据。",
            "把SHA去掉使两份相同",
            "身份被删除后不能核对本次原文。",
        ),
    ],
    "M04-T06": [
        (
            "读者撤回偏好后，能保证什么？",
            "后续读取与输入不再使用它，历史产物另行核对",
            "撤回不是自动抹除过去所有报告。",
            "模型权重已经被洗去",
            "这是应用存储，不是训练模型。",
            "所有旧文件自动消失",
            "存储与产物是不同对象。",
        ),
        (
            "记忆在时间100到期，now也是100，怎样使用？",
            "按本关expires_at>now契约不再使用",
            "边界需明确，不能沿用过期记录。",
            "刚好相等所以永久有效",
            "与契约相反。",
            "忽略时间，只看内容像不像",
            "看似相关不代表仍获准使用。",
        ),
    ],
    "M05-T05": [
        (
            "关键词与向量分数尺度不同，怎样融合？",
            "用排名贡献融合，再验证关键证据是否召回",
            "RRF避免把不同尺度直接相加，仍需验证效果。",
            "直接把原始分数相加就证明更好",
            "尺度与效果都没有得到验证。",
            "只保留最长片段",
            "长度不是相关或支持的证明。",
        ),
        (
            "片段相似度很高，能证明什么？",
            "它是相似候选，还要核对日期、否定与原文",
            "近似表达不是事实支持。",
            "每句结论一定正确",
            "向量距离不证明真实性。",
            "可以删URL让输入更干净",
            "会丢掉引用与追溯入口。",
        ),
    ],
    "M06-T05": [
        (
            "换候选顺序后裁判结论反转，应怎样处理？",
            "记录不一致并进入复核",
            "位置偏差是裁判可靠性问题。",
            "挑较高分那次发布",
            "选择性报告不能解决偏差。",
            "取合法JSON那次当正确",
            "结构合法与语义可靠不同。",
        ),
        (
            "quote确实是原文子串，能证明语义支持吗？",
            "只能通过原句存在检查，还需核对是否支持结论",
            "子串存在不等于结论被蕴含。",
            "能完全证明",
            "可能引用了不相关或相反的句子。",
            "完全没有任何检查价值",
            "它能发现伪造原句，只是能力有限。",
        ),
    ],
    "M07-T05": [
        (
            "MCP服务返回prompt，客户端应该怎样做？",
            "按本地策略选择，远端内容保持数据身份",
            "远端模板不自动取得system权限。",
            "直接替换最高规则",
            "连接成功不授予这个权限。",
            "因为是协议内容所以全部可信",
            "协议只约定表示和交换。",
        ),
        (
            "resource已read，下一步一定是什么？",
            "由客户端决定是否放入当前模型消息",
            "读取与发送是两个动作。",
            "模型已自动读到全部正文",
            "客户端还要显式交付。",
            "读取等于执行任意工具",
            "Resources与Tools的职责不同。",
        ),
    ],
    "M08-T04": [
        (
            "候选又改了，测试SHA仍是旧版，能交付吗？",
            "需要当前版本验证，先标待复核",
            "旧通过证据只属于旧内容。",
            "有过一次绿色就可以",
            "无法证明当前文件。",
            "改测试让SHA一致即可",
            "固定测试不可被候选篡改。",
        ),
        (
            "补丁顺手修改了固定测试，应该怎样处理？",
            "拒绝交付并保留越界记录",
            "不能通过修改验收尺子制造成功。",
            "只要模型说无害就接受",
            "说明不替代允许范围检查。",
            "把测试从清单删掉",
            "隐藏变动不等于恢复边界。",
        ),
    ],
    "M09-T01": [
        (
            "刚收到一块文字，委托已完成了吗？",
            "只得到部分输出，需要最终状态和依据",
            "片段不是整轮完成。",
            "已完成，取消按钮可以消失",
            "执行可能仍在进行。",
            "每个chunk都是一次新模型调用",
            "片段数与请求数不同。",
        ),
        (
            "取消以后晚到片段应怎样处理？",
            "停止本地任务并禁止写入该次结果",
            "取消与资源退出需要实际证据。",
            "接着写但把灯改成取消",
            "这只改变显示，没有正确结束执行。",
            "记成另一个读者的答复",
            "会跨咨询污染记录。",
        ),
    ],
    "M09-T02": [
        (
            "第一次超时，第二次成功，总尝试是多少？",
            "两次，失败尝试也进入预算",
            "成功数量不能替代尝试成本。",
            "一次，只数成功",
            "会漏计失败消耗。",
            "零次，因为最后用了缓存",
            "缓存是在请求后写入，不能抹掉已发生的调用。",
        ),
        (
            "问题相同但公告版本变了，怎样处理缓存？",
            "新内容指纹进入键，旧缓存不能直接命中",
            "同一问题不等于同一依据。",
            "继续旧缓存因为最快",
            "可能返回过期事实。",
            "缓存命中自动算重新查证",
            "重用结果没有取得新原文。",
        ),
    ],
    "M09-T03": [
        (
            "模型对象创建成功，证明支持工具吗？",
            "仍需实际工具与消息契约测试",
            "接口对象可创建不代表所有能力受支持。",
            "证明所有接口都兼容",
            "能力需要逐项验证。",
            "模型名越新就无需验证",
            "名字不能证明请求与回执行为。",
        ),
        (
            "能力档案写unknown，怎样开始？",
            "做当前配置的受限探测或明确能力缺口",
            "不擅自更换配置或伪造结果。",
            "默认true继续执行",
            "把未知当支持会掩盖失败。",
            "用教师固定回答顶替",
            "不能冒充实际行为。",
        ),
    ],
    "M09-T04": [
        (
            "身份正确但请求另一读者的档案，应怎样返回？",
            "403拒绝并且不调用本人研究链",
            "认证不等于授权所有用户数据。",
            "200因为token有效",
            "作用域仍越界。",
            "401说明完全没有身份",
            "本例身份已确认，失败在授权层。",
        ),
        (
            "健康检查200，证明什么？",
            "该检查路径可响应，研究质量另行验收",
            "运行设施与答复质量不同。",
            "研究结论都有据",
            "健康响应没有核对原文。",
            "取消与恢复一定可靠",
            "需要对应真实任务验证。",
        ),
    ],
    "M10-T01": [
        (
            "只查一张已有公告的时间，怎样选工作方式？",
            "选择足够的简单接待并核对原文",
            "不为复杂度而增加循环与分工。",
            "必用最多的Agent",
            "更多组件增加成本且未必有益。",
            "跳过依据直接猜",
            "简单仍需实际依据。",
        ),
        (
            "本人研究组件尚未导出，路由应怎样做？",
            "明确报告接线缺口",
            "不回退教师答案冒充本人作品。",
            "悄悄调用备用模型并标完成",
            "缺口被掩盖。",
            "返回空报告但说已交付",
            "文件或空串不证明完成。",
        ),
    ],
    "M10-T02": [
        (
            "案例含expected，能交给被测runtime吗？",
            "不能，预期只交给评分器",
            "否则答案条件泄漏进被测输入。",
            "能，这样更容易全通过",
            "通过不能反映真实泛化。",
            "只给部分预期就不算泄漏",
            "仍改变了实际任务条件。",
        ),
        (
            "平均分很高但有跨用户泄漏，该怎样报告？",
            "单独暴露关键失败并阻止相应交付",
            "平均分不能掩盖重要边界失败。",
            "隐藏低分样本",
            "选择性报告损害验收。",
            "把它算普通文风问题",
            "这是授权与作用域错误。",
        ),
    ],
    "M10-T03": [
        (
            "新增一项能力，首先做什么？",
            "明确输入输出和扩展边界，保留旧契约",
            "先知道要改变哪项行为。",
            "把整馆换框架再说",
            "同时引入太多变量且未解释需求。",
            "只增加文件数量",
            "文件存在不代表能力。",
        ),
        (
            "新需求跑通后，下一步是什么？",
            "跑旧回归与陌生输入，记录限制",
            "局部成功不能证明旧能力仍保留。",
            "立即把全馆标通关",
            "缺本人掌握与回归证据。",
            "删除旧检查免得出错",
            "不能弱化验收制造成功。",
        ),
    ],
    "M10-T04": [
        (
            "发布清单里的通过SHA与当前文件不同，状态应怎样？",
            "draft或待重新验证",
            "通过记录只能证明当时版本。",
            "verified因为名字相同",
            "文件名不能代替内容身份。",
            "把SHA改成当前值即可",
            "不能篡改已有测试凭据。",
        ),
        (
            "交付文件里包含.env，应该怎样？",
            "拒绝纳入发布，配置由接手者本地提供",
            "真实凭据不进入课程产物包。",
            "随包公开方便启动",
            "会暴露密钥。",
            "把文件改名就安全",
            "内容仍然是凭据。",
        ),
    ],
}


def svg_flow(task: str, labels: list[str]) -> str:
    """生成可以在Notebook直接阅读的数据流SVG。"""
    body = []
    for index, label in enumerate(labels):
        x = 22 + index * 202
        pieces = [label[i : i + 10] for i in range(0, len(label), 10)]
        body.append(
            f'<rect x="{x}" y="83" width="182" height="120" rx="8" fill="#fffdf7" stroke="#8c9c92"/>'
        )
        body.append(f'<text x="{x + 14}" y="110" fill="#9b7939" font-size="13">0{index + 1}</text>')
        for row, piece in enumerate(pieces):
            body.append(
                f'<text x="{x + 91}" y="{143 + row * 23}" text-anchor="middle" fill="#203e42" font-size="16">{html.escape(piece)}</text>'
            )
        if index < 4:
            body.append(
                f'<path d="M{x + 183} 143h17" stroke="#203e42" stroke-width="2" marker-end="url(#arrow)"/>'
            )
    loop = task in {"M02-T03", "M03-T02", "M05-T04", "M08-T01"}
    if loop:
        body.append(
            '<path d="M918 207v35H312v-35" fill="none" stroke="#9b7939" stroke-dasharray="5 5" marker-end="url(#arrow)"/>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="285" viewBox="0 0 1040 285" role="img">'
        f"<title>{task} 本关概念数据流</title><desc>" + html.escape(" → ".join(labels)) + "</desc>"
        '<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6" fill="#203e42"/></marker></defs>'
        '<rect width="1040" height="285" fill="#f5f1e6" rx="10"/>'
        f'<text x="22" y="37" font-family="serif" font-size="23" fill="#203e42">{task} · 沿着一份输入走</text>'
        '<text x="22" y="62" font-size="13" fill="#526669">概念示意；本次运行是否经过这些步骤，请核对本页实际输入、观察与输出。</text>'
        + "".join(body)
        + '<text x="22" y="274" font-size="12" fill="#526669">每条箭头都需要一次明确的数据传递；界面、资料存在或模型声称完成，都不能替代运行证据。</text></svg>'
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cell(kind: str, source: str, cell_id: str, tag: str = "demo") -> Any:
    if kind == "markdown":
        return nbformat.v4.new_markdown_cell(source, id=cell_id)
    return nbformat.v4.new_code_cell(source, id=cell_id, metadata={"tags": [tag]})


def notebook_for(spec: Lesson, path: Path) -> None:
    """从教学模板生成完整新课；不覆盖已经存在的本人练习。"""
    if path.exists():
        return
    cli = Path("/Users/sd3/.codex/skills/jupyter-notebook/scripts/new_notebook.py")
    subprocess.run(
        [sys.executable, str(cli), "--kind", "tutorial", "--title", spec.title, "--out", str(path)],
        check=True,
        capture_output=True,
    )
    document = nbformat.read(path, as_version=4)
    signature = spec.signature
    parsed = ast.parse(signature + "\n    pass")
    function = parsed.body[0]
    assert isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
    for argument in function.args.args:
        if argument.annotation is None:
            argument.annotation = ast.Name(id="Any")
    signature = ast.unparse(function).splitlines()[0]
    fname = function.name
    cells = [
        cell(
            "markdown",
            f"# {spec.task} · {spec.title}\n\n{spec.scene}\n\n本关直接在此页学习；需要的Python写法原位解释。馆务是雾岛虚构素材，技术资料保留真实来源。\n\n**要带走：**本人`{fname}`、真实检查回执和改变输入后的对照。预计{spec.hours}次约一小时的学习，可随时保存休息。",
            "opening-scene",
        )
    ]
    cells.append(
        cell(
            "markdown",
            "## 先看本关的工作顺序\n\n预测 → 教师小例子 → 沿数据流检查 → 本人实现 → 正常与故障核对 → 对照 → 新输入。\n\n`setup/demo`由教师提供；`exercise/exercise-test`由本人完成或调用本人代码。报NotImplementedError时先写本页核心函数，教师不会代填。",
            "lesson-route",
        )
    )
    imports = """import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Literal
from IPython.display import Markdown, display
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
ROOT = Path.cwd()
for candidate in [ROOT, *ROOT.parents]:
    if (candidate / 'instructor/catalog.json').is_file():
        ROOT = candidate
        break
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'modules/05-deep-research'))
import library_facilities as lab"""
    cells.append(cell("code", imports, "setup-imports", "setup"))
    cells.append(
        cell(
            "code",
            f"TASK_ID = {spec.task!r}\nmodel, SYSTEM_PROMPT = lab.configure(ROOT, TASK_ID)\nOUTPUT_DIR = ROOT / 'outputs/fog-island' / TASK_ID\nOUTPUT_DIR.mkdir(parents=True, exist_ok=True)\nNOTICE_B = (ROOT / 'world/notices/temporary.md').read_text()\nNOTICE_C = (ROOT / 'world/notices/return-box.md').read_text()\nprint(SYSTEM_PROMPT)\n",
            "setup-world",
            "setup",
        )
    )
    cells.append(
        cell(
            "code",
            '''def save_public(name: str, data: dict) -> Path:
    """保存本页明确构造的公开回执，不保存原始模型对象。
    Args:
        name: 本页文件名；data: 公开数据。
    Returns:
        实际文件路径。
    Raises:
        ValueError: 文件名越界；其他写入错误保留。
    """
    if Path(name).name != name:
        raise ValueError("作品文件名不能带路径")
    return lab.save_json(OUTPUT_DIR / name, data)''',
            "setup-records",
            "setup",
        )
    )
    cells.append(cell("markdown", "## 原理：这个机制为何需要\n\n" + spec.theory, "deep-principles"))
    cells.append(
        cell(
            "markdown",
            "## 先教马上要用的Python\n\n"
            + spec.python
            + "\n\n函数参数是当次输入；字典用键取值，列表保持顺序，集合表达允许身份。`return`交还结果，`raise`中止并保留原因。带`async`的函数需`await`，异步流用`async for`。本页示范与核心题使用不同馆务对象，机制相通；不要把示范常量写进本人函数。",
            "python-before-code",
        )
    )
    cells.append(
        cell(
            "markdown",
            "## 教师示范：先看一小段完整数据\n\n下面的完整小例子使用座位/值班标签等资料，展示输入、处理与输出。它不会调用或替代本人实现。先在心里预测，再逐格运行。",
            "teacher-introduction",
        )
    )
    cells.extend(
        [
            cell("code", spec.teacher, "teacher-mechanism"),
            cell("code", spec.observe, "teacher-observation"),
        ]
    )
    if spec.live:
        cells.append(cell("code", spec.live, "teacher-live-call"))
    elif spec.task not in {"M06-T05", "M09-T01"}:
        # 这次请求有实际公告，但不伪装已执行本人机制。
        request = "林禾请你接待一位访客。他问本周六几点闭馆。只依据这张当前公告回答，保留编号：\n"
        cells.append(
            cell(
                "markdown",
                "### 回到真实模型的输入边界\n\n上面的纯Python检查不消耗模型调用。下面另做一次教师真实接待：明确提供当前公告，核对模型回复。它只证明本关模型连通与当前资料进入请求，不证明本人核心函数已完成。",
                "teacher-model-boundary",
            )
        )
        cells.append(
            cell(
                "code",
                f"teacher_answer = await lab.ask(model, SYSTEM_PROMPT, {request!r} + NOTICE_B)\ndisplay(Markdown(teacher_answer))\nsave_public('teacher-live.json', {{'answer': teacher_answer, 'notice': NOTICE_B, 'scope': '教师输入边界验证'}})",
                "teacher-live-call",
            )
        )
    cells.append(
        cell(
            "markdown",
            "### 休息点 A\n\n能沿输入和输出辨认刚才的机制后，可以保存休息。下一次从下面的本人契约开始，先实现一个正常输入，再接错误分支。原理判断在页末用选择卡完成，不要求文字总结。",
            "rest-a",
        )
    )
    cells.append(
        cell(
            "markdown",
            "## 本人核心实现\n\n**函数契约：**"
            + spec.contract
            + "\n\n**如何渐进完成：**先从一份最小合法输入开始，只让核心数据走通；再分别加入空输入、越界或停止条件；最后跑完整检查与迁移。\n\n<details><summary>提示一：不知道从哪里下手</summary>先对照函数签名，找出当次参数与应返回的字段。用本页示范的不同馆务值尝试一条正常路径。</details>\n\n<details><summary>提示二：条件有点多</summary>先辨认哪些条件是输入是否合法，哪些是允许动作，哪些是结果是否可用。一次只改一个条件，再看首个发生变化的位置。</details>\n\n<details><summary>提示三：跑了却结果不对</summary>查看实际输入、更新和返回类型，定位第一次偏差。可以把一条箭头交给导师解释，核心机制仍由你组织。</details>",
            "owned-contract",
        )
    )
    implementation = (
        signature
        + '\n    """本人实现本关关键机制。\n\n    Args:\n        '
        + ", ".join(a.arg for a in function.args.args)
        + ': 含义与边界见紧邻契约表。\n    Returns:\n        契约指定的真实结果，不内置本题答案。\n    Raises:\n        ValueError: 输入不符合约定；未完成时明确占位。\n    """\n    raise NotImplementedError("请本人完成'
        + fname
        + '")\n'
    )
    cells.append(cell("code", implementation, "owned-implementation", "exercise"))
    cells.append(
        cell(
            "markdown",
            "## 检查真实路径\n\n下面调用的都是本人的函数；每个断言只证明它写明的条件。替身用于可重复故障时会明确标识，模型效果需另跑真实输入，不把替身成绩当馆务完成。",
            "owned-check-guide",
        )
    )
    cells.append(cell("code", spec.checks, "owned-checks", "exercise-test"))
    cells.append(
        cell(
            "markdown",
            "## 改一个条件做对照\n\n"
            + spec.replay
            + "\n\n保持其他输入与版本尽量相同，核对第一处变化；一次观察不推广为所有模型都如此。",
            "replay-guide",
        )
    )
    cells.append(
        cell(
            "code",
            "replay_record = None  # TODO：用本人函数运行上方对照，保存实际输入与结果。\nif replay_record is None:\n    raise NotImplementedError('请本人完成一项只改一个条件的对照')\nsave_public('owned-replay.json', replay_record)",
            "owned-replay",
            "exercise-test",
        )
    )
    cells.append(
        cell(
            "markdown",
            "## 新来客：保持机制，换输入\n\n"
            + spec.transfer
            + "\n\n失败同样留在作品中，核对状态与依据。这里检验核心函数是否使用参数，而非记住示范答案。",
            "transfer-guide",
        )
    )
    cells.append(
        cell(
            "code",
            "transfer_record = None  # TODO：用本页指定的新输入实际运行本人函数。\nif transfer_record is None:\n    raise NotImplementedError('请本人完成陌生输入迁移')\nsave_public('owned-transfer.json', transfer_record)",
            "owned-transfer",
            "exercise-test",
        )
    )
    cells.append(
        cell(
            "markdown",
            "## 把能力放回阿灯\n\n"
            + spec.reuse
            + "\n\n下面只提取你已保存的定义；仍有占位异常时拒绝导出，已有不同本人文件也不自动覆盖。",
            "continuity-handoff",
        )
    )
    prelude = "from pathlib import Path\nfrom typing import Any, Callable, Literal\nimport asyncio\nimport json\nimport hashlib\nfrom langchain.messages import AIMessage, HumanMessage, SystemMessage\n"
    if spec.task == "M01-T03":
        prelude += "ROOT = Path(__file__).resolve().parents[1]\nSYSTEM_PROMPT = (ROOT / 'world/prompts/M01-T03.md').read_text()\n"
    if spec.task == "M09-T02":
        prelude += (
            'class TransientFailure(Exception):\n    """明确的可恢复运行错误。"""\n    pass\n'
        )
    cells.append(
        cell(
            "code",
            "from instructor.learner_exports import export_definitions\nprelude = "
            + repr(prelude)
            + "\nprint('随本人定义一起保存的导入设施：\\n', prelude)\nexported = export_definitions(\n    ROOT / "
            + repr(str(path.relative_to(ROOT)))
            + ", ['owned-implementation'], ["
            + repr(fname)
            + "],\n    ROOT / 'project/"
            + EXPORTS[spec.task]
            + ".py', prelude)\nprint('本人来源与导出文件：', exported)",
            "owned-export",
            "exercise-test",
        )
    )
    document.cells = cells
    document.metadata["kernelspec"] = {
        "display_name": "Agent Learning (.venv)",
        "language": "python",
        "name": "agentlearning",
    }
    document.metadata["agent_learning"] = {
        "task_id": spec.task,
        "campaign_id": "fog-island-library",
    }
    nbformat.write(document, path)


def quiz_for(spec: Lesson) -> list[dict[str, Any]]:
    result = []
    for index, values in enumerate(QUIZZES[spec.task], 1):
        prompt, good, good_feedback, bad, bad_feedback, other, other_feedback = values
        choices = [
            (good, good_feedback, True),
            (bad, bad_feedback, False),
            (other, other_feedback, False),
        ]
        shift = int(hashlib.sha256(f"{spec.task}-{index}".encode()).hexdigest(), 16) % 3
        choices = choices[shift:] + choices[:shift]
        options = [
            {"id": chr(65 + i), "label": label, "feedback": feedback}
            for i, (label, feedback, _) in enumerate(choices)
        ]
        correct = next(chr(65 + i) for i, (_, _, yes) in enumerate(choices) if yes)
        result.append(
            {
                "id": f"{spec.task}-Q{index}",
                "prompt": prompt,
                "concept": spec.mechanism,
                "options": options,
                "correct": correct,
            }
        )
    return result


def main() -> int:
    backup = ROOT / "outputs/authoring/2026-10-03-before"
    if not backup.exists():
        backup.mkdir(parents=True)
        for directory in ["modules", "instructor", "world"]:
            shutil.copytree(
                ROOT / directory,
                backup / directory,
                ignore=shutil.ignore_patterns("__pycache__", "qa", "outputs"),
            )
        shutil.copy2(ROOT / "README.md", backup / "README.md")
    catalog = load_catalog()
    enrichment = json.loads((ROOT / "instructor/course_enrichment.json").read_text())
    for number, folder, title, zone, goal, skills in [
        (
            9,
            "09-runtime-and-service",
            "运行与应用边界",
            "运行室 · 接稳日常使用",
            "让阿灯的流式、预算、接口与服务身份有真实边界。",
            "streaming、缓存、重试、模型契约、认证授权",
        ),
        (
            10,
            "10-opening-capstone",
            "完整数字馆交付",
            "开馆验收桌 · 交出整座馆",
            "把本人全部能力接成可复现、可回归、有实际凭据的数字馆。",
            "workflow选择、端到端、留出、独立扩展、发布清单",
        ),
    ]:
        mid = f"M{number:02}"
        if not any(m["id"] == mid for m in catalog["modules"]):
            catalog["modules"].append(
                {
                    "id": mid,
                    "directory": "modules/" + folder,
                    "title": title,
                    "zone": zone,
                    "story_goal": goal,
                    "skills": skills,
                }
            )
        (ROOT / "modules" / folder).mkdir(parents=True, exist_ok=True)
        enrichment["modules"][mid] = {
            "opening": STORIES[mid],
            "principle": goal + "\n\n" + RECIPES[mid],
            "arc": "本章的实际回执进入下一步的验收；所有能力以本人运行核对。",
            "capability_contract": RECIPES[mid],
            "pitfalls": "工具可见不等于有权限；对象创建不等于接口兼容；旧测试不证明新版本；缺本人组件不得回退。",
            "game_goal": "在统一接待台实际使用本人组件，核对正常、失败/取消、迁移以及当前版本。",
        }
    modules = {m["id"]: m for m in catalog["modules"]}
    for spec in LESSONS:
        mid = spec.task.split("-")[0]
        path = ROOT / modules[mid]["directory"] / spec.file
        notebook_for(spec, path)
        if not any(t["id"] == spec.task for t in catalog["tasks"]):
            q = {
                "id": spec.task,
                "title": spec.title,
                "zone": modules[mid]["zone"],
                "commission": "林禾：“" + spec.scene.split("。")[0] + "。请把这件事实际办清楚。”",
                "obstacle": spec.mechanism,
                "starting_kit": "当前页提供必要Python、完整教师输入输出、真实模型及分层提示。",
                "player_action": spec.contract,
                "reward": "本人的核心函数、正常/故障回执、对照和迁移作品。",
                "acceptance": "核对本页断言、真实输入和来源；选择题与代码迁移分开记录。",
                "replay": spec.replay,
                "transfer": spec.transfer,
                "choice": "选择先做一条正常路径或先定位一个故障，核心验收相同。",
                "next_hook": spec.reuse,
                "prompt_role": "负责"
                + spec.title
                + "，把实际输入、观察和未完成之处交给林禾或读者。",
                "prompt_mission": spec.mechanism
                + "只使用当前实际提供的资料；自然回应，缺少原文、能力或许可时清楚说明，不假报办妥。",
            }
            catalog["tasks"].append(
                {
                    "id": spec.task,
                    "module": mid,
                    "title": spec.title,
                    "notebook": str(path.relative_to(ROOT)),
                    "status": "draft",
                    "requires": [],
                    "external_prerequisites": [],
                    "quest": q,
                    "learning": {
                        "mechanism": spec.mechanism,
                        "python": spec.python,
                        "framework": "当前锁定版本的LangChain/LangGraph、明确本人接口与本页代码。",
                        "frontier": "接口与成熟范式以当前官方资料核查；不承诺通用能力。",
                        "references": list(spec.references),
                    },
                    "pacing": {"sessions": spec.hours, "session_minutes": 60},
                }
            )
        enrichment["tasks"][spec.task] = {
            "principle_markdown": "### 从第一性原理理解这一关\n\n" + spec.theory,
            "quiz": quiz_for(spec),
        }
    catalog["tasks"].sort(key=lambda t: t["id"])
    catalog["schema_version"] = 5
    catalog["primary_track"] = (
        "Python与LangChain → LangGraph → 记忆与RAG → 研究与协议 → Coding Agent → 运行与完整交付"
    )
    catalog["campaign"]["evidence"] = ["本人程序运行", "原理选择题", "陌生输入迁移"]
    write_json(ROOT / "instructor/catalog.json", catalog)
    for mid, chapter in enrichment["modules"].items():
        chapter["opening"] = STORIES[mid]
        chapter["desk_title"] = modules[mid]["zone"].split(" · ")[-1]
        chapter["capability_contract"] += (
            "\n\n模块接待台实际接线：" + RECIPES[mid]
            if RECIPES[mid] not in chapter["capability_contract"]
            else ""
        )
    write_json(ROOT / "instructor/course_enrichment.json", enrichment)
    for task in catalog["tasks"]:
        path = ROOT / "assets/lessons" / (task["id"] + ".svg")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg_flow(task["id"], FLOWS[task["id"]]), encoding="utf-8")
    story = "# 雾岛图书馆：开馆行动\n\n> 故事是贯穿课程的虚构馆务，不需要提前阅读。实际学习从README当前Notebook进入。\n\n"
    story += "雾岛的雾不需要被打败，它只是让人看不远。图书馆需要的也是同一种可靠：知道眼前依据在哪里，知道下一步怎样走，知道尚未看见什么。\n\n你是从零开始的新人工程师。林禾负责提出具体需求与人的决定，阿灯是逐步由你建造的软件助手，匿名访客带来新的输入。这里只有这四种角色，没有开馆倒计时、扣分或必须连续学习的约定。\n\n贯穿全馆的是三件物品：折角公告、取件回执、值班簿。它们分别指向输入依据、实际行动、可以接续的状态；最后交付时重新汇合。\n\n"
    for m in catalog["modules"]:
        story += f"## {m['id']} · {m['zone']}\n\n{STORIES[m['id']]}\n\n"
        story += (
            "**本章实际委托：**"
            + "；".join(
                t["id"] + " " + t["title"] for t in catalog["tasks"] if t["module"] == m["id"]
            )
            + "。\n\n"
        )
    story += "## 灯亮以后\n\n开馆是新的开始。陌生需求可能暴露新的缺口；从实际失败、来源与验收出发，选择必要的工具与框架。故事奖励只能对应已经生成的答复、档案、报告、服务或补丁，不能代替本人掌握。\n"
    (ROOT / "world/STORY.md").write_text(story, encoding="utf-8")
    print(
        "完整编排：",
        len(catalog["modules"]),
        "模块，",
        len(catalog["tasks"]),
        "任务；新增课暂标draft，待真实验证。",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
