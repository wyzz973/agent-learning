# w06 — 状态图、路由与恢复

## 目标

状态与分支路由 → 亲手连接一张图 → 看见中间步骤并保存会话 → 暂停等待人再恢复 → 把自己的 agent 放入图。每天的做什么、为什么、核心思想和验收都在任务卡，按顺序逐张打开。

## 每日任务

- [D11 · 状态与分支路由](../../curriculum/tasks/D11.md)
- [D12 · 亲手连接一张图](../../curriculum/tasks/D12.md)
- [D13 · 看见中间步骤并保存会话](../../curriculum/tasks/D13.md)
- [D14 · 暂停等待人再恢复](../../curriculum/tasks/D14.md)
- [D15 · 把自己的 agent 放入图](../../curriculum/tasks/D15.md)

## 自检标准

- [ ] 所有本人练习测试通过，能解释每个函数的输入、返回与失败情况。
- [ ] 关掉示范换数据重写本周一个关键函数。
- [ ] 跑通本周应用入口，分清脚本回放、真实工具执行与真实模型调用。

## Build It — 手写版

文件：ex1_graph.py、recovery_demo.py。先运行 00_warmup.py，再按 choose_route → build_search_graph；随后运行恢复示范 完成。注释中文；教师写示范/骨架，TODO 与独立段由本人写。

## Use It — 框架版

| 本人实现/观察 | 框架对应能力 | 本人解释责任边界 |
|---|---|---|
| 本周的状态或结果处理 | LangGraph / Pydantic | |
| 正常与失败路径 | 错误消息/状态或校验反馈 | |

## Ship It — 带走的工件

运行空输入和有效输入；画图；关掉示范重写路由。跨周应用用 src/agentlab/course_runtime.py 调用已有本人实现，不复制答案。学习代码未完成时入口明确报错。

## 运行

```sh
uv run python weeks/w06-langgraph/00_warmup.py
uv run pytest weeks/w06-langgraph -k demo -q
uv run pytest weeks/w06-langgraph -q
./check.sh --week w06
```


```sh
uv run python weeks/w06-langgraph/recovery_demo.py
uv run python scripts/run_course_app.py --mode graph
uv run python scripts/run_course_app.py --mode graph --query ""
```

recovery_demo 是完整教师示范，输入 True/False 模拟人的决定。仅证明同一进程内暂停与恢复，不证明数据库持久化；真实跨进程恢复在 w09。


## 教材与学习进度

教材准备检查：1 条示范通过，3 条练习规格待本人完成；热身与完整教师示范可运行。这是教材状态，不是学习者已掌握；真实模型尚未在本轮调用。

## 卡住的地方

（本人填写具体函数、预期输出、实际报错和处理办法。）
