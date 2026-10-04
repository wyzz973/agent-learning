"""准备隔离的教师浏览器验收页，复用已保存本人函数，不写通关状态。"""

import ast
import shutil

import nbformat

# 演练Notebook代码模板保留原行；实际课程另有逐格长度校验。
# ruff: noqa: E501
from instructor.check import ROOT


def main() -> int:
    """准备图解、本人第一关接线及教师流式演练。"""
    destination = ROOT / "outputs/authoring/2026-10-03-ui"
    destination.mkdir(parents=True, exist_ok=True)
    for relative in [
        "instructor/course_enrichment.json",
        "assets/fog-desk.css",
        "world/notices/opening.md",
        "world/notices/temporary.md",
        "world/notices/return-box.md",
    ]:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    original = nbformat.read(ROOT / "modules/01-langchain-foundations/01-first-reader.ipynb", 4)
    source = next(c.source for c in original.cells if c.id == "reader-exercise")
    definition = next(n for n in ast.parse(source).body if isinstance(n, ast.AsyncFunctionDef))
    fn = ast.get_source_segment(source, definition)
    if fn is None:
        raise ValueError("本人已保存定义无法定位")
    intro = (
        "# 雾岛图书馆 · 教师界面验收\n\n"
        "第一张接待台复用已保存的本人answer_reader；第二张是明确标出的教师流式设施演练。"
        "记录隔离在本目录，不登记本人完成。\n\n"
        "![RAG图解](/files/assets/rag-workflow.svg)\n\n"
        "![工具循环](/files/assets/agent-loop.svg)"
    )
    setup = f"""import asyncio
import sys
from pathlib import Path
from typing import Any
ROOT = Path({str(ROOT)!r})
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'modules/05-deep-research'))
import library_facilities as lab
from langchain.messages import HumanMessage, SystemMessage
from instructor.course_workspace import show_module_workspace
UI_ROOT = Path({str(destination)!r})
model, SYSTEM_PROMPT = lab.configure(ROOT, 'M01-T01')
NOTICE_B = (ROOT / 'world/notices/temporary.md').read_text()
"""
    binding = """NOTICES = {'NOTICE-A': 'opening.md', 'NOTICE-B': 'temporary.md', 'NOTICE-C': 'return-box.md'}
async def existing_reader(question: str, selection: str | None, controls: dict) -> dict:
    notice = (ROOT / 'world/notices' / NOTICES[selection]).read_text()
    answer = await answer_reader(question, notice)
    return {'answer': answer, 'evidence': [{'id': selection, 'text': notice}],
            'artifacts': [], 'status': 'answered'}
reader_workspace = show_module_workspace('M01', existing_reader, UI_ROOT)
"""
    stream = """async def teacher_stream(question: str, selection: str | None, controls: dict) -> dict:
    pieces = []
    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question + '\\n当前公告：\\n' + NOTICE_B)]
    async for chunk in model.astream(messages):
        if chunk.text:
            pieces.append(chunk.text)
            stream_workspace.desk.emit_progress({'stage': '真实流正在返回', 'text': chunk.text})
    return {'answer': ''.join(pieces), 'evidence': [{'id': 'NOTICE-B', 'text': NOTICE_B}],
            'artifacts': [], 'status': 'answered'}
stream_workspace = show_module_workspace('M09', teacher_stream, UI_ROOT)
"""
    document = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell(intro),
            nbformat.v4.new_code_cell(setup),
            nbformat.v4.new_code_cell(fn),
            nbformat.v4.new_code_cell(binding),
            nbformat.v4.new_markdown_cell(
                "## 教师真实流式演练\n\n这个回调用于验收公开事件与取消设施，未代填M09本人run_stream。"
            ),
            nbformat.v4.new_code_cell(stream),
        ],
        metadata={
            "kernelspec": {
                "display_name": "Agent Learning (.venv)",
                "language": "python",
                "name": "agentlearning",
            }
        },
    )
    nbformat.write(document, destination / "interface-check.ipynb")
    print(destination / "interface-check.ipynb")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
