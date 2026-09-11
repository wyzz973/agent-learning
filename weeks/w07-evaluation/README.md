# w07 — 证据、评分与首月交付

## 目标

检查回答引用的路径 → 用固定样例算通过率 → 理解结构化输出的三层 → 复测同一应用与理解前沿地图 → 首月作品验收与重写。每天的做什么、为什么、核心思想和验收都在任务卡，按顺序逐张打开。

## 每日任务

- [D16 · 检查回答引用的路径](../../curriculum/tasks/D16.md)
- [D17 · 用固定样例算通过率](../../curriculum/tasks/D17.md)
- [D18 · 理解结构化输出的三层](../../curriculum/tasks/D18.md)
- [D19 · 复测同一应用与理解前沿地图](../../curriculum/tasks/D19.md)
- [D20 · 首月作品验收与重写](../../curriculum/tasks/D20.md)

## 自检标准

- [ ] 所有本人练习测试通过，能解释每个函数的输入、返回与失败情况。
- [ ] 关掉示范换数据重写本周一个关键函数。
- [ ] 跑通本周应用入口，分清脚本回放、真实工具执行与真实模型调用。

## Build It — 手写版

文件：ex1_eval.py、structured_demo.py。先运行 00_warmup.py，再按 unknown_paths → score_cases；随后验证整个应用入口 完成。注释中文；教师写示范/骨架，TODO 与独立段由本人写。

## Use It — 框架版

| 本人实现/观察 | 框架对应能力 | 本人解释责任边界 |
|---|---|---|
| 本周的状态或结果处理 | LangGraph / Pydantic | |
| 正常与失败路径 | 错误消息/状态或校验反馈 | |

## Ship It — 带走的工件

从新终端按 README 跑工具/循环/图；本人改一条需求再测试；写复盘。跨周应用用 src/agentlab/course_runtime.py 调用已有本人实现，不复制答案。学习代码未完成时入口明确报错。

## 运行

```sh
uv run python weeks/w07-evaluation/00_warmup.py
uv run pytest weeks/w07-evaluation -k demo -q
uv run pytest weeks/w07-evaluation -q
./check.sh --week w07
```



```sh
uv run python weeks/w07-evaluation/structured_demo.py
uv run python scripts/run_course_app.py --mode evaluate
uv run python scripts/run_course_app.py --mode graph
```

首月验收：新终端重跑 tool/loop/langchain/graph/evaluate 五个入口；各自有实际结果。评估数据在 curriculum/fixtures/search_cases.json，仅评确定性检索工具；模型回答质量需单独验证。本人解释消息轨迹、改一条需求、补对应测试，并记录重写证据。有 key 时加 --live，保存真实模型与工具消息；未运行就写未验证。

## 教材与学习进度

教材准备检查：1 条示范通过，3 条练习规格待本人完成；热身与完整教师示范可运行。这是教材状态，不是学习者已掌握；真实模型尚未在本轮调用。

## 卡住的地方

（本人填写具体函数、预期输出、实际报错和处理办法。）
