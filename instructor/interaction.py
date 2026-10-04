"""雾岛Notebook的统一交互设施：只调用显式传入的本人函数，不提供学生答案。"""

from __future__ import annotations

import asyncio
import hashlib
import html
import inspect
import json
import os
import re
import threading
import time
import traceback
import uuid
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

import ipywidgets as widgets
from IPython.display import HTML, display

DeskHandler = Callable[[str, str | None], Awaitable[dict[str, Any]]]
_APPEND_LOCK = threading.Lock()
_PRIVATE_FIELDS = {
    "apikey",
    "token",
    "accesstoken",
    "refreshtoken",
    "authorization",
    "password",
    "secret",
    "cookie",
    "cookies",
    "headers",
    "requestheaders",
    "reasoning",
    "reasoningcontent",
    "reasoningdetails",
    "chainofthought",
    "additionalkwargs",
    "responsemetadata",
    "rawresponse",
}
_STATE_TEXT = {
    "idle": "接待台空着，可以递来一张问题纸。",
    "running": "阿灯正在办理这次咨询，请稍等。",
    "cancelling": "正在停下这次办理，请等回执收好。",
    "completed": "答复已放在桌上，依据和作品在下方。",
    "incomplete": "这件事还没办完，阿灯留下了当前结果。",
    "needs_confirmation": "阿灯把结果留在桌上，等你确认后再继续。",
    "failed": "阿灯没能办成这次委托，已留下当前结果和原因。",
    "unrecognized": "答复已回来，但办理状态还需要核对，先不算办妥。",
    "cancelled": "这次已停下，没有把它记成办妥。",
    "error": "这次没办妥，请展开诊断记录查看原因。",
}
# 仅把明确认识的业务状态映射到界面；未知值不能默认当作成功。
_HANDLER_STATES = {
    "completed": "completed",
    "success": "completed",
    "ok": "completed",
    "answered": "completed",
    "verified": "completed",
    "budget_exhausted": "incomplete",
    "blocked": "incomplete",
    "needs_attention": "incomplete",
    "incomplete": "incomplete",
    "needs_evidence": "incomplete",
    "needs_capability": "incomplete",
    "needs_review": "needs_confirmation",
    "draft": "incomplete",
    "reported": "completed",
    "paused": "incomplete",
    "pending": "incomplete",
    "needs_confirmation": "needs_confirmation",
    "awaiting_confirmation": "needs_confirmation",
    "awaiting_approval": "needs_confirmation",
    "failed": "failed",
    "error": "failed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _redact(text: str) -> str:
    for key, value in os.environ.items():
        if len(value) >= 6 and any(
            part in key.upper() for part in ("TOKEN", "API_KEY", "SECRET", "PASSWORD")
        ):
            text = text.replace(value, "[已隐藏凭据]")
    text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[已隐藏凭据]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{12,}\b", "[已隐藏凭据]", text)
    return text


def _public(value: Any) -> Any:
    if isinstance(value, str):
        return _redact(value)
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _public(item)
            for key, item in value.items()
            if re.sub(r"[^a-z]", "", str(key).lower()) not in _PRIVATE_FIELDS
        }
    if isinstance(value, (list, tuple)):
        return [_public(item) for item in value]
    raise TypeError("交互结果需要公开的JSON数据，不能传入原始消息或模型响应对象。")


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _append_attempt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _APPEND_LOCK, path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _header(title: str, introduction: str, eyebrow: str) -> Any:
    return widgets.HTML(
        '<div class="fog-shelf" aria-hidden="true"><i></i><i></i><i></i><i></i></div>'
        f'<p class="fog-eyebrow">{_escape(eyebrow)}</p><h2>{_escape(title)}</h2>'
        f'<p class="fog-intro">{_escape(introduction)}</p>'
    )


def _style(root: Path) -> str:
    return (root / "assets/fog-desk.css").read_text(encoding="utf-8")


def _display(ui: Any, root: Path, enabled: bool) -> None:
    if enabled:
        display(HTML("<style>" + _style(root) + "</style>"))  # type: ignore[no-untyped-call]
        display(ui)  # type: ignore[no-untyped-call]


def _safe_url(url: str) -> str | None:
    parsed = urlsplit(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc and not parsed.username:
        return url
    return None


def _evidence_html(evidence: list[Any], empty: str) -> str:
    if not evidence:
        return '<p class="fog-note">' + _escape(empty) + "</p>"
    rows = []
    for item in evidence:
        if isinstance(item, str):
            rows.append(
                '<div class="fog-evidence-item fog-message-text">' + _escape(item) + "</div>"
            )
            continue
        if not isinstance(item, Mapping):
            raise TypeError("依据应为文字或包含公开字段的字典。")
        title = item.get("title") or item.get("source_id") or item.get("id") or "本次依据"
        text = item.get("text") or item.get("content") or item.get("excerpt") or ""
        url = _safe_url(str(item.get("url", "")))
        link = (
            f'<a href="{_escape(url)}" target="_blank" rel="noopener noreferrer">查看原文</a>'
            if url
            else ""
        )
        rows.append(
            '<div class="fog-evidence-item"><strong>'
            + _escape(title)
            + "</strong> "
            + link
            + '<div class="fog-message-text">'
            + _escape(text)
            + "</div></div>"
        )
    return "".join(rows)


class QuizController:
    """控制复盘单选题，仅记录本次选择，不认定掌握。

    Args:
        task_id: 课程任务ID；items: 含题目、选项、解析和参考选项的列表。
        root: 仓库根目录，选择记录保存到outputs/learning/attempts.jsonl。
    """

    def __init__(self, task_id: str, items: list[dict[str, Any]], root: Path) -> None:
        self.task_id = task_id
        self.root = root.resolve()
        self.items = {item["id"]: item for item in items}
        self.questions: dict[str, Any] = {}
        self.submit_buttons: dict[str, Any] = {}
        self.retry_buttons: dict[str, Any] = {}
        self.feedback: dict[str, Any] = {}
        self.last_attempts: dict[str, dict[str, Any]] = {}
        self.attempts_path = self.root / "outputs/learning/attempts.jsonl"
        cards = []
        for number, item in enumerate(items, 1):
            question_id = item["id"]
            selection = widgets.RadioButtons(
                options=[(option["label"], option["id"]) for option in item["options"]],
                value=None,
                description="选择",
                layout=widgets.Layout(width="100%"),
            )
            submit = widgets.Button(description="看看我的判断", disabled=True)
            submit.add_class("fog-primary")
            retry = widgets.Button(description="再想一次", disabled=True)
            feedback = widgets.HTML()
            self.questions[question_id] = selection
            self.submit_buttons[question_id] = submit
            self.retry_buttons[question_id] = retry
            self.feedback[question_id] = feedback
            selection.observe(
                lambda change, q=question_id: self._choice_changed(q, change), names="value"
            )
            submit.on_click(lambda _button, q=question_id: self.submit(q))
            retry.on_click(lambda _button, q=question_id: self.retry(q))
            actions = widgets.HBox([submit, retry], layout=widgets.Layout(flex_flow="row wrap"))
            actions.add_class("fog-actions")
            card = widgets.VBox(
                [
                    widgets.HTML(f"<h3>{number:02d} · {_escape(item['prompt'])}</h3>"),
                    selection,
                    actions,
                    feedback,
                ]
            )
            card.add_class("fog-quiz-card")
            cards.append(card)
        self.ui = widgets.VBox(
            [
                _header(
                    "把这件事想清楚",
                    "先选一个判断，再看每个选项的解释。答错可以重试，编码练习仍由你完成。",
                    task_id + " · 回到值班桌",
                ),
                *cards,
                widgets.HTML(
                    '<p class="fog-note">这里只保存选择证据，不把分数或参考答案当成已经掌握。</p>'
                ),
            ]
        )
        self.ui.add_class("fog-root")

    def _choice_changed(self, question_id: str, change: dict[str, Any]) -> None:
        self.submit_buttons[question_id].disabled = change["new"] is None

    def choose(self, question_id: str, option_id: str) -> None:
        """设置一个明确选项，便于键盘交互和控制器测试。

        Args:
            question_id: 当前题目ID；option_id: 题目中存在的选项ID。
        Returns:
            无，不自动提交或记录成绩。
        Raises:
            KeyError: 题目不存在；ValueError: 选项不合法。
        """
        self.questions[question_id].value = option_id

    def submit(self, question_id: str) -> dict[str, Any] | None:
        """提交一次本人选择，显示逐项解析并保存证据。

        Args:
            question_id: 当前题目ID。
        Returns:
            已保存的选择记录，含提交时的题目快照与内容指纹；未选择时为None。
        Raises:
            KeyError: 题目不存在；OSError: 记录无法保存。
        """
        item = self.items[question_id]
        selected = self.questions[question_id].value
        if selected is None:
            self.feedback[
                question_id
            ].value = '<p class="fog-note" role="status">先选一个你认为合理的答案。</p>'
            return None
        # 保留提交当时的完整题意与呈现顺序，不能用修订后的题库解释旧选项字母。
        question_snapshot = {
            "id": item["id"],
            "prompt": item["prompt"],
            "concept": item["concept"],
            "options": [
                {"id": option["id"], "label": option["label"], "feedback": option["feedback"]}
                for option in item["options"]
            ],
            "correct": item["correct"],
        }
        snapshot_json = json.dumps(
            question_snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        option_labels = {option["id"]: option["label"] for option in item["options"]}
        attempt = {
            "kind": "quiz_choice",
            "learning_signal": "choice",
            "origin": "learner",
            "help_level": "unreported",
            "schema_version": 2,
            "question_sha256": hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest(),
            "question_snapshot": question_snapshot,
            "selected_label": option_labels[selected],
            "expected_label": option_labels[item["correct"]],
            "attempt_id": uuid.uuid4().hex,
            "created_at": _now(),
            "task_id": self.task_id,
            "question_id": question_id,
            "selected": selected,
            "matched_expected": selected == item["correct"],
            "concept": item["concept"],
            "evidence_scope": "仅本人本次选择，不能自动推断独立掌握或通关",
        }
        _append_attempt(self.attempts_path, attempt)
        self.last_attempts[question_id] = attempt
        rows = []
        for option in item["options"]:
            labels = []
            if option["id"] == selected:
                labels.append("你的选择")
            if option["id"] == item["correct"]:
                labels.append("参考判断")
            tag = (
                '<span class="fog-feedback-tag">' + _escape(" · ".join(labels)) + "</span>"
                if labels
                else ""
            )
            rows.append(
                '<div class="fog-feedback-line" data-reference="'
                + str(option["id"] == item["correct"]).lower()
                + '">'
                + tag
                + "<strong>"
                + _escape(option["label"])
                + "</strong>"
                + '<p class="fog-message-text">'
                + _escape(option["feedback"])
                + "</p></div>"
            )
        message = (
            "这次判断与参考一致。再看看每项为什么成立或不成立。"
            if attempt["matched_expected"]
            else "这次有一处要重新想想。下面逐项说明原因。"
        )
        self.feedback[question_id].value = (
            '<div class="fog-feedback" role="status"><p>'
            + message
            + "</p>"
            + "".join(rows)
            + '<p class="fog-note">本题关注：'
            + _escape(item["concept"])
            + "</p></div>"
        )
        self.retry_buttons[question_id].disabled = False
        self.submit_buttons[question_id].disabled = True
        return attempt

    def retry(self, question_id: str) -> None:
        """清空本题选择以重新判断，不删除先前选择记录。

        Args:
            question_id: 当前题目ID。
        Returns:
            无，参考结果收起且无默认选择。
        Raises:
            KeyError: 题目不存在。
        """
        self.questions[question_id].value = None
        self.feedback[question_id].value = ""
        self.retry_buttons[question_id].disabled = True
        self.submit_buttons[question_id].disabled = True


def _validate_quiz(items: Any) -> list[dict[str, Any]]:
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list) or not items:
        raise ValueError("当前任务需要至少一道复盘选择题。")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not all(
            key in item for key in ("id", "prompt", "options", "correct", "concept")
        ):
            raise ValueError("题目缺少id/prompt/options/correct/concept。")
        if item["id"] in seen:
            raise ValueError("题目ID重复。")
        seen.add(item["id"])
        options = item["options"]
        if not isinstance(options, list) or len(options) < 2:
            raise ValueError("每题需要至少两个有解析的选项。")
        ids = []
        for option in options:
            if not isinstance(option, dict) or not all(
                isinstance(option.get(key), str) and option[key]
                for key in ("id", "label", "feedback")
            ):
                raise ValueError("每个选项需要id、label和feedback文字。")
            ids.append(option["id"])
        if len(ids) != len(set(ids)) or item["correct"] not in ids:
            raise ValueError("选项ID重复或参考答案不在选项中。")
    return items


def show_quiz(task_id: str, root: Path | str, *, display_ui: bool = True) -> QuizController:
    """显示当前任务的复盘选择题，保留编码任务与独立掌握边界。

    Args:
        task_id: course_enrichment.json中的任务ID。
        root: 仓库根目录；display_ui: False时只创建可测试控制器，不渲染输出。
    Returns:
        QuizController，可选择、提交、重试并检查真实选择记录。
    Raises:
        OSError: 配置或样式不可读取；KeyError: 任务不存在；ValueError: 题目结构不合法。
    """
    root = Path(root).resolve()
    enrichment = json.loads(
        (root / "instructor/course_enrichment.json").read_text(encoding="utf-8")
    )
    items = _validate_quiz(enrichment["tasks"][task_id]["quiz"])
    controller = QuizController(task_id, items, root)
    _display(controller.ui, root, display_ui)
    return controller


class DeskController:
    """控制真实咨询、取消与记录，只调用Notebook传入的本人异步函数。

    Args:
        module_id: 例如M01；handler: async(question, selection)返回公开字典的函数。
        root: 仓库根目录；selections: 可选的依据目录；initial_selection: 明确的初始依据ID。
        title: 读者看到的工作台标题；description: 本界面的真实能力范围。
        timeout_seconds: 整轮等待上限，最多60秒；artifact_url_prefix: Jupyter文件下载前缀。
    """

    def __init__(
        self,
        module_id: str,
        handler: DeskHandler,
        root: Path,
        *,
        selections: Mapping[str, Any] | None = None,
        initial_selection: str | None = None,
        title: str = "阿灯的接待台",
        description: str = "把问题交给阿灯，看看它实际回答了什么、依据在哪里。",
        timeout_seconds: float = 60,
        artifact_url_prefix: str = "/files/",
    ) -> None:
        if not re.fullmatch(r"M\d{2}", module_id):
            raise ValueError("module_id格式应为M01这样的模块ID。")
        if not callable(handler):
            raise TypeError("handler必须由Notebook明确传入本人异步函数。")
        if not 0 < timeout_seconds <= 60:
            raise ValueError("交互整轮超时必须在0～60秒之间。")
        if not artifact_url_prefix.startswith("/") or artifact_url_prefix.startswith("//"):
            raise ValueError("文件前缀必须是当前Jupyter服务的绝对路径。")
        self.module_id = module_id
        self.handler = handler
        self.root = root.resolve()
        self.timeout_seconds = timeout_seconds
        self.artifact_url_prefix = artifact_url_prefix.rstrip("/") + "/"
        self.selections = dict(selections or {})
        if initial_selection is not None and initial_selection not in self.selections:
            raise ValueError("初始依据不在当前目录中。")
        self.state = "idle"
        self._task: asyncio.Task[None] | None = None
        self._cancel_requested = False
        self._finishing = False
        self.last_record: dict[str, Any] | None = None
        self.last_result: dict[str, Any] | None = None
        self.run_dir: Path | None = None
        self.history: list[dict[str, str]] = []
        self.progress_events: list[dict[str, Any]] = []
        self.live_text = ""
        self.context_provider: Callable[[], dict[str, Any]] | None = None
        self.request_context: dict[str, Any] = {}
        self._scheduled_cancel: asyncio.Task[bool] | None = None
        self.question = widgets.Textarea(
            description="问题",
            placeholder="例如：本周六几点开门？",
            layout=widgets.Layout(width="100%"),
        )
        self.question.add_class("fog-question")
        options: list[tuple[str, str | None]] = [("请选择本次交来的资料", None)]
        for key, value in self.selections.items():
            label = value.get("label", key) if isinstance(value, Mapping) else str(value)
            options.append((str(label), key))
        self.selection = widgets.Dropdown(
            options=options,
            value=initial_selection,
            description="依据",
            layout=widgets.Layout(width="100%"),
        )
        self.selection.observe(self._selection_changed, names="value")
        self.send_button = widgets.Button(
            description="交给阿灯", tooltip="提交本次问题；运行中不可重复发送"
        )
        self.send_button.add_class("fog-primary")
        self.cancel_button = widgets.Button(description="停下这次办理", disabled=True)
        self.send_button.on_click(lambda _button: self.start())
        self.cancel_button.on_click(lambda _button: self._schedule_cancel())
        self.status = widgets.HTML()
        self.validation = widgets.HTML()
        self.conversation = widgets.HTML()
        self.input_evidence = widgets.HTML()
        self.output_evidence = widgets.HTML()
        self.artifacts = widgets.HTML()
        self.diagnostics = widgets.HTML()
        actions = widgets.HBox(
            [self.send_button, self.cancel_button], layout=widgets.Layout(flex_flow="row wrap")
        )
        actions.add_class("fog-actions")
        controls: list[Any] = [widgets.Label("读者的问题"), self.question]
        if self.selections:
            controls.extend([widgets.Label("这次交来的资料"), self.selection, self.input_evidence])
        controls.extend([self.validation, actions])
        form = widgets.VBox(controls)
        form.add_class("fog-controls")
        self.ui = widgets.VBox(
            [
                _header(title, description, module_id + " · 雾岛图书馆"),
                self.status,
                self.conversation,
                form,
                self.output_evidence,
                self.artifacts,
                self.diagnostics,
                widgets.HTML(
                    '<p class="fog-note">接待灯只显示本次运行状态。'
                    "答复和文件不自动代表学习任务已经完成。</p>"
                ),
            ]
        )
        self.ui.add_class("fog-root")
        self._render_history()
        self._update_input_evidence()
        self._set_state("idle")

    def _selection_changed(self, _change: dict[str, Any]) -> None:
        self._update_input_evidence()

    def _update_input_evidence(self) -> None:
        selected = self.selections.get(self.selection.value)
        evidence = selected.get("evidence", []) if isinstance(selected, Mapping) else []
        if isinstance(evidence, (str, Mapping)):
            evidence = [evidence]
        self.input_evidence.value = (
            "<details><summary>展开这次交来的原文</summary><div>"
            + _evidence_html(
                _public(evidence), "选定资料后，可在这里查看准备交给本人的函数的原文。"
            )
            + "</div></details>"
        )

    def _set_state(self, state: str) -> None:
        self.state = state
        self.status.value = (
            f'<div class="fog-status" data-state="{state}" role="status" aria-live="polite">'
            '<span class="fog-lamp" aria-hidden="true"></span><span>'
            + _STATE_TEXT[state]
            + "</span></div>"
        )

    def _render_history(self) -> None:
        if not self.history:
            self.conversation.value = (
                '<div class="fog-empty">桌上还没有问题纸。可以先问一件具体的小事。</div>'
            )
            return
        rows = []
        for message in self.history:
            label = "读者" if message["speaker"] == "visitor" else "阿灯"
            rows.append(
                f'<article class="fog-message" data-speaker="{message["speaker"]}">'
                f'<div class="fog-speaker">{label}</div><div class="fog-message-text">'
                + _escape(message["text"])
                + "</div></article>"
            )
        self.conversation.value = (
            '<div class="fog-conversation" aria-live="polite">' + "".join(rows) + "</div>"
        )

    def _lock(self, active: bool) -> None:
        self.question.disabled = active
        self.selection.disabled = active
        self.send_button.disabled = active
        self.cancel_button.disabled = not active

    def start(
        self, question: str | None = None, selection: str | None = None
    ) -> asyncio.Task[None] | None:
        """启动一次咨询；空输入或重复发送不调用handler。

        Args:
            question: 显式问题，省略时读取文本框；selection: 显式资料ID，省略时读取当前选项。
        Returns:
            当前创建的异步任务；未启动时为None。
        Raises:
            ValueError: 显式资料ID不在目录中。
        """
        if self._task is not None and not self._task.done():
            self.validation.value = (
                '<p class="fog-note" role="status">这张问题纸还在办理，请等一下或先取消。</p>'
            )
            return None
        value = self.question.value if question is None else question
        if not isinstance(value, str) or not value.strip():
            self.validation.value = (
                '<p class="fog-error" role="alert">先写下你想问的事，再交给阿灯。</p>'
            )
            return None
        if len(value) > 8000:
            self.validation.value = (
                '<p class="fog-error" role="alert">这张问题纸太长了，请先缩到8000字以内。</p>'
            )
            return None
        chosen = self.selection.value if selection is None else selection
        if chosen is not None and chosen not in self.selections:
            raise ValueError("资料ID不在当前工作台目录中。")
        if self.selections and chosen is None:
            self.validation.value = '<p class="fog-error" role="alert">先选这次交给阿灯的资料。</p>'
            return None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.validation.value = (
                '<p class="fog-error" role="alert">接待台需要正在运行的Notebook内核，'
                "请导师检查连接。</p>"
            )
            return None
        self.validation.value = ""
        self.question.value = value
        if chosen is not None:
            self.selection.value = chosen
        self._cancel_requested = False
        self._finishing = False
        self.last_result = None
        self.last_record = None
        self.progress_events = []
        self.live_text = ""
        self.request_context = _public(self.context_provider()) if self.context_provider else {}
        self.run_dir = self.root / "outputs/interactive" / self.module_id / uuid.uuid4().hex
        self.history.append({"speaker": "visitor", "text": _redact(value.strip())})
        self._render_history()
        self.output_evidence.value = ""
        self.artifacts.value = ""
        self.diagnostics.value = ""
        self._lock(True)
        self._set_state("running")
        self._task = loop.create_task(self._run(value.strip(), chosen, self.run_dir))
        return self._task

    def emit_progress(self, event: dict[str, Any]) -> None:
        """显示本人回调交来的实际阶段或普通文字片段。

        Args:
            event: stage及可选text；不得包含隐藏推理或原始模型对象。
        Returns:
            无，公开事件与界面同步更新。
        Raises:
            RuntimeError: 本次任务已停止；ValueError: 事件超出公开契约。
        """
        if self.state != "running" or self._cancel_requested:
            raise RuntimeError("本次办理已经停止，不能再写入进度")
        if not set(event) <= {"stage", "text"} or not isinstance(event.get("stage"), str):
            raise ValueError("进度只接受实际stage和普通text")
        public = _public(event)
        self.progress_events.append(public)
        if len(self.progress_events) > 500:
            raise ValueError("本次公开事件过多，请在回调合并片段后再显示")
        text = public.get("text", "")
        if not isinstance(text, str):
            raise ValueError("流式文字必须是字符串")
        self.live_text += text
        self._render_history()
        if self.live_text:
            self.conversation.value += (
                '<article class="fog-message" data-speaker="adeng"><div class="fog-speaker">'
                '阿灯 · 正在答复</div><div class="fog-message-text">'
                + html.escape(_redact(self.live_text))
                + "</div></article>"
            )
        self.status.value = (
            '<div class="fog-status" data-state="running" role="status">'
            '<span class="fog-lamp"></span>' + html.escape(public["stage"]) + "</div>"
        )

    async def submit(
        self, question: str | None = None, selection: str | None = None
    ) -> dict[str, Any] | None:
        """提交并等待本次实际运行，方便Notebook或自动化验证。

        Args:
            question: 问题或读取文本框；selection: 资料ID或读取当前选项。
        Returns:
            本次公开记录；空输入或已有运行时为None。
        Raises:
            ValueError: 显式资料ID不合法。
        """
        task = self.start(question, selection)
        if task is None:
            return None
        await task
        return self.last_record

    async def wait_idle(self) -> None:
        """等待控件已经启动的任务完成，不额外发送请求。

        Args:
            无。
        Returns:
            无。
        Raises:
            CancelledError: 调用者主动取消此等待。
        """
        if self._task is not None:
            await asyncio.shield(self._task)

    async def cancel(self) -> bool:
        """真正取消当前异步任务并等待其退出，不只更改接待灯。

        Args:
            无。
        Returns:
            是否对一个正在运行的任务发出了取消。
        Raises:
            无：取消结果作为独立运行状态记录。
        """
        task = self._task
        if task is None or task.done() or self._cancel_requested or self._finishing:
            return False
        # 让刚创建的运行任务进入自己的try/finally，立即取消也能留下真实回执。
        await asyncio.sleep(0)
        if task.done() or self._finishing:
            return False
        self._cancel_requested = True
        self.cancel_button.disabled = True
        self._set_state("cancelling")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # 任务在开始执行前被取消，没有handler动作需要继续等待。
        return True

    def _schedule_cancel(self) -> None:
        self._scheduled_cancel = asyncio.get_running_loop().create_task(self.cancel())

    def _exception_details(self, error: Exception) -> dict[str, Any]:
        frames = []
        for frame in traceback.extract_tb(error.__traceback__)[-8:]:
            filename = Path(frame.filename)
            try:
                relative = str(filename.relative_to(self.root))
            except ValueError:
                relative = filename.name
            frames.append({"file": relative, "line": frame.lineno, "function": frame.name})
        return {"type": type(error).__name__, "message": _redact(str(error)), "frames": frames}

    def _normalize_artifacts(self, values: Any) -> list[dict[str, str]]:
        if not isinstance(values, list):
            raise TypeError("artifacts必须是实际输出文件的列表。")
        artifacts = []
        for value in values:
            path_value = value.get("path") if isinstance(value, Mapping) else value
            if not isinstance(path_value, (str, Path)):
                raise TypeError("作品需要明确的path。")
            path = Path(path_value)
            if not path.is_absolute():
                path = self.root / path
            resolved = path.resolve()
            if not resolved.is_relative_to(self.root / "outputs") or resolved.name == ".env":
                raise ValueError("作品链接只允许指向本仓库outputs中的文件。")
            if not resolved.is_file():
                raise FileNotFoundError("函数声明的作品尚未实际生成：" + resolved.name)
            label = (
                value.get("label", resolved.name) if isinstance(value, Mapping) else resolved.name
            )
            artifacts.append(
                {"label": _redact(str(label)), "path": str(resolved.relative_to(self.root))}
            )
        return artifacts

    def _normalize_result(self, result: Any) -> dict[str, Any]:
        if (
            not isinstance(result, dict)
            or not isinstance(result.get("answer"), str)
            or not result["answer"].strip()
        ):
            raise TypeError("本人handler必须返回含非空answer字符串的字典。")
        evidence = result.get("evidence", [])
        if not isinstance(evidence, list):
            raise TypeError("evidence必须是本次实际依据列表。")
        _evidence_html(evidence, "")
        handler_status = result.get("handler_status", result.get("status"))
        if handler_status is not None and (
            not isinstance(handler_status, str) or not handler_status
        ):
            raise TypeError("handler_status应为非空字符串，未声明业务结果时省略它。")
        if "handler_status" in result and "status" in result and result["status"] != handler_status:
            raise ValueError("handler_status与兼容字段status不一致，不能推断办理结果。")
        response = {
            "answer": result["answer"],
            "evidence": evidence,
            "artifacts": self._normalize_artifacts(result.get("artifacts", [])),
            "handler_status": handler_status,
        }
        for key in ("trace", "memory", "status"):
            if key in result:
                response[key] = result[key]
        return dict(_public(response))

    async def _run(self, question: str, selection: str | None, run_dir: Path) -> None:
        started = time.monotonic()
        record: dict[str, Any] = {
            "kind": "interactive_run",
            "module_id": self.module_id,
            "run_id": run_dir.name,
            "started_at": _now(),
            "question": _redact(question),
            "selection": selection,
            "trusted_controls": dict(self.request_context),
            "request_status": "running",
            "handler_status": None,
            "evidence_scope": "显式传入函数的实际交互运行，不自动登记学习完成",
        }
        handler_returned = False
        try:
            await asyncio.to_thread(_write_json, run_dir / "request.json", record)
            timeout = asyncio.timeout(self.timeout_seconds)
            async with timeout:
                pending = self.handler(question, selection)
                if not inspect.isawaitable(pending):
                    raise TypeError("handler必须返回可await的结果，请传入本人异步函数。")
                result = await pending
                handler_returned = True
            if self._cancel_requested:
                raise asyncio.CancelledError
            if timeout.expired():
                raise TimeoutError("整轮等待已超过上限。")
            public_result = await asyncio.to_thread(self._normalize_result, result)
            self.last_result = public_result
            handler_status = public_result["handler_status"]
            # 未声明业务状态时只表示请求已返回；handler_status仍为None，不补造业务成功。
            state = (
                "completed"
                if handler_status is None
                else _HANDLER_STATES.get(handler_status, "unrecognized")
            )
            record.update(
                status=state,
                request_status="returned",
                handler_status=handler_status,
                result=public_result,
            )
            if state == "unrecognized":
                record["diagnostic"] = {
                    "type": "UnrecognizedHandlerStatus",
                    "message": "函数返回了未识别状态：" + handler_status,
                }
        except asyncio.CancelledError:
            record.update(
                status="cancelled",
                request_status="cancelled",
                diagnostic={"type": "CancelledError", "message": "用户取消了这次办理。"},
            )
        except TimeoutError as error:
            record.update(
                status="cancelled" if self._cancel_requested else "error",
                request_status="cancelled" if self._cancel_requested else "timed_out",
                diagnostic=self._exception_details(error),
            )
        except Exception as error:
            record.update(
                status="error",
                request_status="invalid_response" if handler_returned else "failed",
                diagnostic=self._exception_details(error),
            )
        record.update(
            finished_at=_now(),
            elapsed_seconds=round(time.monotonic() - started, 3),
            progress_events=self.progress_events,
        )
        self._finishing = True  # handler已退出，此刻只保存回执，不再显示可取消的模型动作。
        self.cancel_button.disabled = True
        try:
            await asyncio.to_thread(_write_json, run_dir / "result.json", record)
            record["saved_record"] = str((run_dir / "result.json").relative_to(self.root))
        except OSError as error:
            record["persistence_error"] = self._exception_details(error)
        self.last_record = record
        self._render_record(record)
        self._lock(False)
        self._set_state(record["status"])

    def _artifact_link(self, path: str, label: str) -> str:
        url = self.artifact_url_prefix + quote(path, safe="/")
        return (
            '<li><a href="'
            + _escape(url)
            + '" target="_blank" rel="noopener noreferrer">'
            + _escape(label)
            + "</a></li>"
        )

    def _render_record(self, record: dict[str, Any]) -> None:
        result = record.get("result")
        if result:
            self.history.append({"speaker": "adeng", "text": result["answer"]})
            self.output_evidence.value = (
                "<details open><summary>阿灯本次返回的依据</summary><div>"
                + _evidence_html(
                    result["evidence"],
                    "本次函数没有返回可核对的依据，请回到本页确认资料如何进入请求。",
                )
                + "</div></details>"
            )
            links = [
                self._artifact_link(item["path"], item["label"]) for item in result["artifacts"]
            ]
            self.artifacts.value = (
                "<details open><summary>这次真正生成的作品</summary><ul>"
                + "".join(links)
                + "</ul></details>"
                if links
                else ""
            )
        else:
            if record["status"] == "cancelled":
                text = "这次先停在这里。已经发生的动作不会自动撤销，我没有把咨询记成办妥。"
            elif record.get("diagnostic", {}).get("type") == "NotImplementedError":
                text = "这一项还没接好。请回到本页的本人代码格完成它，再来试一次。"
            elif record.get("diagnostic", {}).get("type") == "TimeoutError":
                text = "这次等得太久了，我先停下。可以查看诊断，再决定是否重新办理。"
            else:
                text = "这次没办妥。我把出错位置留在诊断里，先查清再继续。"
            self.history.append({"speaker": "adeng", "text": text})
        details: dict[str, Any] = {
            key: record[key]
            for key in (
                "run_id",
                "status",
                "request_status",
                "handler_status",
                "elapsed_seconds",
                "diagnostic",
                "persistence_error",
            )
            if key in record
        }
        if result:
            for key in ("trace", "memory"):
                if key in result:
                    details[key] = result[key]
        saved = (
            self._artifact_link(record["saved_record"], "打开本次运行记录")
            if "saved_record" in record
            else ""
        )
        warning = (
            '<p class="fog-error">本次记录未能保存，请查看写入错误。</p>'
            if "persistence_error" in record
            else ""
        )
        self.diagnostics.value = (
            "<details><summary>给学习者的诊断与运行记录</summary><div>"
            + warning
            + '<pre class="fog-pre">'
            + _escape(json.dumps(details, ensure_ascii=False, indent=2))
            + "</pre>"
            + ("<ul>" + saved + "</ul>" if saved else "")
            + "</div></details>"
        )
        self._render_history()


def show_desk(
    module_id: str,
    handler: DeskHandler,
    root: Path | str,
    *,
    selections: Mapping[str, Any] | None = None,
    initial_selection: str | None = None,
    title: str = "阿灯的接待台",
    description: str = "把问题交给阿灯，看看它实际回答了什么、依据在哪里。",
    timeout_seconds: float = 60,
    artifact_url_prefix: str = "/files/",
    display_ui: bool = True,
) -> DeskController:
    """展示模块交互台，不加载或替代任何学生实现。

    Args:
        module_id: 模块ID；handler: Notebook明确传入的本人异步适配函数。
        root: 仓库根目录；selections: {id: {label, evidence}}形式的可选依据。
        initial_selection: 明确指定初始依据；title/description: 当前真实接入能力的自然说明。
        timeout_seconds: 整轮不超过60秒；artifact_url_prefix: Jupyter文件前缀。
        display_ui: 是否实际显示。
    Returns:
        DeskController，可提交、取消并检查实际状态与产物。
    Raises:
        ValueError: 配置或ID非法；OSError: 样式不可读；TypeError: handler不合法。
    """
    root = Path(root).resolve()
    controller = DeskController(
        module_id,
        handler,
        root,
        selections=selections,
        initial_selection=initial_selection,
        title=title,
        description=description,
        timeout_seconds=timeout_seconds,
        artifact_url_prefix=artifact_url_prefix,
    )
    _display(controller.ui, root, display_ui)
    return controller
