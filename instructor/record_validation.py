"""从当前源文件与实际执行副本整理课程验收，绝不制造学生成绩。"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import nbformat

from instructor.author_course import write_json
from instructor.check import ROOT, load_catalog

# 验收文档的原段落保持完整，运行代码仍由Ruff和mypy检查。
# ruff: noqa: E501


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verified-on", type=date.fromisoformat,
        default=datetime.now(ZoneInfo("Asia/Shanghai")).date(),
    )
    args = parser.parse_args()
    verified_on = args.verified_on.isoformat()
    catalog = load_catalog()
    check_outputs = {}
    for name, arguments in {
        "pytest": ["-m", "pytest", "-q"],
        "ruff": ["-m", "ruff", "check", "instructor", "tests", "modules", "--exclude", "*.ipynb"],
        "notebook_teachers": ["-m", "instructor.lint_notebooks"],
        "exports": ["-m", "instructor.check_export_contracts"],
        "mypy": ["-m", "mypy", "instructor"],
        "course": ["-m", "instructor.check"],
    }.items():
        checked = subprocess.run(
            [sys.executable, *arguments], cwd=ROOT, capture_output=True, text=True, timeout=60
        )
        if checked.returncode != 0:
            raise ValueError(
                name + "当前检查未通过：" + checked.stdout[-1200:] + checked.stderr[-400:]
            )
        check_outputs[name] = checked.stdout.strip()
    fixtures = json.loads(
        (ROOT / "outputs/enterprise-redesign/fixture-validation.json").read_text()
    )
    native_proof = json.loads(
        (ROOT / "outputs/enterprise-redesign/native-model-proof.json").read_text()
    )
    if (
        not native_proof["model_type_preserved"]
        or not native_proof["original_configuration_preserved"]
    ):
        raise ValueError("原生框架模型与配置的实际兼容验收不通过")
    preservation = json.loads((ROOT / "outputs/enterprise-redesign/preservation.json").read_text())
    if preservation["changed"] or not all(r["prepared"] for r in fixtures["records"]):
        raise ValueError("本人保护或实际环境准备未通过")
    blueprints_path = ROOT / "instructor/module_blueprints.json"
    blueprints = json.loads(blueprints_path.read_text())
    enrichment = json.loads((ROOT / "instructor/course_enrichment.json").read_text())
    question_count = sum(len(t["quiz"]) for t in enrichment["tasks"].values())
    pytest_match = re.search(r"(\d+) passed", check_outputs["pytest"])
    mypy_match = re.search(r"(\d+) source files", check_outputs["mypy"])
    if pytest_match is None or mypy_match is None:
        raise ValueError("实际检查输出没有可读取的通过数量，不能写入假计数")
    pytest_count = int(pytest_match[1])
    mypy_count = int(mypy_match[1])
    results = []
    cells = chars = 0
    for task in catalog["tasks"]:
        directory = ROOT / "outputs/validation" / task["id"]
        record = json.loads((directory / "result.json").read_text())
        source = nbformat.read(ROOT / task["notebook"], as_version=4)
        actual = nbformat.read(directory / "executed.ipynb", as_version=4)
        teacher = [
            {"id": c.id, "source": c.source}
            for c in source.cells
            if c.cell_type == "code" and set(c.metadata.get("tags", [])) & {"setup", "demo"}
        ]
        executed = [
            {"id": c.id, "source": c.source}
            for c in actual.cells
            if c.cell_type == "code" and set(c.metadata.get("tags", [])) & {"setup", "demo"}
        ]
        expected_skipped = {
            c.id
            for c in source.cells
            if c.cell_type == "code"
            and set(c.metadata.get("tags", [])) & {"exercise", "exercise-test"}
        }
        if (
            not record["passed"]
            or teacher != executed
            or expected_skipped != set(record["skipped_exercise_cells"])
        ):
            raise ValueError("当前源文件与教师运行/跳过清单不一致：" + task["id"])
        record["teacher_source_sha256"] = hashlib.sha256(
            json.dumps(teacher, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        record["prompt_sha256"] = hashlib.sha256(
            (ROOT / "world/prompts" / (task["id"] + ".md")).read_bytes()
        ).hexdigest()
        results.append(record)
        cells += len(source.cells)
        chars += sum(len(c.source) for c in source.cells if c.cell_type == "markdown")
    report: dict[str, Any] = {
        "campaign_id": "fog-island-library",
        "verified_on": verified_on,
        "execution_recorded_utc": datetime.now(UTC).isoformat(),
        "scope": "44份当前教师setup/demo在独立新内核运行；本人实现、对照、迁移与模块接线格全部跳过。",
        "course_design": {
            "zones": 10,
            "quests": 44,
            "ready_notebooks": 44,
            "scene_prompts": 44,
            "notebook_cells": cells,
            "markdown_characters": chars,
            "concept_questions": question_count,
            "task_svg_diagrams": 44,
            "core_svg_diagrams": 3,
            "module_architecture_diagrams": len(blueprints["modules"]),
            "production_projects": len(blueprints["modules"]),
            "production_case_environments": len(fixtures["records"]),
            "reviewed_source_walkthroughs": len(enrichment["tasks"]),
        },
        "executed_teacher_code_cells": sum(r["executed_cells"] for r in results),
        "skipped_student_cells": sum(len(r["skipped_exercise_cells"]) for r in results),
        "results": results,
        "checks": {
            "pytest": f"{pytest_count} passed",
            "ruff": "Python设施、测试与模块通过；Notebook教师格按明确标签另查",
            "notebook_teachers": check_outputs["notebook_teachers"],
            "export_contracts": check_outputs["exports"],
            "mypy": f"{mypy_count} files passed",
            "course": "目录、prompt、图片路径、题库、规则别名及入口一致",
            "preservation": f"本轮开始的{preservation['exercise_cells']}个exercise核心格逐格一致；第一关全部本人格含源/元数据/输出一致",
        },
        "enterprise_validation": {
            "native_model_proof": "outputs/enterprise-redesign/native-model-proof.json；当前真实模型通过create_agent兼容验收，原配置保留。",
            "teacher_scope": "十章实际业务环境、模型与故障示范；源码与当前执行副本一致。",
            "fixture_scope": fixtures["scope"],
            "prepared_cases": len(fixtures["records"]),
            "learner_cases_executed": 0,
            "source_marker_fix": "曾观察到答复错误沿用NOTICE；提供真实来源包并修正通用岗位编号规则后重验。",
            "failure_evidence": "outputs/enterprise-redesign/source-marker-failures",
            "ui_scope": "新版章节与生产实训的静态Notebook HTML渲染、展开原理、图像与桌面布局；未操作本人业务函数。",
            "review_report": "outputs/enterprise-redesign/walkthrough-review.json",
            "preservation_report": "outputs/enterprise-redesign/preservation.json",
        },
        "interface_validation": {
            "report": "outputs/authoring/2026-10-03-ui/acceptance.json",
            "M01": "复用已保存本人answer_reader真实调用",
            "M09": "明确标识的教师真实流演练，28个实际事件与一次取消；未代写run_stream",
            "all_modules": "10个统一工作台已提供；参数、一次性许可、取消、缺实现行为替身测试通过。本人业务组件待逐关完成。",
        },
        "limits": [
            "教师路径成功与本人掌握分开，不登记通关。",
            "本人完整RAG/研究/协作/语义评分/毕业验收尚未运行；其设施连接有单独契约测试。",
            "官方发现范围为LangChain/Python/MCP三个主域，不冒称开放全网搜索。",
            "受控16份双语语料/20卡已测中英文与中文查英文；真实业务多语质量与本人策略仍须另验。",
            "模型生成代码只在M08隔离Docker运行；本轮没有对互联网部署或推送GitHub。",
            "多模态按用户要求暂不涉及；课件质量仍需后续本人独立实现与迁移表现持续检验。",
        ],
        "facility_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                *ROOT.glob("instructor/*.py"),
                *ROOT.glob("modules/*/*.py"),
                ROOT / "uv.lock",
                ROOT / "assets/fog-desk.css",
            ]
        },
    }
    write_json(ROOT / "instructor/validation.json", report)
    state = json.loads((ROOT / "instructor/state.json").read_text())
    state["updated_at"] = verified_on
    state["next_action"] = (
        "从M01-T02当前Notebook继续，完成后进入M01-T03消息工作垫，再进入M02四项工具委托；不重做已完成第一关。"
    )
    state["material_validation"].update(
        real_demo_notebooks_passed=44,
        note=f"{pytest_count}设施测试通过；44份教师新内核验证，本人格按实际清单跳过，未新增通关。",
    )
    state["authoring_scope"].update(
        status="materials_ready",
        completed_notebooks=44,
        request="按模块系统设计企业情景精品课程，原理、组件、生产故障、真实实训与本人交付；多模态暂不涉及。",
        polish=f"10模块三级路线、44逐关源码拆解、10架构图与手册、20生产案例环境、{question_count}判断卡、统一接待台；实际验证与本人掌握分别记录。",
        enterprise_revision="materials_verified_learner_work_pending",
    )
    for blueprint in blueprints["modules"]:
        blueprint["lab_status"] = "teacher_verified_learner_pending"
    write_json(blueprints_path, blueprints)
    for module in catalog["modules"]:
        state.setdefault("interface_delivery", {})[module["id"]] = {
            "status": "workspace_ready_learner_binding_pending",
            "entry": next(
                t["notebook"] for t in reversed(catalog["tasks"]) if t["module"] == module["id"]
            ),
            "contract": "module_agent(question, selection, controls)",
            "verification": "instructor/tests/test_workspace.py；本人函数运行与教师UI演练单独记录",
            "note": "界面不回退教师答案，不自动修改学习状态。",
        }
    state["interface_delivery"]["M01"]["observed_existing_binding"] = (
        "answer_reader真实浏览器验收通过，公告卡与新module_agent待本人完成。"
    )
    write_json(ROOT / "instructor/state.json", state)
    acceptance = f"""# {verified_on} 课程验收清单

课程按10模块、44份Notebook编排为从零入门、组件开发、生产实训三级。贯穿项目是机构数字知识服务；每章有业务架构、详细原理、故障矩阵、实际实训与本人交付契约。当前44份教师路径全部通过，学习入口仍为M01-T02，原有本人作品保留。

| 内容 | 本轮完成与证据 |
|---|---|
| 完整学习路线 | LEARNING_ROUTE.md与catalog，按module/task及约一小时的休息点 |
| 原理与过程 | 十章完整手册嵌入首关；44关新增审核过的三条具体源码观察与对照/迁移 |
| 图文 | 44张任务SVG、3张核心图、10张业务架构图；原位图片路径通过 |
| 剧情 | 完整十章加机构业务事件，折角公告/取件回执/值班簿贯穿到交付 |
| 编码与复盘 | 核心编码保留，{question_count}情景单选题有逐项解析、无默认答案 |
| 生产实训 | 十章真实模型、SQLite/HTTP/MCP/embedding/Docker边界；20本人案例环境实际准备通过 |
| 本人完整项目 | 明确的module_agent契约、三阶段接线、独立环境与实际输入/事件/事务检查；本人实现未代填 |
| 接待台 | 十章末页已搭统一设施、身份/办理/一次性许可/依据/作品/事件/取消 |
| 教师实际运行 | 44/44，{report["executed_teacher_code_cells"]}教师格执行，{report["skipped_student_cells"]}本人格跳过 |
| 设施检查 | {pytest_count} pytest、Ruff、{mypy_count}文件mypy与课程检查通过 |
| 已修真实偏差 | 新资料答复套旧编号；提供完整来源身份并修正岗位规则，原失败另存后重新验证 |
| 保护本人内容 | 本轮开始的{preservation["exercise_cells"]}个exercise核心格一致；第一关本人全部格及输出一致 |

## 明早怎样验收

先打开根README看十章业务项目和三级路线。选读PRODUCTION_RESEARCH.md了解逐模块依据。M03首关的展开手册讲图/reducer/并行/副作用，章末真实两进程实训展示“发布已提交、节点未交回更新”；M04核对CAS与撤回；M05核对索引更新与权限；M07核对MCP真实生命周期；M08看当前源码与固定Docker测试；M09看实际HTTP超时歧义。章末再按三阶段接线与独立案例交付本人的阿灯。

运行`uv run python -m instructor.launch`打开当前Notebook。对教师部分可逐格观察真实输出；本人未完成格的NotImplementedError是等待学习者实现，不是教师兜底。接待台同样只调用明确传入的本人组件，缺实现会指出缺口。

浏览器验收保存在`outputs/authoring/2026-10-03-ui`：RAG和工具图实际加载，M01本人旧函数真实答复，M09教师真实流与取消，540与1280宽度无工作台横向溢出。它是教师设施验收，不登记学习成绩。

新版章节静态渲染验收在`outputs/enterprise-redesign/ui`，检查了展开手册、实际图片与1280宽度的章末实训。生产示范证据在`outputs/enterprise/Mxx-Txx`；案例初始环境证明在`fixture-validation.json`；编号错误的失败Notebook另存，未用新的成功覆盖旧失败。

生产故障矩阵包含已跑示范、本人案例与进一步扩展设计，三者分别标识。课程是企业情景的本地实践，真实机构的IAM、网络部署、大规模索引、运维容量等仍需在具体环境完成验收；本文不宣称已有商业服务上线。

尚未宣称：本人全馆端到端完成、留出成绩、所有模型兼容、开放全网研究、互联网部署、多模态能力或市场排名。本轮未提交、推送，也未代填后续核心答案。
"""
    (ROOT / "instructor/ACCEPTANCE.md").write_text(acceptance, encoding="utf-8")
    print(
        "已记录：44/44教师，",
        report["executed_teacher_code_cells"],
        "教师格；",
        report["skipped_student_cells"],
        "本人格跳过；未登记新通关。",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
