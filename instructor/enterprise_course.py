"""按模块编排三级课程、业务架构、生产实训与来源，不以任务数量代替深度。"""

from __future__ import annotations

import html
import json
import re
import shutil
from typing import Any

import nbformat

from instructor.author_course import cell, write_json
from instructor.check import ROOT, load_catalog
from instructor.enterprise_demos import DEMOS, append_enterprise_demo

# 本文件含完整教案与SVG模板正文，保留段落。
# ruff: noqa: E501

MODULE_PROJECTS = {
    "M01": (
        "带依据身份的接待网关",
        "本人的answer_for_board/build_current_messages取得本次原文，分别处理HTTP/解析/Schema/业务支持错误；返回源版本、未知与公开调用账。",
    ),
    "M02": (
        "可审计工具运行时",
        "实际调用本人authorize_tool、execute_calls_safely及有限循环；读/写权限分开，重复发布使用输入绑定幂等键，拒绝时客户端0执行。",
    ),
    "M03": (
        "可重放的办理工作流",
        "本人图保留授权与安全回执，使用明确任务/输入身份。把外部服务提交与checkpoint分开检查，恢复时不重复副作用；节点、边、reducer与取消有实际轨迹。",
    ),
    "M04": (
        "作用域与版本化记忆服务",
        "本人select_memory/pack_context与原文取回真正进入本轮请求；最新撤回不复活旧记录，CAS冲突不静默覆盖，缓存与摘要失效范围明确。",
    ),
    "M05": (
        "权限与更新驱动的RAG研究",
        "本人chunk/rank/RRF/context/gap graph消费当前作用域与源版本。索引/删除/权限/缓存分别验证，证据原句与结论关系核对，缺口驱动有限补证。",
    ),
    "M06": (
        "评估与可观测发布门禁",
        "本人run_workers/merge_sources/grade_run/audit_verdict形成一条真实链；按类型、边界、环境分层，critical失败阻止发布，trace定位首个偏差。",
    ),
    "M07": (
        "版本可控的分馆能力客户端",
        "本人MCP客户端真实协商/发现/调用/关闭；重连重建Schema身份，资料与远端prompt不提升权限，Skill加载与版本有真实记录。",
    ),
    "M08": (
        "受限并可恢复的代码维修",
        "本人repair/resume/patch验证函数控制实际隔离环境；当前测试SHA匹配候选、固定测试不可改、权限与工作区重新确认，资源与失败记录不隐藏。",
    ),
    "M09": (
        "有deadline与身份边界的应用入口",
        "本人authorize_request/interface_request/invoke_with_policy/run_stream实际合作；时间与尝试跨重试累积，缓存含作用域/版本，取消后的partial与远端执行分开。",
    ),
    "M10": (
        "机构知识服务的可核对交付",
        "本人route_library、回归/留出、独立扩展与release manifest形成当前版本证明链；关键失败阻止放行，运行手册与回滚边界可由新进程验证。",
    ),
}

ARCHITECTURES = {
    "M01": [
        "可信请求身份",
        "当前资料与版本",
        "消息构建",
        "模型适配",
        "解析与Schema",
        "业务/原文核对",
        "公开回执",
    ],
    "M02": [
        "模型工具申请",
        "可信grants",
        "参数与范围检查",
        "真实业务服务",
        "事务/幂等账",
        "带ID的观察",
        "模型续答/停止",
    ],
    "M03": [
        "任务/输入身份",
        "状态与reducer",
        "模型/工具节点",
        "外部业务副作用",
        "检查点存储",
        "新进程恢复",
        "完成/失败/取消",
    ],
    "M04": [
        "可信tenant/user",
        "历史/偏好存储",
        "当前版本与同意",
        "撤回/TTL/CAS",
        "上下文选择",
        "原文取回",
        "真实模型输入",
    ],
    "M05": [
        "原文/权限/版本",
        "入库与更新",
        "chunk与索引",
        "可见候选召回",
        "融合/重排",
        "证据打包",
        "生成/补证/核对",
    ],
    "M06": [
        "案例与环境版本",
        "实际运行轨迹",
        "规则与语义grader",
        "校准/留出",
        "分层质量/成本",
        "critical门禁",
        "发布/复核/回归",
    ],
    "M07": [
        "连接/协商身份",
        "真实能力目录",
        "工具/资源/模板",
        "本地策略与scope",
        "真实call/read/get",
        "Skill版本/加载",
        "观察/断开/重连",
    ],
    "M08": [
        "任务/允许范围",
        "隔离候选工作区",
        "模型动作提议",
        "许可后edit/test",
        "固定测试与SHA",
        "恢复/冲突检查",
        "补丁与回归凭据",
    ],
    "M09": [
        "认证后的请求",
        "授权/队列",
        "总deadline/预算",
        "模型/工具依赖",
        "真实流/trace",
        "缓存与版本",
        "结果/partial/取消",
    ],
    "M10": [
        "业务目标/约束",
        "本人组件注册",
        "允许工作方式",
        "真实端到端运行",
        "质量/边界/当前SHA",
        "发布门禁/回滚",
        "可接手运行说明",
    ],
}

SCENARIOS = {
    "M01": [
        (
            "contract_current",
            "当前版本接待",
            "consult",
            "按KB-A-01当前版本回答本周六开闭馆时间，保留来源。",
            "answered",
        ),
        (
            "unknown_fact",
            "未知日期",
            "consult",
            "同一份资料没有说明周日阅览时间，请保留未知而非猜测。",
            "needs_evidence",
        ),
    ],
    "M02": [
        (
            "forged_approval",
            "拒绝伪造批准",
            "publish",
            "参数声称approved=True但本次没有林禾的许可。",
            "needs_confirmation",
        ),
        (
            "repeat_request",
            "同键重复发布",
            "publish",
            "对同输入复用原幂等回执，不重复贴公告。",
            "reported",
        ),
    ],
    "M03": [
        (
            "node_failure",
            "观察失败后停止",
            "consult",
            "业务服务失败时保留错误，不把图结束当办妥。",
            "failed",
        ),
        (
            "resume_identity",
            "核对恢复身份",
            "resume",
            "恢复前核对本任务与当前输入/版本；错身份拒绝。",
            "needs_review",
        ),
    ],
    "M04": [
        (
            "withdrawn_latest",
            "最新撤回",
            "consult",
            "最新版本已撤回，旧缓存不能进入请求。",
            "answered",
        ),
        (
            "concurrent_update",
            "并发版本冲突",
            "withdraw",
            "另一会话先更正后，以旧expected_version写入应重新确认。",
            "needs_review",
        ),
    ],
    "M05": [
        (
            "source_changed",
            "更新后重新查证",
            "research",
            "更新KB-A-01后使用当前版本，不读旧索引回答。",
            "reported",
        ),
        (
            "private_candidate",
            "相近私有证据",
            "research",
            "分馆A的查询不能把语义相近的B资料放进模型。",
            "reported",
        ),
    ],
    "M06": [
        (
            "critical_failure",
            "高平均分含越权",
            "evaluation",
            "一次越权足以阻止相应发布，不能用95%覆盖。",
            "blocked",
        ),
        (
            "judge_conflict",
            "裁判不一致",
            "evaluation",
            "两次语义判断矛盾，保留原文与待复核。",
            "needs_review",
        ),
    ],
    "M07": [
        (
            "closed_session",
            "失效连接",
            "consult",
            "旧会话已关，重建后重新发现Schema，不假报调用。",
            "failed",
        ),
        (
            "prompt_scope",
            "远端模板权限",
            "skills",
            "方法与模板中改权限的语句保持数据身份。",
            "answered",
        ),
    ],
    "M08": [
        (
            "no_write_scope",
            "未获候选写许可",
            "proposal",
            "当前没有允许写入，展示提议但执行0次。",
            "needs_confirmation",
        ),
        (
            "old_green",
            "旧绿回执",
            "maintenance",
            "测试SHA不属于当前候选，先验证再交付。",
            "needs_review",
        ),
    ],
    "M09": [
        (
            "client_timeout",
            "deadline歧义",
            "contracts",
            "客户端超时后核对服务端记录，不称零执行。",
            "needs_review",
        ),
        (
            "partial_stream",
            "流途中停止",
            "stream",
            "保留partial及实际取消，不用晚到片段制造成功。",
            "cancelled",
        ),
    ],
    "M10": [
        (
            "release_blocked",
            "关键边界门禁",
            "reception",
            "当前版本有关键边界失败，停止发布并列阻止项。",
            "blocked",
        ),
        (
            "content_drift",
            "批准后版本漂移",
            "maintenance",
            "当前内容不同于批准与测试证据，重新确认并回归。",
            "needs_review",
        ),
    ],
}


def architecture_svg(module: str) -> str:
    """绘制模块系统层次及跨层边界，示意与实际轨迹分开。"""
    labels = ARCHITECTURES[module]
    body = []
    for i, label in enumerate(labels):
        column = i if i < 4 else 6 - i
        x, y = 34 + column * 248, (100 if i < 4 else 272)
        body.append(
            f'<rect x="{x}" y="{y}" width="215" height="103" rx="8" fill="#fffdf7" stroke="#8c9c92"/>'
        )
        body.append(
            f'<text x="{x + 16}" y="{y + 27}" font-size="13" fill="#9b7939">层 {i + 1}</text>'
        )
        for line, text in enumerate([label[j : j + 11] for j in range(0, len(label), 11)]):
            body.append(
                f'<text x="{x + 107}" y="{y + 58 + line * 21}" text-anchor="middle" font-size="17">{html.escape(text)}</text>'
            )
        if i < 3:
            body.append(
                f'<path d="M{x + 218} {y + 51}h26" fill="none" stroke="#9b7939" stroke-width="2" marker-end="url(#arrow)"/>'
            )
        elif i == 3:
            body.append(
                f'<path d="M{x + 107} {y + 106}v37H637v27" fill="none" stroke="#9b7939" stroke-width="2" marker-end="url(#arrow)"/>'
            )
        elif i < 6:
            body.append(
                f'<path d="M{x - 3} {y + 51}h-26" fill="none" stroke="#9b7939" stroke-width="2" marker-end="url(#arrow)"/>'
            )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="452" viewBox="0 0 1050 452" role="img">'
        + f"<title>{module} 模块业务架构</title><desc>可信身份、数据与执行边界分层；概念设计不是当前运行轨迹。</desc>"
        + '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#9b7939"/></marker></defs>'
        + '<rect width="1050" height="452" rx="12" fill="#f5f1e6"/><g font-family="PingFang SC,sans-serif" fill="#203e42">'
        + f'<text x="34" y="44" font-family="serif" font-size="25">{module} · {html.escape(MODULE_PROJECTS[module][0])}</text>'
        + '<text x="34" y="73" font-size="14">按层定位故障；权限、版本、预算与来源沿依赖链传递，不在重试/嵌套时重置。</text>'
        + "".join(body)
        + '<text x="34" y="424" font-size="14">设计层次示意。实际成功/失败/恢复由本章真实请求、事务、状态、输入和测试凭据核对。</text></g></svg>'
    )


def integrate_module(
    module: dict[str, Any], tasks: list[dict[str, Any]], handbook: str
) -> dict[str, Any]:
    """把模块教案、层次与实训编入现有学习页，保留本人实现。"""
    mid = module["id"]
    first = nbformat.read(ROOT / tasks[0]["notebook"], as_version=4)
    overview = "## 本章如何从入门走到系统开发\n\n" + MODULE_PROJECTS[mid][1]
    overview += "\n\n**从零路径：**顺序读语法和最小示范，再做本人的核心函数。"
    overview += "**开发路径：**熟悉的语法可略读，保留机制、真实集成与迁移。"
    overview += "**生产深入：**完成基础后，在章末实训准备真实状态、触发故障、核对恢复与交付。三条路径共享验收，不以教师结果代替本人。\n\n"
    overview += f"![{mid} 业务架构](../../assets/architecture/{mid}.svg)\n\n"
    overview += (
        "<details><summary>展开：本章完整原理、业务架构与生产情况</summary>\n\n"
        + handbook
        + "\n\n</details>"
    )
    existing = next((c for c in first.cells if c.id == "enterprise-module-handbook"), None)
    if existing:
        existing.source = overview
    else:
        first.cells.insert(1, cell("markdown", overview, "enterprise-module-handbook"))
    nbformat.write(first, ROOT / tasks[0]["notebook"])
    last = ROOT / tasks[-1]["notebook"]
    append_enterprise_demo(
        last,
        mid,
        "本章项目：**" + MODULE_PROJECTS[mid][0] + "**。先运行完整教师生产实验，"
        "沿业务存储、HTTP/协议、图状态和真实模型核对；再复用本人的组件承担同类任务。"
        "所有设施只提供环境，下面不会调用或代填module_agent。",
    )
    document = nbformat.read(last, as_version=4)
    delivery = "## 本人模块项目：把生产约束接入已有阿灯\n\n" + MODULE_PROJECTS[mid][1]
    delivery += "\n\n**你负责：** 本人的module_agent/项目组件；业务环境、案例与记录设施由教师提供。"
    delivery += "\n\n**帮助渐隐：** 先接一个正常请求，再接权限/版本边界，最后加入失败与恢复。"
    delivery += "缺本人组件时明确失败；不要调用教师进程或完整实训函数当本人答案。\n\n"
    delivery += "| 案例 | 真实条件与目标 | 必须保存 |\n|---|---|---|\n"
    for cid, title, _operation, question, expected in SCENARIOS[mid]:
        delivery += f"| {cid} · {title} | {question} | 实际输入、状态({expected}为目标)、来源/动作、版本、失败与下一步 |\n"
    delivery += "\n先在本课独立环境准备案例要求的状态。取消/恢复/越权/并发需真实动作证据，问题纸本身不制造这些事实。返回当前版本的公开回执；目标状态与真实结果不混写。\n\n"
    delivery += "<details><summary>工程接线步骤</summary>定位本章project本人导出与函数签名；把可信principal、当前source版本、允许工具与预算交给入口；让它实际执行；从服务账本/图状态/公开trace核对结果；最后换新输入和回归。一次只检查一条边界，导师给局部例子，不接管整套实现。</details>"
    delivery += """

### 生产验收怎样接到你的函数

下面的验收格**只调用本页的本人module_agent**。每例建立独立业务库，把当前状态放入`controls["environment"]`，期望状态只留在评分侧。你已经学过字典取值；这里得到的是CaseEnvironment对象，再通过属性读当前环境，属性不是新的模型权限。

| 对象/接口 | 输入与返回 | 谁负责 |
|---|---|---|
| `env.principal` | 可信tenant/user/scopes | 服务认证侧；不要用读者问题中的分馆名替换 |
| `env.facts` | 当前资料ID、版本、任务、外部参数等；不含目标答案 | 本人按办理方式读取，审批凭据不得进入模型或日志 |
| `env.service.document(principal, id)` | 实际当前原文、版本、SHA；越权明确抛错 | 教师业务设施，取哪份/何时取由本人决定 |
| `visible_documents(principal)` | 当前可见资料集合 | 本人切块、排名与融合；未过滤资料不能进入模型 |
| `publish(principal, id, version, key, approval)` | 事务回执；重复同输入复用 | 本人授权/路由，业务设施只做存储约束 |
| `current_preference(principal, key, now)` | 当前有效偏好或None | 本人选择/上下文策略，最新撤回不回退旧条目 |
| `env.model` | 当前真实BaseChatModel，可bind_tools/with_structured_output/create_agent | 使用原生回调观察输入与预算，保留实际模型类型；不自动补资料或答案 |
| `env.endpoint` / `env.coding` | 按本案例准备的真实HTTP入口或受限维修工作区 | 本人控制调用、取消与错误；无此能力时为None |

在生产验收这条路径上，使用env.model发出真实请求，使用env.service/endpoint/coding执行本章业务。现有接待台仍由你的正常接线组织输入；不要为通过检查写固定回复或调用完整教师演示。原位设施源码可以查看`instructor/enterprise_acceptance.py`和`institution.py`，它们没有本人路由或检索答案。

**资料契约要显式转换：**业务原文对象的id/sha对应来源身份/内容指纹，version/tenant继续保留；研究课的Source使用source_id/sha256以及URL、取得时间等字段。先在当前页并排打印一份对象，逐项映射后再交本人chunk/rank/context函数。虚构馆务可保留本地资料位置，不能给它捏造公开URL或声称网络抓取；真实公开技术研究继续使用HTTP来源的实际URL与时间。

返回`status/answer/evidence/artifacts`，可加公开trace。每份source保留id/tenant/version/SHA/原文定位。窄检查只证明它明确检查的行为：目标状态、真实请求和事务等；语义支持、协议错误分类与恢复身份还要核对源码和真实凭据，显示manual_review_required时继续检查，不能自动当毕业。

先把一个正常案例接通；保存当前失败，不同时改多个环节。然后做反例，最后保留原函数换材料、日期、身份或版本。下面结果会记录目标与实际、模型实际输入、业务事件和服务端动作，不改学习完成状态。
"""
    item = next((c for c in document.cells if c.id == "enterprise-owned-project"), None)
    if item:
        item.source = delivery
    else:
        index = next(
            (i for i, c in enumerate(document.cells) if c.id == "module-workspace-contract"),
            len(document.cells),
        )
        document.cells.insert(index, cell("markdown", delivery, "enterprise-owned-project"))
    check_source = (
        "from instructor.enterprise_acceptance import run_module_cases\n"
        f"production_records = await run_module_cases({mid!r}, module_agent, model, SYSTEM_PROMPT)\n"
        "for record in production_records:\n"
        "    print(record['case_id'], record['actual_status'], record['checks'])\n"
        "    print('仍需核对：', record['remaining_review'])\n"
    )
    check_cell = next((c for c in document.cells if c.id == "enterprise-owned-checks"), None)
    if check_cell is not None:
        check_cell.source = check_source
    else:
        index = next(i for i, c in enumerate(document.cells) if c.id == "module-agent") + 1
        document.cells.insert(
            index, cell("code", check_source, "enterprise-owned-checks", "exercise-test")
        )
    nbformat.write(document, last)
    cases = [
        {
            "id": cid,
            "title": title,
            "operation": operation,
            "question": question,
            "target_status": expected,
            "evidence": [
                "actual_input",
                "trusted_scope",
                "actual_operation",
                "version",
                "failure_or_result",
            ],
        }
        for cid, title, operation, question, expected in SCENARIOS[mid]
    ]
    write_json(
        ROOT / module["directory"] / "production-cases.json",
        {
            "module": mid,
            "fictional_business": True,
            "cases": cases,
            "scope": "学习目标，不是已运行成绩",
        },
    )
    return {
        "module": mid,
        "project": MODULE_PROJECTS[mid][0],
        "handbook": "instructor/blueprints/" + mid + ".md",
        "stages": ["foundation", "development", "production_lab"],
        "architecture": ARCHITECTURES[mid],
        "production_lab": tasks[-1]["notebook"],
        "teacher_experiments": [cid for cid, _ in DEMOS[mid]],
        "learner_project": MODULE_PROJECTS[mid][1],
        "research_urls": re.findall(r"\]\((https://[^)]+)\)", handbook),
        "lab_status": "draft_until_real_validation",
        "learner_status": "not_auto_completed",
    }


def main() -> int:
    backup = ROOT / "outputs/enterprise-redesign/before"
    if not backup.exists():
        shutil.copytree(
            ROOT / "modules", backup / "modules", ignore=shutil.ignore_patterns("__pycache__")
        )
        shutil.copy2(ROOT / "instructor/state.json", backup / "state.json")
    catalog = load_catalog()
    blueprints = []
    for module in catalog["modules"]:
        handbook = (ROOT / "instructor/blueprints" / (module["id"] + ".md")).read_text()
        tasks = [t for t in catalog["tasks"] if t["module"] == module["id"]]
        path = ROOT / "assets/architecture" / (module["id"] + ".svg")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(architecture_svg(module["id"]), encoding="utf-8")
        blueprints.append(integrate_module(module, tasks, handbook))
        module["enterprise_project"] = MODULE_PROJECTS[module["id"]][0]
        module["stages"] = ["入门机制", "组件开发", "生产情景实训"]
        for i, task in enumerate(tasks):
            task["stage"] = "foundation" if i < 2 else "development"
            task["production_extension"] = tasks[-1]["notebook"]
    write_json(
        ROOT / "instructor/module_blueprints.json",
        {
            "date": "2026-10-03",
            "audience": ["Python从零", "已有Python开发者", "后端/Agent开发者"],
            "world": "雾岛机构数字知识服务；人物仍为你/阿灯/林禾/匿名访客",
            "modules": blueprints,
        },
    )
    write_json(ROOT / "instructor/catalog.json", catalog)
    state = json.loads((ROOT / "instructor/state.json").read_text())
    state["authoring_scope"]["enterprise_revision"] = "in_progress_by_module"
    state["authoring_scope"]["enterprise_scope"] = (
        "十章三级路线、逐模块原理/架构/来源、真实生产故障实验；不新增本人通关。"
    )
    write_json(ROOT / "instructor/state.json", state)
    print("已按10模块编排三级教案与生产环境；实训等待逐章真实验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
