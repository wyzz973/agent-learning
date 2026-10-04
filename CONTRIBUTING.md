# 参与雾岛图书馆

欢迎帮助课程变得更清楚、可运行、可核查。最有用的贡献来自具体学习障碍：哪一格难以理解，哪份输入触发了错误，哪个概念与实际代码不一致。

## 报告问题

在 [Issues](https://github.com/wyzz973/agent-learning/issues/new/choose) 中注明模块与任务、Notebook 的 cell ID、复现步骤、预期和实际结果。涉及环境时附操作系统、Python 和依赖版本。密钥、请求头、私有输入及模型内部推理不进入公开问题。

原理或 API 纠错请提供官方文档、论文或最小运行证据，并说明检查的版本。故事素材是虚构馆务；研究公开技术资料时记录真实 URL、取得时间和支持结论的原文。

## 开始修改

Fork 后从当前 `main` 建立分支，例如 `codex/clarify-tool-receipts`，安装锁定环境：

```sh
uv sync --locked --python 3.12
```

先读根目录 [AGENTS.md](AGENTS.md) 和目标模块的 `AGENTS.md`，再读 `instructor/state.json`、`instructor/catalog.json` 与目标 Notebook。保留已有本人代码和学习证据；发布教材与推进学习状态分别处理。

课程用英文 Python 标识符、类型注解和中文解释。公开函数说明 Args / Returns / Raises。新机制需要原位解释输入、处理、输出和失败，先展示可运行示范，再给本人契约、分层提示、对照和迁移检查。

## 修改正确的来源

| 要修改的内容 | 主要来源 | 同步方式 |
|---|---|---|
| 任务、角色、状态和 prompt | `instructor/catalog.json` | `instructor.render_curriculum` |
| 原理、判断题、小步观察与源码拆解 | `instructor/course_enrichment.json` | `instructor.render_curriculum` |
| 模块业务、架构与生产项目 | `instructor/module_blueprints.json`、`instructor/blueprints/` | 按导师目录说明同步对应教材 |
| 教师示范与设施 | 目标 Notebook 的 `setup/demo`、对应 Python 模块 | 校验引用、导出与实际执行 |
| 当前学习入口 | `instructor/state.json` | 仅在确需切换时使用 `instructor.sync_entry` |

生成区有明确标记。修改源数据后，在仓库根目录运行：

```sh
uv run --locked python -m instructor.render_curriculum
```

随后核对 diff。不要用生成器覆盖本人 `exercise/exercise-test` 的源码、元数据或已保存输出，也不要新增隐藏学生答案或教师回退。

新任务先保留 `planned/draft` 状态；只有讲授、示范和验证完整的 Notebook 才可进入 `ready`。章末接待台要明确调用本人组件，缺少能力时展示接线缺口。

## 验证

提交前使用与 CI 一致的无密钥检查，并核对生成内容：

```sh
uv run --locked python -m instructor.render_curriculum --check
uv run --locked python -m instructor.check
uv run --locked python -m instructor.check_export_contracts
uv run --locked python -m instructor.lint_notebooks
uv run --locked ruff check instructor tests modules --exclude '*.ipynb'
uv run --locked mypy
uv run --locked pytest -q
```

`lint_notebooks` 的教师门禁检查 `setup/demo`；本人及 `exercise-test` 的样式诊断分别列出。同来源分格重复导入有公开解释。设施测试与教师门禁不证明本人掌握。

教师源码或实际 prompt 改动后，在自己的 `.env` 配置下执行受影响的真实示范。下面的命令会调用模型并更新全馆教师输出，维护者按需要使用：

```sh
uv run --locked python -m instructor.validate_notebooks --refresh-demo-outputs
```

执行器跳过本人格。注明运行范围、真实模型与替身测试、跳过项目和未解决问题；具体命令选项可用 `--help` 查询。仅修改文档排版时无需重跑无关模型。

## 提交 Pull Request

说明具体问题、修改后的行为或学习体验，以及实际验证范围。涉及学习顺序或技术原理时附依据。README 中的模块数、题数和执行结果必须与当前目录及记录一致。

提交前核对 diff，确认 `.env`、本机 `outputs/` 和 `instructor/qa/` 对话记录未进入版本库。保留验证中的失败与限制，不把计划、教师运行或文件存在写成本人通关。

仓库当前未指定许可证，许可状态见根 [README](README.md#致谢与许可)。
