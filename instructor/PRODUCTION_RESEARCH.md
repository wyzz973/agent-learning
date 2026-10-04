# 模块调研与工程设计依据

核查日期：2026-10-03。课程使用锁定依赖；文档会更新，官方文档的推荐不自动证明本项目已经实现。每章把业务架构、原理、故障矩阵和出处嵌入当前Notebook，本文是导师的设计记录，不是新的学习前置。

贯穿产品是**机构数字知识服务**：门厅与分馆咨询、政策资料检索、建设研究、批准后发布、可恢复办理和隔离维修。分馆模拟tenant，匿名访客模拟用户作用域，林禾承担实际人的批准。SQLite、HTTP、MCP、embedding和Docker是真实本地设施；馆务语料与受控故障属于教学环境，不能把它们当真实提供方事故或生产部署。

## M01：模型网关、提示配置与结构契约

[LangChain模型接口](https://docs.langchain.com/oss/python/langchain/models)区分消息、模型能力和公开响应；[结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output)区分ProviderStrategy、ToolStrategy与错误处理。由此采用“消息序列化→远程调用→解析→Schema→业务支持”的教学链，避免把一次ainvoke等同完整应用。错误修复需要限定类别与次数，认证失败不能当格式错误无限重试。

本章把旧公告快照与新消息并排观察，用真实HTTP成功但坏JSON的反例隔开网络与解析，用Pydantic拒绝非法字段。本人项目处理新版本和未知日期。接口策略按当前提供方实测，不宣称所有模型都支持同样的严格格式。

## M02：模型申请与工具事务

[LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)描述参数Schema与执行能力；[Middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview)提供拦截位置。课程把工具说明、tool_calls、授权、执行、ToolMessage和下一轮模型输入逐一分开。每次观察保留调用ID、来源ID与状态，作用不同，不得交换。

生产动作采用真实SQLite事务、输入绑定的幂等键和单次审批。实验重放同请求、改变输入复用旧键、伪造approved参数。幂等记录是业务设施，本人仍要设计授权与循环；工具挂上名字并不意味着已经执行。真实企业身份、跨服务事务和业务幂等保留期需要按部署环境继续设计。

## M03：图、并行与重放

[Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)规定节点更新、super-step和reducer；[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)、[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)说明线程状态与恢复路径。教学重点是可观察状态转换，随后进入分支、汇合和外部副作用。

课程真实运行两次独立进程：首个进程提交发布后，在节点交回更新前抛错；新进程恢复同图与SQLite检查点，用同幂等身份重放，业务库仍只一条发布。该实验验证选定崩溃位置，不能推成所有外部动作exactly-once。本人项目必须继续保留安全回执、身份、预算和终态，图END不等于任务成功。

## M04：记忆、上下文与撤回

[短期记忆](https://docs.langchain.com/oss/python/langchain/short-term-memory)与[长期记忆](https://docs.langchain.com/oss/python/langchain/long-term-memory)服务不同作用域；[上下文工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)强调选择进入有限输入的信息。课程进一步区分checkpoint、跨会话Store、当前context、缓存与归档原文。

实训采用当前版本判断、CAS并发写入、同意/TTL与撤回标记；先取一份旧缓存，再实际更正与撤回，检查旧值没有复活。CAS、撤回传播与缓存失效是本课程的工程设计，不是框架默认替应用完成的功能。历史产物删除、备份保留和真实个人资料政策需独立处理，不能从本轮不引用推断所有副本已消失。

## M05：RAG与研究系统的数据生命周期

[LlamaIndex入库流程](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/)展示基于doc_id/哈希的管理；[后处理](https://developers.llamaindex.ai/python/framework/module_guides/querying/node_postprocessors/)解释召回后筛选；[Open Deep Research](https://github.com/langchain-ai/open_deep_research)提供可研究的完整管线。课程将入库与查询分开，原文身份贯穿chunk、vector、融合、证据包与引用。

真实embedding用于可见英文资料集合，更新和撤回资料后对照旧索引，明确“业务库更新”与“索引已更新”不同。本人实现BM25/向量排名衔接、RRF、上下文打包与缺口循环；查询侧应用tenant、版本和证据约束。向量相似度不能证明可信度，混合排名不能代替引用支持检查。中文跨语言召回、长表格及大规模索引是明确扩展实验，不能冒充当前基线已经覆盖。

## M06：协作、质量评估与诊断

[多Agent研究系统](https://www.anthropic.com/engineering/multi-agent-research-system)强调任务边界、输出、工具与预算；[Agent评估](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)区分任务、轨迹、评分与环境；[OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/)提供跨组件关联模型。课程采用先统一Brief/提纲、再独立取证、最后合并编辑的流程。

原项目的[问题报告283](https://github.com/langchain-ai/open_deep_research/issues/283)描述子任务异常被成功分支遮住的情形；作为已报告案例研究，不声明当前代码仍有该缺陷。本课用受控部分失败、关键越权、高平均分反例和首个偏差轨迹，教学生检查被遮住的失败。裁判需要原句审计、顺序对照与人工校准；20项受控记录的95%不是本课程真实模型成绩。

## M07：MCP互操作与Skills治理

[MCP规范](https://modelcontextprotocol.io/specification/2025-11-25)、[授权](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)、[安全实践](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices)明确协商、能力与受众/透传风险；[Agent Skills规范](https://agentskills.io/specification)和[Deep Agents Skills](https://docs.langchain.com/oss/python/deepagents/skills)区分元数据、方法正文和后端执行。

本章真实initialize/list/call/read/get/close，并观察当前SDK的isError与关闭会话后的失败。客户端重新连接需重新确认Schema；Skill与远端prompt只提供方法或数据，不增加本地权限。课程绑定明确规范版本与当前SDK；本地课堂Bearer门禁仅演练身份隔离，不能称为完整OAuth。SSRF、Origin、token受众和秘密传递在设计矩阵明确，真实远端部署另作环境验收。

## M08：Coding Agent与维修Harness

[Mini-SWE-Agent源码](https://github.com/SWE-agent/mini-swe-agent)可观察最小运行循环；[长期Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)提供可接续任务方法；[Docker安全](https://docs.docker.com/engine/security/)说明容器边界。课程区分模型提出动作、运行时执行、固定验收与本人接纳源码，不以模型的“修好了”收工。

真实隔离实验先跑通过的候选，再改坏源码，检查旧测试SHA立即失效，再跑出失败并恢复；许可、允许路径、资源限制和固定测试保持。容器不是绝对安全边界，课程候选使用已有受限环境；真实组织要按威胁模型选择更强隔离与凭据策略。最后必须实际迁入当前组件并通过研究回归，只有patch文件不足以证明被采用。

## M09：服务运行、流、预算与身份

[LangChain streaming](https://docs.langchain.com/oss/python/langchain/streaming)区分事件与不同投影；[asyncio](https://docs.python.org/3/library/asyncio-task.html)说明Task取消与timeout。课程分别观察客户端等待、本地Task、网络请求和服务端执行；并将总deadline、尝试、并发、缓存键与身份贯穿一轮任务。

真实HTTP实验客户端0.03秒超时，服务端0.18秒后仍实际执行；另做503/成功的两次请求。实际流式示范和取消保留片段、清理与最终状态。提供方限流、客户端断线与格式故障不得用同一种重试；课堂的Retry-After=0是受控值，真实部署要尊重提供方响应并加入抖动与整段预算。健康检查只证明被检查的依赖，不能当质量分。

## M10：交付、版本与运行手册

[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)建议从足够的简单架构开始；[LangSmith evaluation](https://docs.langchain.com/langsmith/evaluation)支持数据集与回归；[uv锁定同步](https://docs.astral.sh/uv/concepts/projects/sync/)支持环境复现。毕业项目围绕真实需求选择咨询、研究、工具或维修路线。

发布清单绑定代码、prompt、材料、工具Schema、依赖和实际验收版本。关键失败阻止放行；审批后修改资料，旧批准不得沿用。停止/回滚需要考虑已提交事务与数据Schema，不能等同git切回。新进程启动、取消、恢复与失败诊断保留真实凭据；本地课程验收不宣称完成所有部署、IAM与组织合规要求。

## 原项目与教学项目怎样结合

[Hello-Agents](https://github.com/datawhalechina/hello-agents)提供中文原理与案例组织参考；[LangChain Academy](https://github.com/langchain-ai/langchain-academy)提供Notebook学习路线；[Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)提供从流程组件逐渐构建研究的方式。本课继承“原理→可运行小例子→项目进阶”，增加一个连续业务、渐隐帮助、本人生产验收和跨Harness证据，讲解与必要写法全部留在当前页。

课程编排属于导师对公开原理的应用设计。结构检查、教师真实运行、本人实现、选择题、陌生输入分别验收；没有哪一项替其他项证明课程学习效果或市场排名。
