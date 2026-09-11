# w05 — 真实文件与有限 agent 循环

## 目标

把磁盘文件读成工具结果 → 给工具建立名字索引 → 接通模型—工具—模型循环 → 同一工具运行两种 agent → 复盘数据流与失败路径。每天的做什么、为什么、核心思想和验收都在任务卡，按顺序逐张打开。

## 每日任务

- [D06 · 把磁盘文件读成工具结果](../../curriculum/tasks/D06.md)
- [D07 · 给工具建立名字索引](../../curriculum/tasks/D07.md)
- [D08 · 接通模型—工具—模型循环](../../curriculum/tasks/D08.md)
- [D09 · 同一工具运行两种 agent](../../curriculum/tasks/D09.md)
- [D10 · 复盘数据流与失败路径](../../curriculum/tasks/D10.md)

## 自检标准

- [ ] 所有本人练习测试通过，能解释每个函数的输入、返回与失败情况。
- [ ] 关掉示范换数据重写本周一个关键函数。
- [ ] 跑通本周应用入口，分清脚本回放、真实工具执行与真实模型调用。

## Build It — 手写版

文件：ex1_files.py、ex2_loop.py。先运行 00_warmup.py，再按 read_text_tool → index_tools → run_agent → successful_paths 完成。注释中文；教师写示范/骨架，TODO 与独立段由本人写。D10 的 successful_paths 是把 w04 的筛选结构迁移到文件结果，预计十分钟内完成。

## Use It — 框架版

| 本人实现/观察 | 框架对应能力 | 本人解释责任边界 |
|---|---|---|
| run_agent 循环 | create_agent | |
| 正常与失败路径 | 错误消息/状态或校验反馈 | |

## Ship It — 带走的工件

用空关键词/缺文件/连续调用验证；重写工具索引并画四类消息。跨周应用用 src/agentlab/course_runtime.py 调用已有本人实现，不复制答案。学习代码未完成时入口明确报错。

## 运行

```sh
uv run python weeks/w05-files-loop/00_warmup.py
uv run pytest weeks/w05-files-loop -k demo -q
uv run pytest weeks/w05-files-loop -q
./check.sh --week w05
```

```sh
uv run python scripts/run_course_app.py --mode tool
uv run python scripts/run_course_app.py --mode loop
uv run python scripts/run_course_app.py --mode langchain
```

工具模式只执行 Python；后两种默认用固定 retry 回放剧本。本人逻辑和文件读取实际运行，回放不证明自主规划或回答质量。完成后可选 --live 使用 .env 模型。



## 教材与学习进度

教材准备检查：4 条示范通过，7 条练习规格待本人完成；热身与完整教师示范可运行。这是教材状态，不是学习者已掌握；真实模型尚未在本轮调用。

## 卡住的地方

（本人填写具体函数、预期输出、实际报错和处理办法。）
