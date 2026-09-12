# Week 04 — 用 Python 写一个 agent 搜索工具

> 按实际开始日安排 5 次学习，每次最多 60 分钟 ｜ 对应 [学习路线](../../LEARNING_PATH.md) 第 4 周

每日具体任务以 [D01～D05](../../curriculum/units/w04.md) 为准；当前任务由 COURSE_STATE.json 指定。

## 文件读哪个、什么时候读

按这个顺序，不用管编辑器里的字母排序。每个文件第一行也标了同样的信息。

| 读的顺序 | 文件 | 什么时候用 | 含哪个练习 |
|---|---|---|---|
| 1 | [00_warmup.py](00_warmup.py) | Day 1-3 开头 | 无，只读只跑，预测 print 结果 |
| 2 | [sample_repo.py](sample_repo.py) | 全周 | 无，本周的数据，不用改 |
| 3 | [ex1_records.py](ex1_records.py) | Day 1-2 | **练习 1、2** |
| 4 | [ex2_search_tool.py](ex2_search_tool.py) | Day 3-4 | **练习 3、4** |
| 5 | [warmup_tools.py](warmup_tools.py) | Day 4 开头 | 无，只读只跑 |
| 6 | [agent_demo.py](agent_demo.py) | Day 4 末尾 | 无，只运行；三种跑法见下 |
| 7 | `recall.py` | Day 5 | **练习 5** ← 这个文件由你创建，仓库里现在没有 |
| 8 | [test_w04.py](test_w04.py) | 每天结尾 | 无，不用改，你的实现要让它变绿 |
| — | [test_w04_bridge.py](test_w04_bridge.py) | 不用管 | 无，检查教师连接代码 |


## agent_demo.py 的三种跑法

```sh
uv run python weeks/w04-python-tools/agent_demo.py                 # 只调工具，不联网
uv run python weeks/w04-python-tools/agent_demo.py --live          # 调真实模型，看消息轨迹
uv run python weeks/w04-python-tools/agent_demo.py --live --debug  # 额外看链路与请求/响应 JSON
```

`--debug` 会打印三样东西，都是平时看不到的：

| 打印什么 | 为什么值得看 |
|---|---|
| LangChain 链路 | 一次运行里，middleware、模型、工具各被调用了几次、按什么顺序 |
| 发出的请求 JSON | **你写的工具 docstring 原样出现在 `tools[0].function.description` 里**——模型就是靠这段文字决定调不调、怎么填参数 |
| 收到的响应 JSON | 模型的 `tool_calls` 长什么样，以及 token 用量 |

请求头里有 API key，所以只打印 URL 和消息体，不打印请求头。

## 五个练习的顺序

文件里每个练习上方都标了同样的编号，例如 `── 练习 1/5 · Day 1 ·`。

| 练习 | 写哪个函数 | 在哪个文件 | 哪天 | 测试筛选词 |
|---|---|---|---|---|
| 1/5 | `find_matches` | ex1_records.py | Day 1 | `-k find_matches` |
| 2/5 | `make_hits` | ex1_records.py | Day 2 | `-k make_hits` |
| 3/5 | `success_result` | ex2_search_tool.py | Day 3 | `-k success_result` |
| 4/5 | `search_repository` | ex2_search_tool.py | Day 4 | `-k search_repository` |
| 5/5 | 重写 `find_matches`、`make_hits` | **`recall.py`（你创建）** | Day 5 | `./check.sh --week w04` |

**需要你自己创建的文件只有一个：`weeks/w04-python-tools/recall.py`（Day 5）。**它不提供骨架也不提供签名——Day 5 的目的就是关掉范例、凭记忆重写，给了骨架就失去意义了。写法要求见 [D05 任务卡](../../curriculum/tasks/D05.md)。

其余文件仓库里都已存在，你只在标了「练习 N/5」的地方动手。

## 目标

独立把“一批文件记录”变成“可以给 agent 使用的搜索结果”。本周只写四个函数，反复练取值、判断、收集和返回。

你想做 Pi 这类 coding agent，也想用 LangChain / LangGraph 做 DeerFlow 这类应用。本周练两条路线共用的工具逻辑：**模型提出要找什么，你的 Python 负责真正查找，框架把结果交回模型。** 项目参考见 [资源清单](../../RESOURCES.md#w04-方向与接口参考)。

## 自检标准

- [ ] 指着 `records`、循环里的 `record`、`record["path"]` 分别说出类型。
- [ ] 用普通 `for` / `if` 完成筛选，能处理空列表与多个命中。
- [ ] 说清每个函数收到什么、返回什么、返回值由谁接住。
- [ ] 独立写出“输入错误”和“查过但没有命中”两种不同结果。
- [ ] 用自己的函数运行本地工具连接示范，并解释它与模型主动调用工具的区别。
- [ ] 隔天关掉示范，完成下面的重写检查；全绿测试只是其中一个条件。

## Build It — 手写版

### 先认识这一份数据

[sample_repo.py](sample_repo.py) 是**内存里的迷你仓库**。一个字典表示一个文件，一份列表表示整个仓库。路径是教学数据，当前工具不扫描磁盘。

```python
{"path": "src/retry.py", "content": "Retry failed requests."}
```

所有练习只围绕一个问题：**哪些文件的路径或正文提到了某个关键词？** 输入保证每条记录的两个字段都是字符串，数据规模固定且很小。

### 每次 60 分钟怎么用

5 分钟回忆昨天 → 10 分钟读当天热身 → 30 分钟自己写 → 10 分钟测试与解释 → 5 分钟交接。到时间就停在当前函数，下一次接着写；提前做完也把重写留到隔天。

| 次数 | Python 动作 | agent 对应能力 | 当天任务与测试筛选词 |
|---|---|---|---|
| Day 1 | 列表/字典分层、`for`、`if`、`in` | 按需求筛选工具数据 | 热身 1～3；读 `collect_paths`，填 `find_matches`；`-k find_matches` |
| Day 2 | 组装新字典、`append`、循环后 `return` | 只返回任务所需字段 | 先关掉示范口述昨天逻辑，再独立写 `make_hits`；`-k make_hits` |
| Day 3 | 函数返回值、`len`、固定字段 | 成功与错误的工具结果 | 热身 4～6；读 `error_result`，填 `success_result`；`-k success_result` |
| Day 4 | 调用函数、接住结果、分支返回 | 组合成工具并交给框架 | 独立写 `search_repository`；`-k search_repository`；跑框架热身与本地连接 |
| Day 5 | 脱离示范重写、换数据验证 | 工具能力迁移 | 完成重写检查、Use It 对比、测试与本人复盘 |

Day 1 开始先花 5 分钟，在编辑器临时文件里尝试：从两条文件记录中取出所有 `path` 并返回。只记住自己卡在“取哪一层 / 循环 / 收集 / 返回”的哪一步，不追求立即写完，再读示范。不要把这次诊断算成通过。

### 两个练习的坡道

| 文件 | 第 1 段：读示范 | 第 2 段：填关键几行 | 第 3 段：独立写 |
|---|---|---|---|
| [ex1_records.py](ex1_records.py) | `collect_paths` | `find_matches` | `make_hits` |
| [ex2_search_tool.py](ex2_search_tool.py) | `error_result` | `success_result` | `search_repository` |

依赖顺序就是表中的顺序：ex1 全部做完再做 ex2。完成 `make_hits` 后，`success_result` 才能用它；前面的函数未完成会让后续测试一起红，这是依赖关系，并不代表一下子多了很多错误。

每次落笔前只说三句：输入是什么形状？这一步要留下什么？最后返回什么形状？写完检查 `append` 是否保存了一个元素、`return` 是否放在正确的缩进层级。Python 写法查 [热身](00_warmup.py) 或 [速查卡](../../SYNTAX_CARDS.md)；AI 陪练边界见 [AGENTS.md](../../AGENTS.md)。

### 输出约定

成功时返回对象，例如搜索 `retry`：

```python
{
    "ok": True,
    "items": [{"path": "src/retry.py"}, {"path": "README.md"}],
    "count": 2,
    "error": None,
}
```

没有命中：`ok=True`、`items=[]`、`count=0`、`error=None`。纯空白关键词：`ok=False`、`items=[]`、`count=0`、`error="keyword must not be blank"`。这是可预期的输入错误；缺字段这样的编程错误在普通函数测试中会抛出，教师提供的工具连接会把异常类型与原因转成错误结果交给模型。练习未完成的 `NotImplementedError` 保持报错，提醒你先完成练习。

本周只回答“在哪里”，所以结果只保留路径。以后要让 agent 解释代码，再增加读取正文的工具。这里的结构化结果是 **Python 工具返回的字典**；模型最终回答的 `response_format` / Pydantic 校验留到通过本周自检后学习，两个概念见 [术语表](../../GLOSSARY.md)。

## Use It — 框架版

完成 ex2 后，先跑 [warmup_tools.py](warmup_tools.py)，再看 [agent_demo.py](agent_demo.py) 中的 `repository_search`。它只把你的函数接到 LangChain；不需要重写搜索逻辑。

```sh
uv run python weeks/w04-python-tools/warmup_tools.py
uv run python weeks/w04-python-tools/agent_demo.py
```

第一条是完整离线示范，开局就能跑；第二条调用你写好的工具，预计得到上面的两条路径。它是代码指定的工具调用，还没有模型决策。

### 对比表（Day 5 填）

跑完 `--live --debug` 之后填这张表。**重点是最后一列**：框架替你做的每一件事，你都要能说出它解决了什么问题。

| 这件事 | 你的 Python 负责什么 | LangChain 负责什么 |
|---|---|---|
| 把函数变成模型能看懂的工具 | 写函数签名、类型注解和 docstring | `@tool` 把它们翻译成 JSON Schema，塞进请求的 `tools` 字段。请求里 `description` 就是你那段 docstring 原文，`parameters.keyword.type` 来自 `keyword: str` |
| 决定要不要搜、搜什么词 | **完全不参与** | 把工具清单和问题一起发给模型；模型决定后，框架把响应里的 `tool_calls` 解析成 Python 对象 |
| 真正执行搜索、返回结果 | `search_repository` → `find_matches` → `make_hits`，**全是你的代码** | 只负责按 `tool_calls` 里的名字和参数调用你的函数，不碰搜索逻辑 |
| 把工具结果交回模型 | 返回一个普通 dict | 转成 `ToolMessage` 追加进消息列表，带上对应的 `tool_call_id`，再发一次请求。**这一步你在 w02 手写过** |
| 防止模型无限调用 | 不参与 | `ModelCallLimitMiddleware(run_limit=4)`，见 `agent_demo.py` 的 `build_demo_agent` |

一句话总结：**模型决定做什么，你的 Python 决定怎么做，框架负责在两者之间传话。**

三件事框架都没替你做：搜索逻辑本身、返回什么字段、出错时返回什么。这些决定了模型能不能给出对的答案——`--debug` 里模型那句 `reasoning_content` 就是照着你写的 docstring 推理的。

可选体验：已有模型配置且练习完成后运行。它会读取 `.env` 并产生真实模型调用费用；模型须支持工具调用。教师提供了单次模型请求 20 秒、整轮 60 秒、最多 4 次模型调用和图步数上限。连接代码由教师维护，这周只需能解释三步：注册工具 → 模型要求调用 → 结果返回模型。

```sh
uv run python weeks/w04-python-tools/agent_demo.py --live
```

检查打印的消息中是否真的有 `repository_search` 调用、相应工具结果和最终回答。仅看到模型给出文件名不算调用工具的证据。真实模型体验不作为本周 Python 达标的前提。

| 手写部分 | LangChain 接口 | 你来填：它接手了什么，什么仍由你的函数负责？ |
|---|---|---|
| `search_repository(records, keyword)` | `@tool` | |
| 直接传参数并接住返回值 | `repository_search.ainvoke(...)` | |
| w02 中的模型 → 工具 → 模型循环 | `create_agent(...).ainvoke(...)` | |

## Ship It — 带走的工件

一个可以独立验证、能被 LangChain 调用的搜索工具。代码留在本周；后续是否提升到 `src/` 按仓库规则决定。本周不要求做编辑文件、运行 shell、网页界面或多 agent。

### Day 5 重写检查

关掉 ex1/ex2 和热身，新建你自己的 `recall.py`，从空白写 `find_matches` 与 `search_repository`。辅助函数可以从已完成的 ex1/ex2 导入，但不能打开它们查看答案。可以查标准库语法，不看旧实现；如果查过 `for` / `return` 的基本写法，在本人复盘记下，再隔天做一次无资料重写。

用下面的新数据检查，没有改搜索规则，只换了场景：

```python
records = [
    {"path": "notes/loop.md", "content": "How tools return data"},
    {"path": "src/main.py", "content": "Read config"},
]
```

预期：搜 `"  TOOLS "` 只命中 `notes/loop.md`；搜 `"main"` 只命中 `src/main.py`；搜 `"absent"` 是成功的空结果；搜 `" "` 是输入错误；空仓库配有效关键词是成功的空结果。给自己的文件加调用并打印，与这些预期逐项对照。

最后说清：`find_matches` 返回列表，`search_repository` 返回字典，为什么调用后不能把这两种返回值当成同一种东西取值？本人把结果填进 [w04 复盘](../../notes/weekly/w04.md)。如果重写仍卡住，就在同一主题补一天；先不要增加框架难度。

## 文件

| 文件 | 什么时候看 |
|---|---|
| [00_warmup.py](00_warmup.py) | Day 1 / Day 3，分段跑与读 |
| [sample_repo.py](sample_repo.py) | 看清一批文件的数据形状 |
| [ex1_records.py](ex1_records.py) / [ex2_search_tool.py](ex2_search_tool.py) | 本周仅有的两个主练习 |
| [warmup_tools.py](warmup_tools.py) / [agent_demo.py](agent_demo.py) | Day 4，看函数怎么接入 agent |
| [test_w04.py](test_w04.py) | 练习的行为规格，不需要学习 pytest 写法 |
| [test_w04_bridge.py](test_w04_bridge.py) | 教师的连接测试，不需要学习假模型实现 |

## 运行

从仓库根目录执行。已安装依赖可直接开始；新环境先 `uv sync`，离线练习无需 key。

```sh
uv run python weeks/w04-python-tools/00_warmup.py
uv run python weeks/w04-python-tools/ex1_records.py
uv run pytest weeks/w04-python-tools/test_w04.py -k demo -q
uv run pytest weeks/w04-python-tools/test_w04.py -k find_matches -xq
uv run pytest weeks/w04-python-tools -q
./check.sh --wip
```

教材交付时的验证：两份热身、两段示范可运行；8 条示范/连接测试通过，13 条练习规格因 TODO 未完成而失败；`./check.sh --wip` 通过。真实模型尚未运行。

开局的 `NotImplementedError` 是留给你写的部分；不把未完成测试跳过或标成通过。教师连接测试使用固定替身结果验证 LangChain 消息连接、错误反馈和模型调用上限，不代表你的搜索函数已完成，也不代表真实模型已验证。周末完成练习后运行 `./check.sh --week w04`，再结合重写检查判断是否达标。

## 卡住的地方

（由你填：在哪个函数、哪一步，以及最后怎么找到问题。）
