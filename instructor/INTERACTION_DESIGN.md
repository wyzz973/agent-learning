# 雾岛图书馆 · 模块交互工作台规范

本文件供导师与界面实现者维护，不增加学习入口。学习者仍在当前 Notebook 内读故事、写核心代码、运行检查；每个模块末尾用同一套工作台操作自己的成果，复盘改为选择题，编码任务保留。

## 体验与视觉语言

工作台像馆内一张可使用的纸质接待桌：纸色 `#f5f1e6` 作背景，深绿 `#203e42` 作正文、结构线和主要按钮，金色 `#9b7939` 只作书脊、分隔线和接待灯的强调。小书架说明所在空间，不承载进度或奖励。中文标题用宋体风格，正文用清晰无衬线字体；使用本机字体栈，不联网加载字体。

正文深绿对纸色的对比度约 10.17:1，次要文字 `#526669` 约 5.37:1，错误文字 `#8b302b` 约 7.28:1。金色约 3.59:1，不用于小号正文。状态始终同时显示文字，不能只让灯变色。运行中接待灯轻微明暗变化，`prefers-reduced-motion` 下关闭动画。键盘聚焦用深绿 3px 轮廓；按钮和选项至少 42～44px 高，窄屏自动换行，不要求横向拖动。

界面分为两层：

- **面向读者的主界面**：具体问题、这次交来的资料、阿灯的自然答复、可核对依据和真实作品。
- **面向学习者的折叠区**：本次运行 ID、状态、耗时、公开工具轨迹、明确返回的记忆信息、异常类型与代码位置。密钥、请求头和隐藏推理不进入这些区域。

未接入的能力不摆可点击按钮，不显示“已解锁”。没有虚拟 XP、排行榜或自动通关动画。作品文件生成可作为真实运行证据，不能自动认证本人掌握。

ipywidgets子控件默认带左右边距，`width:100%`叠加边距会产生横向溢出。工作台范围内将子`jupyter-widgets`的左右边距归零，统一`border-box`并允许flex输入收缩；垂直间距仍由工作台控制。不得用`overflow-x:hidden`遮掉问题或裁切键盘聚焦轮廓。真实浏览器验收需核对工作台、表单与题卡的`scrollWidth <= clientWidth`，并检查窄屏和聚焦状态。

## 复盘选择题

`show_quiz(task_id, root)` 从 `instructor/course_enrichment.json` 读取 `tasks[task_id].quiz`。每任务建议两题，内容针对刚刚实现的因果关系；不能用选择题代替写代码、解释和陌生输入迁移。

题目结构为：

```json
{
  "id": "stable-question-id",
  "prompt": "需要学习者判断的具体问题",
  "options": [
    {"id": "a", "label": "一个判断", "feedback": "这个判断成立或不成立的原因"},
    {"id": "b", "label": "另一个判断", "feedback": "与当前代码或数据流对应的解释"}
  ],
  "correct": "b",
  "concept": "本题希望辨清的机制"
}
```

所有题目初始均不选中，提交按钮不可用。选择后本人点击“看看我的判断”，再显示各选项解析；“再想一次”清空当前选择和解析，但不删除之前的记录。反馈说明错误发生在哪个理解层，不用笼统夸奖或只给红绿分数。

每次提交追加 `outputs/learning/attempts.jsonl`：任务、题目、选择、时间、是否与参考一致及“仅选择证据”的范围。记录使用 `schema_version=2`，保存提交时的 `question_snapshot`（题干、概念、当时顺序的选项 ID／文字／解析及参考 ID），另存 `selected_label` 和 `expected_label`。`question_sha256` 对该快照按 UTF-8、JSON 键排序与固定分隔符计算，指向本次实际题意；选项重排或改字会产生不同指纹。

复查历史选择时必须使用记录内快照，不能拿当前题库解释以前的“A/B/C/D”。新格式不回填或猜测缺少快照的早期记录；这些记录只能说明保存过哪个选项 ID。快照与解析在本人提交后才记录，不新增预选或提前揭示答案。组件不写 `instructor/state.json`，不创建 mastery 或课程 completed 字段。

返回的 `QuizController` 可直接验证：`choose(question_id, option_id)`、`submit(question_id)`、`retry(question_id)`；`questions`、`feedback` 和 `last_attempts` 可检查。`display_ui=False` 仅供自动化验证，不自动选择或答题。

## 本人作品接入契约

调用入口是 `show_desk(module_id, handler, root, ...)`。`handler` 必须由当前 Notebook 明确传入，接线适配可以由导师写，实际能力必须调用本人已经完成的函数。禁止从磁盘自动执行 Notebook、隐式 import 未完成代码、回退到教师模型，或替本人补 TODO。

异步 handler 的输入为 `question: str`、`selection: str | None`；后者是本次选择的资料 ID。返回公开字典：

| 字段 | 含义与限制 |
|---|---|
| `answer` | 必需，非空的实际答复文字；作为纯文本安全显示，不执行 HTML |
| `evidence` | 可选列表；每项为文本或含 `source_id/id`、`title`、`text/content/excerpt`、`url` 的字典；只放本次实际依据 |
| `artifacts` | 可选列表；每项为路径或 `{path, label}`；必须是本仓库 `outputs/` 下已经存在的文件 |
| `trace` | 可选，JSON 可序列化的公开工具或阶段记录，不传原始消息对象 |
| `memory` | 可选，本次实际读取或改变的公开记忆记录；没有读过就不填写 |
| `handler_status` | 可选，函数明确声明的业务状态；兼容 `status` 字段，若两者同时存在必须一致。未提供时保留为 null，不补造业务成功 |

`selections` 为 `{资料ID: {label, evidence}}`，用于选择与预览本次交来的原文。**预览原文不等于模型已经使用它**：发送后“阿灯本次返回的依据”只显示 handler 实际返回的 evidence，不能自动把所选资料当成工具调用证据。`initial_selection` 只在 Notebook 明确指定时设置；选择题始终无默认答案。

M01 接线示意仅需绑定明确的本人适配函数：

```python
from instructor.interaction import show_desk

desk = show_desk(
    "M01", handler=my_desk_handler, root=ROOT,
    selections=my_notice_choices,
    title="阿灯的门厅接待台",
    description="选一张公告，问阿灯一件具体的馆务小事。",
)
```

`my_desk_handler` 如何调用本人 `answer_reader` 及返回实际依据，由该 Notebook 明确展示。设施不会替它生成答案。当前输入只包含本次问题与 selection；界面上的历史气泡不会偷偷进入模型上下文，也不能据此宣称已经有对话记忆。需要历史或流式事件时由相应模块扩展显式契约。

## 状态、取消与真实记录

`DeskController` 提供 `start()`、`await submit()`、`await cancel()`、`await wait_idle()`；可测试控件为 `question`、`selection`、`send_button`、`cancel_button`。按钮事件与这些方法走同一执行路径，不维护一套只供测试的模拟逻辑。

空白问题和未选必要资料不调用 handler；运行中冻结输入、防止重复发送。外层 `asyncio.timeout` 最多 60 秒，底层模型函数继续保留自己的单次超时和调用预算。取消实际调用 `Task.cancel()` 并等待退出；handler 必须允许取消传播，并在自己的 finally 里回收工具进程或容器。取消不能撤销已经发生的外部写入，不显示“已回滚”。

运行记录明确区分三层：`request_status` 表示调用生命周期（`running`、`returned`、`cancelled`、`timed_out`、`failed`、`invalid_response`）；`handler_status` 保留本人函数声明的业务状态；`status` 是据此产生的界面状态。函数正常返回了“缺少证据”，仍是请求 `returned`，但业务没有完成。

- `completed`、`success`、`ok`、`answered`、`verified` 才映射到普通答复返回状态。
- `budget_exhausted`、`blocked`、`needs_attention`、`incomplete`、`needs_evidence`、`paused`、`pending` 显示未办完。
- `needs_confirmation`、`awaiting_confirmation`、`awaiting_approval` 显示待确认；当前工作台不会自动批准或继续办理。
- `failed`、`error` 显示办理失败；`cancelled`、`canceled` 显示取消。它们若由handler正常返回，`request_status` 仍是 `returned`，与外层取消或请求异常区分。
- 未认识的非空状态原样保留，界面显示状态待核对，诊断标明 `UnrecognizedHandlerStatus`，不能静默归为完成。非字符串或互相冲突的声明作为 `invalid_response` 报错。
- 没有声明业务状态时，界面仅显示“答复已返回”，`handler_status=null`，不能推断业务已经完成或学习者已掌握。

运行状态因此涵盖待接待、办理中、取消中、答复已返回、未办完、待确认、状态待核对、已取消与失败。`NotImplementedError` 显示“本人代码尚未接好”；异常不会被改造成成功回答。诊断保留异常类型、去除凭据后的原因、文件与行号，不记录 traceback 中的源代码行或原始模型响应。

每次实际启动使用新目录 `outputs/interactive/M01/<run-id>/`（其他模块替换 M01），保存 request.json 与 result.json。此前作品不覆盖，quiz记录与desk记录也不混用。写入失败必须明确显示“记录未保存”；函数声称生成但实际不存在的作品不得展示下载链接。默认文件链接使用本地 Jupyter 的 `/files/` 路由，服务有前缀时用 `artifact_url_prefix` 显式配置。

## 十个模块的业务接入

下面是业务验收目标。十章统一界面设施已经提供，每章本人module_agent需要按此完成行为接线；**M01已有保存的本人函数可真实演示**。专用业务尚未完成时显示缺口，控件存在不代替行为证据。

| 模块 | 交互目标 | 接入前必须验证 |
|---|---|---|
| M01 门厅 | 选择公告、提出问题、核对答复与出处 | 调用本人 answer_reader，换公告影响实际输入，保存本人结果 |
| M02 问询台 | 查看取件请求、回执和退件原因 | 工具轨迹来自真实调用；未取得原文不能显示已取得 |
| M03 委托台 | 查看实际阶段进度并取消 | 阶段事件由本人图产生；取消真正停止并回收任务，不能播放固定进度 |
| M04 值班室 | 选择会话、恢复、核对和撤回记忆 | session 与 user 明确；界面状态来自实际持久化记录 |
| M05 研究阅览室 | 提交研究范围、展开来源与证据缺口 | 原文 URL、获取时间、证据位置可核对，报告消费本人的研究产物 |
| M06 服务台 | 比较运行、查看评估与服务请求 | 另一客户端实际调用、质量结果和失败轨迹对应同一请求 |
| M07 交换站 | 发现工具、查看方法实际加载情况 | MCP发现和调用分别记录；Skill正文确实按需加载，不能只列配置 |
| M08 维修间 | 查看修改提议、许可、diff和执行结果 | 本人控制函数运行，测试版本与候选SHA一致；执行仅在受限容器 |
| M09 运行室 | 真实流式片段、调用/缓存、接口与身份边界 | 事件来自实际回调，失败尝试计数，缓存绑定当前输入，不跨user |
| M10 验收桌 | 选择本人能力、查看端到端与发布凭据 | 未批准不写、规则/语义分开、留出不泄漏、当前SHA对应实际验证 |

M03可通过emit_progress显示实际阶段，M04/M08有办理和一次性许可控件，返回trace/memory在折叠区核对。专用会话列表、逐文件diff等可在本模块完成前扩展，不能假装尚未完成的本人恢复/维修已发生。当前通用设施与这些业务能力分开验收。

## 接入完成标准

2026-10补充：10章末页已提供`show_module_workspace`与本人`module_agent(question, selection, controls)`契约。身份、办理方式和一次性许可由真实控件确定，办理中锁定，许可读取后清空；所有尚未完成的本人组件仍明确失败。`DeskController.emit_progress`只接受本人实际回调的stage/text，保存公开事件，任务结束后拒绝晚到事件。界面设施完成与本人行为完成分别记录。M03、M04、M08的专用业务逻辑由本人接线，不因控件存在自动宣称恢复或修改完成。

每个模块界面达到以下条件才可称为已接入：

1. Notebook展示实际绑定的本人函数，缺失实现明确失败；替身测试证明调用参数和路径，但真实模型验收另行记录。
2. 本人完成一次正常任务、一次失败或取消、一次改变资料/输入的迁移；界面、记录文件与真实输出一致。
3. 可从键盘选择、提交、取消、重试和展开依据；窄屏无必需横向滚动，减少动态效果设置生效。
4. 原文、结果、未完成与实际产物分开；凭据与隐藏推理不出现，外部文本不能变成可执行HTML。
5. 复盘先选后解释，记录仅代表选择；界面不改变通关状态、不产生虚假奖励，编码仍由本人完成。
6. 在重启Notebook内核后重新创建界面，能再运行；不依赖上一次内核残留对象，也不自动调用其他模型补缺口。

自动化验证：`uv run pytest tests/test_interaction.py -q`。这些测试使用替身，不证明真实模型效果或视觉验收；M01本人函数接入、真实输出与浏览器呈现需要单独核查。
