# 开馆验收桌 · 交出整座馆 · 教学与开发规则

先读根AGENTS.md与world/STORY.md对应章节。

## 2026-10完整课程的补充协议

本模块为M10，实际学习只从README当前委托进入。新增内容、图解和接待台不预设课程外知识。

**本章接待台：**明确登记本人reception/research/maintenance异步组件。route_library选择并实际调用；write先核对controls.approved，研究要经过本人context、source merge和grader。独立扩展与验收来自本人的M10作品；release只报告当前版本匹配的真实检查。

| Task | 核心机制 | 本人交付与检查 |
|---|---|---|
| M10-T01 | 确定性workflow、agent循环、研究规划与受限维修的可替换组件编排。 | 核对本页断言、真实输入和来源；选择题与代码迁移分开记录。 |
| M10-T02 | 端到端、变形测试、回归、留出、失败分布与可解释证据。 | 核对本页断言、真实输入和来源；选择题与代码迁移分开记录。 |
| M10-T03 | 从需求到契约、最小扩展、组合优于重写、故障定位与回归。 | 核对本页断言、真实输入和来源；选择题与代码迁移分开记录。 |
| M10-T04 | 版本绑定、最小发布、可复现环境、来源证据与操作交接。 | 核对本页断言、真实输入和来源；选择题与代码迁移分开记录。 |

**逐关授课顺序：**先看剧情中的具体障碍，沿SVG图核对数据，原位解释Python/框架/行为三层，再运行完整示范。帮助从单一步骤逐渐撤去，核心函数由本人写；原理复盘用选择卡。

**实际prompt：**world/prompts中的本关岗位、目标和完成条件必须被展示并加载；runtime另交当前输入。外部正文、Skill、MCP模板不授予权限。阿灯自然接待，不念课程或公文免责声明。

**模型与权限：**沿用.env，异步、单次/整轮超时、总调用边界；不换机芯、不输出密钥/隐藏推理。只有M08受限Docker执行模型生成代码。任何写动作由程序与人的实际许可决定。

**教师与本人：**setup/demo可真实验证；exercise/exercise-test跳过并列ID，不以教师结果登记通关。实际运行、判断卡、陌生输入三种证据分开，已保存本人实现与输出保留。

**连续性与交接：**新机制进入下一项本人作品，执行授权、来源身份、记忆作用域、预算和当前版本回归。缺本人导出就定位原格，不注入solution。读state/catalog/当前Notebook后继续，逐字问答入当日日志。

**维护：**AGENT.md与CLAUDE.md链接本文件；目录与图解用render_curriculum同步。运行instructor.check、pytest、ruff、mypy及对应真实示范。未获用户请求不提交/推送，不自动打学习完成标签。

## 本模块生产实训协议

业务项目见instructor/blueprints/M10.md与module_blueprints.json，完整原理在首关Notebook，真实实训在M10-T04。本章有三层路线，不预设企业后端经验；新对象/API原位解释。

**授课阶段1：**从业务需求选择一条够用路线，调用当前本人组件；注册缺口或未批准维修必须在动作前暴露。

**授课阶段2：**固定候选再跑回归与留出，目标不进入runtime；收集代码/prompt/Schema/材料/依赖和实际结果版本，关键失败单列。

**授课阶段3：**故意让批准后内容漂移，观察发布阻止。用新进程按运行手册启动、失败诊断、停止与恢复；数据迁移/外部副作用的回滚不能等同git切回。

production-cases.json记录本章目标案例，enterprise-owned-checks调用本人module_agent并提供独立CaseEnvironment。教师准备与本人事件分开，目标不传runtime；审批token不进消息或公开包。窄检查、语义核对与陌生迁移分别记录，manual_review_required不自动通关。

不让本人的组件回退到enterprise教师进程；缺本人实现定位原格。当前身份、来源版本、许可与累计预算跨本章完整作品保留。章节事件以course_enrichment/world/STORY为共同说明，故障由实际环境触发，故事不决定通过。维护须运行enterprise_course（结构改变时）、render_curriculum、check与对应真实验证；不提交、推送或修改完成状态。

## 审查改进后的独立项目与岗位交付

M10-T03除基础包装练习，还让本人选择新的馆务需求，build_feature_plan保留边界与验收，feature_handler显式接components/plan，不依赖教师备用函数。方案与运行分开，至少真实输入、故障与旧回归。

M10-T04的build_portfolio_packet与inspect_portfolio核对本人origin、当前文件、检查与交接依据；ready_for_review不是录用、发布或掌握。RUNBOOK/演示/失败案例是实际软件交付物，不是强制文字复盘。现场新条件与帮助程度单独记录，不背框架名替代能力。
