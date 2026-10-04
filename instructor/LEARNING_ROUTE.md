# 从第一行Python到完整数字馆

这份路线供选读；学习入口始终是README当前Notebook。单位是module/task，每次约一小时，按休息点多次完成。时间是可调整的教学估计，不是保证多久掌握。

主线：消息与结构 → 工具反馈循环 → 状态图 → 持久化与记忆 → RAG/自适应研究 → 协作与评估 → MCP/Skills → 隔离维修 → 日常运行 → 完整交付。

## 学习节奏

工作日一次约一小时，完成一个可观察小步便保存。起步月优先门厅、问询台和委托台的基础任务；完整课程跨多个学习阶段，复杂研究与独立交付允许多次完成，不把一个月当强制终点。

每章有**入门、组件开发、生产实训**三层。下表是核心任务的可调整估计；生产深入另预留每章约3—6次学习，不把环境排障或独立编码强塞进一小时。每次只接通一条数据边、一个正常行为或一个故障处理，保存真实结果后休息。已会Python可以略读语法例子，核心实现、生产边界与迁移仍需完成。

首关Notebook里的展开手册提供本章完整原理与业务架构；章末提供生产实验、三段实践、本人module_agent接线、独立环境验收与设计选择题。所有层次都在本章当前页说明，导师调研不增加前置阅读。

| Module | 具体成长 | 任务数 | 约一小时次数 | 章末作品 |
|---|---|---:|---:|---|
| [M01 · LangChain 基础](../modules/01-langchain-foundations/README.md) | 帮门口读者读懂开馆公告，让公告台显示答复。 | 3 | 9 | 本人组件、实际回执与统一接待台 |
| [M02 · 工具与 Agent](../modules/02-tools-and-agents/README.md) | 让阿灯自己申请公告和手册，处理取件失败。 | 4 | 12 | 本人组件、实际回执与统一接待台 |
| [M03 · LangGraph 控制](../modules/03-langgraph-control/README.md) | 连续查资料、分流问题，让读者看到进度并能取消。 | 4 | 12 | 本人组件、实际回执与统一接待台 |
| [M04 · 记忆与人工审核](../modules/04-memory-and-human-review/README.md) | 断电后接续委托，记住确认信息，保留可核对的经验。 | 6 | 18 | 本人组件、实际回执与统一接待台 |
| [M05 · Deep Research 核心](../modules/05-deep-research/README.md) | 为阿灯的建设方案寻找真实技术依据，补足研究缺口。 | 5 | 21 | 本人组件、实际回执与统一接待台 |
| [M06 · 研究系统与评估](../modules/06-research-system/README.md) | 研究者分工，定位失败，让另一台设备使用阿灯。 | 5 | 21 | 本人组件、实际回执与统一接待台 |
| [M07 · 协议与可复用能力](../modules/07-protocols-and-skills/README.md) | 把资料工具与核查方法交给分馆，比较成熟装配方式。 | 5 | 15 | 本人组件、实际回执与统一接待台 |
| [M08 · Coding Agent 拓展](../modules/08-coding-agent/README.md) | 修复数字馆的真实组件，中断后还能继续维修。 | 4 | 15 | 本人组件、实际回执与统一接待台 |
| [M09 · 运行与应用边界](../modules/09-runtime-and-service/README.md) | 让阿灯的流式、预算、接口与服务身份有真实边界。 | 4 | 15 | 本人组件、实际回执与统一接待台 |
| [M10 · 完整数字馆交付](../modules/10-opening-capstone/README.md) | 把本人全部能力接成可复现、可回归、有实际凭据的数字馆。 | 4 | 21 | 本人组件、实际回执与统一接待台 |

## M01 · 门厅 · 第一盏接待灯

帮门口读者读懂开馆公告，让公告台显示答复。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M01-T01](../modules/01-langchain-foundations/01-first-reader.ipynb) | 显式上下文：本地资料必须进入本轮消息，回复必须回到原文核对。 | answer_reader | 3 |
| [M01-T02](../modules/01-langchain-foundations/02-notice-board.ipynb) | 结构化输出规定字段，语义核对判断字段内容是否有依据。 | NoticeAnswer, answer_for_board | 3 |
| [M01-T03](../modules/01-langchain-foundations/03-message-workbench.ipynb) | 显式消息边界、提示版本、资料与指令分离；对同题只改一个因素。 | build_current_messages, module_agent | 3 |

**交互交付：**先读取所选公告，使用本人build_current_messages组织输入，保留本人NoticeAnswer的字段与来源核对。真正调用当前模型后返回答复与当前公告；未知事项显示待确认。schema来自M01-T02的本人导出，不复制教师schema。

## M02 · 问询台 · 打开资料柜

让阿灯自己申请公告和手册，处理取件失败。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M02-T01](../modules/02-tools-and-agents/01-cabinet-tools.ipynb) | Tool 是可执行能力；模型提交参数，程序执行并返回观察。 | read_document, build_cabinet_agent | 3 |
| [M02-T02](../modules/02-tools-and-agents/02-tool-dispatch.ipynb) | 工具调用消息和工具执行是两步；ToolMessage用调用ID关联观察。 | execute_calls | 3 |
| [M02-T03](../modules/02-tools-and-agents/03-tool-recovery.ipynb) | 工具契约、错误观察与中间件分工；重试与纠正有上限。 | execute_calls_safely, run_with_recovery | 3 |
| [M02-T04](../modules/02-tools-and-agents/04-tool-permissions.ipynb) | 工具能力、模型请求、程序授权和真实执行四层分离；默认拒绝。 | authorize_tool, module_agent | 3 |

**交互交付：**调用本人run_with_recovery；允许工具通过本人authorize_tool检查，实际执行仍由execute_calls_safely完成。把完整请求ID与回执转换为公开trace，只有实际成功工具正文进入evidence。拒绝回执不算来源。

## M03 · 委托台 · 把事情办完

连续查资料、分流问题，让读者看到进度并能取消。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M03-T01](../modules/03-langgraph-control/01-reception-routes.ipynb) | State保存工作数据，Node返回更新，Edge决定执行路线；区分workflow与agent。 | ReceptionState, read_evidence, answer_reader, choose_route, build_reception_graph | 3 |
| [M03-T02](../modules/03-langgraph-control/02-observation-loop.ipynb) | 模型提出动作、程序执行、观察进入状态、再次决定；停止是显式路径。 | LoopState, model_step, tools_step, route_step, build_consultation_graph | 3 |
| [M03-T03](../modules/03-langgraph-control/03-progress-and-cancel.ipynb) | 公开运行事件和预算是控制系统的一部分；停止原因也属于结果。 | observe_run | 3 |
| [M03-T04](../modules/03-langgraph-control/04-parallel-state.ipynb) | 并行分支、reducer、fan-in与确定性；子图是边界而非新权限。 | merge_receipts, module_agent | 3 |

**交互交付：**使用本人build_consultation_graph编译真实图，再由observe_run消费公开事件；独立取件时使用本人的merge_receipts检查去重和冲突。保留calls、stop_reason与真实路径。graph结束与委托办妥分开。

## M04 · 值班室 · 交班不失忆

断电后接续委托，记住确认信息，保留可核对的经验。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M04-T01](../modules/04-memory-and-human-review/01-durable-shift-log.ipynb) | Checkpointer保存thread状态；持久存储和同一thread标识共同支持恢复。 | run_persistent_consultation | 3 |
| [M04-T02](../modules/04-memory-and-human-review/02-review-and-publish.ipynb) | interrupt把审批作为状态；Command恢复，幂等边界防止重放重复写入。 | review_notice, publish_once | 3 |
| [M04-T03](../modules/04-memory-and-human-review/03-reader-memory.ipynb) | Store与checkpointer职责不同；记忆要写入、按命名空间读取、更新和删除。 | save_preference, load_preferences, withdraw_preference | 3 |
| [M04-T04](../modules/04-memory-and-human-review/04-context-folder.ipynb) | 完整持久状态与本轮模型输入分开；裁剪、摘要、外置原文各有损失边界。 | pack_context, fetch_archived | 3 |
| [M04-T05](../modules/04-memory-and-human-review/05-experience-notes.ipynb) | 把外部任务反馈形成有适用条件的经验，在后续尝试检索使用；不更新模型权重。 | make_experience, choose_experiences, withdraw_experience | 3 |
| [M04-T06](../modules/04-memory-and-human-review/06-memory-lifecycle.ipynb) | 记忆是有来源、有作用域、有生命周期的应用数据。 | select_memory, module_agent | 3 |

**交互交付：**按controls的匿名user_id读取本人记忆；select_memory核对当前有效条目，未声明同意/到期的旧记录留待确认。恢复操作使用原thread_id与本人run_persistent_consultation。撤回需controls.approved，由本人withdraw_preference执行，再重新读取确认；旧报告不被假称已删除。

## M05 · 研究阅览室 · 为数字馆查证

为阿灯的建设方案寻找真实技术依据，补足研究缺口。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M05-T01](../modules/05-deep-research/01-scope-and-evidence.ipynb) | 研究简报表达目标、边界、子问题、证据要求和停止条件。 | scope_request | 4 |
| [M05-T02](../modules/05-deep-research/02-search-and-sources.ipynb) | 搜索负责发现候选，fetch取得原文；Evidence保存URL、时间、片段和定位。 | collect_sources | 4 |
| [M05-T03](../modules/05-deep-research/03-retrieval-and-evidence.ipynb) | RAG把检索结果作为生成依据；切分、索引、召回和引用定位分别可检查。 | chunk_sources, rank_chunks | 4 |
| [M05-T04](../modules/05-deep-research/04-gap-driven-research.ipynb) | 研究循环根据证据覆盖与冲突决定继续搜索、澄清或结束；批评需指向原文。 | next_research_step, build_gap_graph | 4 |
| [M05-T05](../modules/05-deep-research/05-hybrid-retrieval.ipynb) | 关键词/语义候选、RRF、MMR与引用身份；检索质量先于生成。 | combine_rankings, module_agent | 3 |

**交互交付：**用本人研究简报、collect_sources、chunk_sources/rank_chunks和combine_rankings选择真实证据；pack_context与fetch_archived保留来源身份。本人build_gap_graph驱动缺口与预算，真实报告返回URL、时间与窗口。不用snapshot_input替代本人上下文。

## M06 · 服务台 · 接受开馆验收

研究者分工，定位失败，让另一台设备使用阿灯。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M06-T01](../modules/06-research-system/01-plan-research-write.ipynb) | 先比较固定并行流程与模型委派；子agent上下文隔离，返回有证据的结果。 | run_workers, merge_worker_sources | 4 |
| [M06-T02](../modules/06-research-system/02-evaluation-and-ablation.ipynb) | 固定任务集、独立评判、轨迹与产物双检查；消融实验识别机制贡献。 | grade_run | 4 |
| [M06-T03](../modules/06-research-system/03-trace-and-diagnosis.ipynb) | 可观测性连接输入、决策、工具、状态与产物；公开事件支持归因和预算分析。 | diagnose_trace | 4 |
| [M06-T04](../modules/06-research-system/04-local-research-service.ipynb) | 应用入口、持久任务、事件流、产物位置与运行配置组成交付闭环。 | handle_research | 4 |
| [M06-T05](../modules/06-research-system/05-semantic-evaluation.ipynb) | 代码grader、语义judge、人工校准、盲评与不确定性。 | audit_verdict, module_agent | 3 |

**交互交付：**本人handle_research调用run_workers、merge_worker_sources、研究与grade_run，audit_verdict核对模型裁判可靠性；使用本地服务时返回job与实际状态。全管线calls累计包括摘要，失败和待复核保留。

## M07 · 交换站 · 分享工具和方法

把资料工具与核查方法交给分馆，比较成熟装配方式。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M07-T01](../modules/07-protocols-and-skills/01-mcp-tools.ipynb) | MCP定义能力发现、工具调用与上下文连接；协议不是agent的决策循环。 | branch_read, ask_branch | 3 |
| [M07-T02](../modules/07-protocols-and-skills/02-skills-and-context.ipynb) | Skill保存任务知识、步骤与参考；先展示元数据，再按相关性加载正文/资源。 | answer_using_method | 3 |
| [M07-T03](../modules/07-protocols-and-skills/03-tool-discovery.ipynb) | 能力目录与执行工具分开；按需发现/加载工具，选择过程同样需要评估。 | select_tool_names, run_with_discovery | 3 |
| [M07-T04](../modules/07-protocols-and-skills/04-deep-agents-comparison.ipynb) | Deep Agents组合模型循环、文件上下文、记忆、技能与委派；用同题实验理解抽象。 | compare_my_harnesses | 3 |
| [M07-T05](../modules/07-protocols-and-skills/05-mcp-resources-and-prompts.ipynb) | MCP工具、资源、提示模板的控制主体与信任边界。 | compose_mcp_context, module_agent | 3 |

**交互交付：**调用本人ask_branch或answer_using_method取得实际工具观察；Resources/Prompts由compose_mcp_context选择为本轮数据，远端模板不提升权限。实际加载的Skill与真实协议/工具轨迹放进trace，方法名存在不算执行过。

## M08 · 维修间 · 阿灯维护自己

修复数字馆的真实组件，中断后还能继续维修。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M08-T01](../modules/08-coding-agent/01-read-edit-test.ipynb) | 读代码→修改→运行不可篡改的测试→反馈续改，代码执行必须在隔离环境。 | run_guarded_repair | 4 |
| [M08-T02](../modules/08-coding-agent/02-maintenance-resume.ipynb) | Harness是模型周围的执行环境：权限、文件、任务状态、工具、技能与验证共同协作。 | create_maintenance_record, resume_maintenance | 4 |
| [M08-T03](../modules/08-coding-agent/03-opening-handover.ipynb) | 把产品拆回已学契约：模型输入、动作执行、控制、记忆、技能、恢复与评估。 | answer_with_budget | 4 |
| [M08-T04](../modules/08-coding-agent/04-patch-transactions.ipynb) | 补丁事务、允许路径、测试不可篡改、内容版本与回归证据。 | verify_patch_proposal, module_agent | 3 |

**交互交付：**先检查controls.approved和允许工作区；未获准仅返回提议。本人run_guarded_repair/resume_maintenance在既有CodingWorkspace隔离环境中工作；verify_patch_proposal核对固定测试与当前SHA。界面不执行候选源码，也不提供任意shell。

## M09 · 运行室 · 接稳日常使用

让阿灯的流式、预算、接口与服务身份有真实边界。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M09-T01](../modules/09-runtime-and-service/01-streaming-service.ipynb) | 真实astream、部分结果与完整结果、接口能力声明和事件背压。 | run_stream | 3 |
| [M09-T02](../modules/09-runtime-and-service/02-runtime-policy.ipynb) | 瞬态重试、总调用预算、缓存身份、并发上限与可观察成本。 | invoke_with_policy | 3 |
| [M09-T03](../modules/09-runtime-and-service/03-interface-contracts.ipynb) | 提供方能力、适配器、消息ABI、结构与行为测试、受控降级。 | check_interface_request | 3 |
| [M09-T04](../modules/09-runtime-and-service/04-service-boundaries.ipynb) | 认证与授权、租户作用域、健康检查、版本一致性与部署演练。 | authorize_request, module_agent | 3 |

**交互交付：**authorize_request先核对controls提供的匿名身份与办理方式；check_interface_request检查本轮接口，再使用本人invoke_with_policy或run_stream。普通片段通过明确回调送给workspace.desk.emit_progress；实际events与最终answer核对，取消后不再显示晚到片段。

## M10 · 开馆验收桌 · 交出整座馆

把本人全部能力接成可复现、可回归、有实际凭据的数字馆。

| Task | 实现什么与为什么 | 本人函数 | 约一小时次数 |
|---|---|---|---:|
| [M10-T01](../modules/10-opening-capstone/01-library-orchestrator.ipynb) | 确定性workflow、agent循环、研究规划与受限维修的可替换组件编排。 | route_library | 4 |
| [M10-T02](../modules/10-opening-capstone/02-opening-acceptance.ipynb) | 端到端、变形测试、回归、留出、失败分布与可解释证据。 | run_acceptance_suite | 4 |
| [M10-T03](../modules/10-opening-capstone/03-independent-feature.ipynb) | 从需求到契约、最小扩展、组合优于重写、故障定位与回归。 | extend_library | 5 |
| [M10-T04](../modules/10-opening-capstone/04-release-and-handover.ipynb) | 版本绑定、最小发布、可复现环境、来源证据与操作交接。 | build_release_manifest, module_agent | 4 |

**交互交付：**明确登记本人reception/research/maintenance异步组件。route_library选择并实际调用；write先核对controls.approved，研究要经过本人context、source merge和grader。独立扩展与验收来自本人的M10作品；release只报告当前版本匹配的真实检查。

## 核心能力覆盖

| 能力 | 本人机制与真实验收位置 |
|---|---|
| 消息/结构化/提示边界 | M01-T01, M01-T02, M01-T03 |
| 工具循环/失败/权限 | M02-T01, M02-T02, M02-T03, M02-T04, M03-T02 |
| LangGraph/并发/子图/取消 | M03-T01, M03-T02, M03-T03, M03-T04 |
| 持久化/审核/长期记忆/上下文 | M04-T01, M04-T02, M04-T03, M04-T04, M04-T05, M04-T06 |
| RAG/切块/embedding/混合检索 | M05-T02, M05-T03, M05-T05 |
| 研究/规划/补证/协作 | M05-T01, M05-T04, M06-T01 |
| 评估/消融/trace/裁判 | M06-T02, M06-T03, M06-T05, M10-T02 |
| MCP/Resources/Prompts/Skills | M07-T01, M07-T02, M07-T03, M07-T04, M07-T05 |
| 代码维修/隔离/恢复/补丁 | M08-T01, M08-T02, M08-T03, M08-T04 |
| 流式/预算/缓存/服务边界 | M06-T04, M09-T01, M09-T02, M09-T03, M09-T04 |
| 完整应用/独立设计/回归/交付 | M10-T01, M10-T02, M10-T03, M10-T04 |

多模态暂不进入主线。协议升级、模型后训练/RL与开放互联网生产部署作为以后独立扩展，当前不标成已实训能力。
