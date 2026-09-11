# 换模型也能接着学

## 启动顺序

任何模型都先运行 `uv run python scripts/learn.py --handoff`，然后读根 AGENTS.md、COURSE_STATE.json、当前任务卡、目标目录规则、实际练习。首次回复用三句话说明：当前任务、已核实的卡点、今天第一个小动作。不得只凭上一个模型的聊天断言宣布完成。

Codex 按项目根到启动目录发现规则；从根启动后要主动读目标模块规则，不能假设所有后代文件都已加载。[Codex 官方说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。

Claude Code 支持项目与子目录 CLAUDE.md；本仓库让它们链接同目录 AGENTS.md，保持同一份文本。其他模型若不自动读规则，手动提供同一入口。[Claude Code 官方说明](https://code.claude.com/docs/en/memory)。

## 状态只记证据

COURSE_STATE.json 是进度真源，字段含义：

| 字段 | 含义 |
|---|---|
| active_task | 唯一当前任务，D01～D60 |
| progress | 已开始任务的记录；没有记录就是未开始 |
| status | in_progress / needs_practice / completed |
| learner_evidence | 本人解释、独立写作或重写的实际证据，未知留空 |
| checks | 本次实际运行的命令、退出码、结果；不能写计划命令冒充证据 |
| blocker | 当前具体困难，不能用“Python 不会”代替某个函数/语法 |
| next_action | 下次落笔的动作，例如“在 find_matches 判断当前 record” |
| materials | 教材准备状态，和学习进度分开 |
| updated_at | 最后实际更新的本地日期时间 |

completed 必须有 learner_evidence 与成功验收证据；讲解/阅读课也须有本人解释和题目核对记录。检查器只能检查记录结构，不能证明独立性；导师必须诚实记录。

## 每次离开前

先重读状态与 git diff，只更新本次任务，防止覆盖另一个模型的新记录。不自动修改 active_task 跳课。把新卡点和最小下一步写清；原问答追加 notes/qa，较长命令结果可存 artifacts/ 并引用。日志不保留密钥、隐私正文或模型隐藏推理。

两个模型不同时编辑同一练习；另一个可以只读 review。发现状态与代码矛盾先实际检查，保留已有记录并注明纠正原因。禁止回滚本人代码来适配自己的方案。

## 可以直接发给其他模型

> 请作为我的 Python + agent 导师继续本仓库。先读 AGENTS.md、COURSE_STATE.json，运行 `uv run python scripts/learn.py --handoff`，再读当前任务和目录规则。先确认我在哪个具体动作卡住；按“输入是什么、一步做什么、返回给谁”解释。注释中文，保留 TODO 和独立题给我写。只登记实际证据，结束前更新状态并逐字记问答。不要替我赶进度。

本协议保证可携带的上下文材料；不同产品是否遵循指令仍需实际检查，不能保证它们自动共享聊天历史。
