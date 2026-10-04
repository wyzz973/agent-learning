"""完整模块接待台的教学界面；只调明确传入的本人组件。"""

from __future__ import annotations

import html
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import ipywidgets as widgets

from instructor.interaction import DeskController, show_desk

ModuleHandler = Callable[[str, str | None, dict[str, Any]], Awaitable[dict[str, Any]]]

OPERATIONS = {
    "M01": [("当前公告咨询", "consult")],
    "M02": [("取件并答复", "consult"), ("核对一张退件", "failure")],
    "M03": [("连续办理", "consult"), ("并行查两份资料", "parallel")],
    "M04": [("读取当前偏好", "consult"), ("恢复一项咨询", "resume"), ("撤回偏好", "withdraw")],
    "M05": [("研究并列出出处", "research"), ("只检查证据缺口", "evidence")],
    "M06": [("提交研究任务", "research"), ("查看实际评分", "evaluation")],
    "M07": [("通过分馆资料回答", "consult"), ("查看本次方法加载", "skills")],
    "M08": [("查看维修提议", "proposal"), ("在隔离候选中维修", "maintenance")],
    "M09": [("流式接待", "stream"), ("检查接口边界", "contracts")],
    "M10": [("日常接待", "reception"), ("资料研究", "research"), ("维修提议", "maintenance")],
}


class CourseWorkspace:
    """保留读者、办理方式和一次性许可的真实控件。"""

    def __init__(self, module: str, handler: ModuleHandler, root: Path) -> None:
        self.module, self.root = module, root
        self.user = widgets.Dropdown(
            options=[("匿名读者 A", "reader-a"), ("匿名读者 B", "reader-b")],
            description="本次读者",
            layout=widgets.Layout(width="100%"),
        )
        self.operation = widgets.Dropdown(
            options=OPERATIONS[module],
            description="这次办理",
            layout=widgets.Layout(width="100%"),
        )
        self.approval = widgets.Checkbox(
            value=False,
            description="我确认允许本次写入候选工作区或撤回所选偏好",
            indent=False,
            layout=widgets.Layout(width="100%"),
        )
        self.controls = [self.user, self.operation]
        if module in {"M04", "M08", "M10"}:
            self.controls.append(self.approval)
        notices = {
            key: {
                "label": label,
                "evidence": [
                    {
                        "id": key,
                        "title": label,
                        "text": (root / "world/notices" / filename).read_text(encoding="utf-8"),
                    }
                ],
            }
            for key, label, filename in [
                ("NOTICE-A", "试营业公告", "opening.md"),
                ("NOTICE-B", "当前临时公告", "temporary.md"),
                ("NOTICE-C", "东门还书箱说明", "return-box.md"),
            ]
        }
        selections = notices if module == "M01" else {"current": {"label": "本次委托"}}

        async def invoke_owned(question: str, selection: str | None) -> dict[str, Any]:
            values = dict(self.desk.request_context)
            self.approval.value = False  # 每次许可都由本次界面输入，不沿用上一张问题纸。
            for control in self.controls:
                control.disabled = True
            try:
                return await handler(question, selection, values)
            finally:
                for control in self.controls:
                    control.disabled = False

        chapter = json.loads((root / "instructor/course_enrichment.json").read_text())
        scene = chapter["modules"][module]
        self.desk: DeskController = show_desk(
            module,
            invoke_owned,
            root,
            selections=selections,
            initial_selection="NOTICE-B" if module == "M01" else "current",
            title="阿灯 · " + scene.get("desk_title", "雾岛接待窗"),
            description="选择本次办理方式，递来问题纸。下面的答复来自你亲手完成的组件。",
            display_ui=False,
        )
        self.desk.question.placeholder = "这次想让阿灯帮你办什么？"
        self.desk.context_provider = self.snapshot
        self.desk.selection.description = "手头依据"
        opener = scene["opening"].split("\n\n")[0]
        story = widgets.HTML(
            '<section class="fog-scene"><p class="fog-eyebrow">林禾的委托</p><p>'
            + html.escape(opener)
            + '</p><p class="fog-note">接待窗已经搭好。'
            "未完成本人函数时，会明确显示接线缺口；这里不会自动调用教师答案。</p></section>"
        )
        control_box = widgets.VBox(self.controls)
        control_box.add_class("fog-controls")
        children = list(self.desk.ui.children)
        children[1:1] = [story, control_box]
        self.desk.ui.children = tuple(children)
        self.ui = self.desk.ui

    def snapshot(self) -> dict[str, Any]:
        """读取一次实际控件值，模型文本不能伪造这些值。

        Args:
            无。
        Returns:
            本次user_id、operation和approved。
        Raises:
            无。
        """
        return {
            "user_id": self.user.value,
            "operation": self.operation.value,
            "approved": self.approval.value,
        }


def show_module_workspace(
    module: str,
    handler: ModuleHandler,
    root: Path,
    *,
    display_ui: bool = True,
) -> CourseWorkspace:
    """提供统一模块界面，明确绑定本人异步处理函数。

    Args:
        module: 当前模块ID；handler: 本人函数；root: 仓库；display_ui: 是否显示。
    Returns:
        可自由输入、取消、选匿名身份和一次性许可的接待台。
    Raises:
        ValueError: 未登记模块；OSError: 世界与章节资料缺失。
    """
    if module not in OPERATIONS:
        raise ValueError("未登记这个区域")
    workspace = CourseWorkspace(module, handler, root.resolve())
    if display_ui:
        from instructor.interaction import _display

        _display(workspace.ui, root, True)
    return workspace
