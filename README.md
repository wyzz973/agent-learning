![雾岛图书馆：开馆行动](assets/readme-hero.svg)

# 雾岛图书馆：开馆行动

**一门从零开始、用 Jupyter 边学 Python 边造 Agent 的中文实践课程。**

[开始第一关](#当前委托) · [全馆地图](#全馆地图) · [启动工作台](#启动工作台) · [教学方法](instructor/PEDAGOGY.md)

> 图书馆准备试营业。馆长林禾把一张公告放在电脑旁：
> “门口有读者问周六几点开门。先让阿灯把这一件事做好。”

你是新人工程师，亲手建造助手 **阿灯**。它将学会依据公告回答、调用工具查资料、恢复中断的委托、组织有来源的研究、向分馆提供服务，最后在隔离环境维护自己的代码。

无需既往 Python 或 Agent 经验。每关的故事、必要写法、真实 prompt、示范、本人练习与验收都放在同一份 Notebook。主线是 **Python → LangChain → LangGraph → Deep Research → Coding Agent**。

## 当前委托

<!-- current-task:start -->
### [M01-T01 · 门口的第一位读者](modules/01-langchain-foundations/01-first-reader.ipynb)
<!-- current-task:end -->

**第一关要交付一封可以对照公告核查的读者答复。**

1. 从字符串、变量和 `print` 写下第一句话。
2. 对比真实模型“未收到公告”与“收到公告”的回答，找到资料进入请求的位置。
3. 亲手实现答复函数，处理临时公告，再接待一位询问还书箱的新读者。

完成本人代码后，Notebook会保存 `opening-answer.md` 和 `quest-evidence.json`。教师示范已有真实输出可供观察；本人练习仍由你完成，不会用教师答案兜底。

## 启动工作台

准备好 Git 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)。环境使用 Python 3.12，uv可按需准备对应版本。

```sh
git clone https://github.com/wyzz973/agent-learning.git
cd agent-learning
uv sync --locked --python 3.12
```

**首次配置模型：**将 [`.env.example`](.env.example) 另存为仓库根目录的 `.env`，填入自己的 `DEEPSEEK_API_KEY`；`DEFAULT_MODEL` 使用模板中的默认值即可。已有 `.env` 时直接沿用，不覆盖。第一关真实调用需要可用的模型服务。

```sh
uv run python -m instructor.launch
```

启动器会注册项目内核，并打开 JupyterLab 中的当前委托。也可以在支持 Jupyter 的 IDE 中打开同一份 Notebook，选择项目 `.venv` 内核。

点击一格，按 **Shift + Enter**。按顺序阅读和运行；遇到标为“本人动手”的格子，先完成其中的代码。`NotImplementedError` 表示这一步正在等你实现。环境或认证报错可以直接交给模型导师，注意不要贴出密钥。

## 一关怎样玩

**收到委托 → 预测与示范 → 学必要写法 → 亲手实现 → 对照验证 → 展示作品 → 新情况挑战。**

每关都会回答五个问题：谁需要帮助、为什么当前办不到、你要写什么、怎样证明有效、完成后留下什么。

| 你解决的事情 | 放进作品夹的成果 |
|---|---|
| 读者需要准确的开馆信息 | 有出处的答复与实际输入记录 |
| 咨询办理到一半中断 | 可以恢复的委托档案 |
| 馆长需要数字馆建设方案 | 带原文证据和未解决问题的研究报告 |
| 分馆想使用同样的能力 | 可调用的 MCP 工具与可复用的 Skill |
| 阿灯的引用组件出现缺陷 | 经过隔离测试和研究回归的源码补丁 |

**一关可以分多次学习。** 每次约一小时，在Notebook的休息点留下当前cell、卡点和下一小步。没有开馆倒计时，也不因报错扣分。提示随时可看，关键实现保留给你。

## 全馆地图

<!-- evolution-map:start -->
| 区域 | 你会接到什么委托 | 在这里学的核心技术 |
|---|---|---|
| [门厅 · 第一盏接待灯](modules/01-langchain-foundations/README.md) | 帮门口读者读懂开馆公告，让公告台显示答复。 | Python起步、消息、结构化输出 |
| [问询台 · 打开资料柜](modules/02-tools-and-agents/README.md) | 让阿灯自己申请公告和手册，处理取件失败。 | Tools、tool calling、执行器、错误反馈 |
| [委托台 · 把事情办完](modules/03-langgraph-control/README.md) | 连续查资料、分流问题，让读者看到进度并能取消。 | LangGraph状态、节点、反馈循环、事件 |
| [值班室 · 交班不失忆](modules/04-memory-and-human-review/README.md) | 断电后接续委托，记住确认信息，保留可核对的经验。 | 检查点、HITL、长期记忆、上下文、Reflexion |
| [研究阅览室 · 为数字馆查证](modules/05-deep-research/README.md) | 为阿灯的建设方案寻找真实技术依据，补足研究缺口。 | 搜索/fetch、RAG、证据、自适应研究 |
| [服务台 · 接受开馆验收](modules/06-research-system/README.md) | 研究者分工，定位失败，让另一台设备使用阿灯。 | 协作、评估、消融、tracing、服务交付 |
| [交换站 · 分享工具和方法](modules/07-protocols-and-skills/README.md) | 把资料工具与核查方法交给分馆，比较成熟装配方式。 | MCP、Skills、按需工具发现、DeepAgents |
| [维修间 · 阿灯维护自己](modules/08-coding-agent/README.md) | 修复数字馆的真实组件，中断后还能继续维修。 | coding agent、隔离执行、harness、源码迁移 |

全馆设计了 **28 项委托**；目前 **1 关教材可开始**，0 关编写中，27 关待编写。故事地图和prompt设计完成，不代表全部Notebook已经制作完成。
<!-- evolution-map:end -->

地图中的委托有明确的学习目标、本人控制点、作品奖励、对照实验和迁移挑战。模块索引用于了解路线；实际学习始终从首页的当前Notebook进入。

## Prompt 与代码都在故事里

阿灯的身份、岗位、读者或馆长的委托、可用信息和完成条件会写入实际模型prompt。第一关使用的[系统提示原文](world/prompts/M01-T01.md)也会在Notebook中显示，随后真正传入 `SystemMessage`。

研究者、调度模块、记忆、工具、Skills和维修任务都服务于这座图书馆。技术名称保持准确：**Tools负责执行，MCP负责连接，Skills保存方法，memory保存并取回信息，LangGraph管理状态与控制。**

馆务与人物属于虚构教学场景；研究任务使用的公开技术资料需要记录真实URL、取得时间和原文证据。

## 怎样判断自己学会了

分别保留三种证据：**程序实际运行、本人能解释、换输入仍能完成。**

教师提供环境、完整示范、局部提示和验收设施；你组织关键实现。运行成功后，还要解释数据怎么流动，并尝试一个陌生输入。故事奖励与学习掌握不会自动画等号。

| 目录 | 用途 |
|---|---|
| [`modules/`](modules/) | 区域索引与可学习的Notebook |
| [`world/`](world/) | 公告等场景素材、各关实际prompt |
| [`project/`](project/) | 在课程中逐步积累的本人作品 |
| `outputs/` | 本机实际运行产生的答复、报告和记录 |
| [`instructor/`](instructor/) | 导师维护的任务目录、状态、检查和依据 |

需要模型导师帮助时，可以直接说：**“请读仓库规则和当前学习状态，从我正在看的cell开始解释。”** `AGENTS.md` 与指向它的 `CLAUDE.md` 为不同harness提供同一套教学约定。

## 教材依据与验证

课程设计参考 [LangChain Academy](https://academy.langchain.com/) 和 [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)，并核查 MCP、Agent Skills、Deep Agents 与相关研究的适用边界。

- [教学依据](instructor/PEDAGOGY.md)：示范、练习、反馈与迁移怎样安排。
- [技术调研](instructor/RESEARCH.md)：官方来源、版本与仍在变化的接口。
- [作品约定](project/README.md)：阿灯的数据与代码职责。
- [教师验证记录](instructor/validation.json)：第一关实际运行的范围；不代表本人通关。

维护教材时使用：

```sh
uv run python -m instructor.check
uv run pytest instructor/tests -q
uv run ruff check instructor
uv run mypy instructor
```

这些检查不调用模型，也不填写本人练习。密钥、运行产物和本机逐字对话日志不进入公开仓库。
