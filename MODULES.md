# 模块地图

| 模块 | 责任 | 规则 |
|---|---|---|
| 根目录 | 总路线、共同教学规则、当前状态、术语/API | [AGENTS](AGENTS.md) |
| curriculum | 60 张任务卡、研究依据、开周标准 | [AGENTS](curriculum/AGENTS.md) |
| curriculum/tasks | 一天一张教学契约，任务顺序以 course.json 为准 | [AGENTS](curriculum/tasks/AGENTS.md) |
| weeks | 可运行教材与本人练习，已完成周冻结 | [AGENTS](weeks/AGENTS.md) |
| weeks/w01～w03 | 历史学习代码，保持冻结 | [w01](weeks/w01-python-foundations/AGENTS.md) / [w02](weeks/w02-bare-agent/AGENTS.md) / [w03](weeks/w03-langchain-core/AGENTS.md) |
| weeks/w04-python-tools | 列表字典与工具返回值 | [AGENTS](weeks/w04-python-tools/AGENTS.md) |
| weeks/w05-files-loop | 文件读取、消息、有限 agent 循环 | [AGENTS](weeks/w05-files-loop/AGENTS.md) |
| weeks/w06-langgraph | 状态、路由、图与暂停恢复 | [AGENTS](weeks/w06-langgraph/AGENTS.md) |
| weeks/w07-evaluation | 证据约束、结构化数据、评估与首月交付 | [AGENTS](weeks/w07-evaluation/AGENTS.md) |
| src/agentlab | 跨周应用连接与可复用模块 | [AGENTS](src/agentlab/AGENTS.md) |
| scripts | 教师维护的课程入口与验证工具 | [AGENTS](scripts/AGENTS.md) |
| tests | 仓库基础设施与教材规则测试 | [AGENTS](tests/AGENTS.md) |
| notes | 本人复盘、逐字问答、决策依据 | [AGENTS](notes/AGENTS.md) |
| templates | 新任务/新周/交接的模板 | [AGENTS](templates/AGENTS.md) |

每行模块均有同目录 CLAUDE.md 链接到 AGENTS.md。w01～w03 沿用 weeks 的冻结规则；后续新周开课时必须同时建立模块规则和教材，不提前建立充满占位文件的空周。
