# 导师工作台

学习者从根README的当前委托进入Notebook。本目录只维护故事、教材与证据，不能变成另一个必读入口。

- catalog.json：雾岛10章44项委托、三级阶段、学习目标、材料状态和情景prompt。课程外前置为空。
- course_enrichment.json：十章剧情与原理、44份审核后的源码观察、108道逐项解析选择题；原位写入Notebook。
- state.json：当前任务/cell和玩家证据。机器可运行、本人解释、陌生输入迁移分别记录。
- render_curriculum.py：从目录生成区域地图、world/prompts及受管理的原理/选择卡格；已有本人格不改，`--check`检查一致性。
- check.py：检查情景、任务字段、Notebook格式、代码标签与当前入口。
- validate_notebooks.py：只执行教师setup/demo；本人练习保持本人完成。
- launch.py：打开当前可学习Notebook。
- learner_exports.py：从保存后的本人练习格提取指定定义与来源记录，不执行答案、不自动覆盖project已有修改；同时提供受限世界资料加载。
- PEDAGOGY.md：示范、练习、反馈与迁移的教学依据。
- RESEARCH.md：技术机制、官方来源与版本核查。
- COURSE_IMPROVEMENTS.md：Hello-Agents对照后修复的衔接与验收边界。
- LEARNING_ROUTE.md / coverage.json：10章44关的完整路线、学习次数估计与核心覆盖；选读，不替代当前Notebook。
- course_atlas.py：逐关流程、即时术语与完整剧情，渲染成SVG和Notebook讲授。
- QUALITY_STANDARD.md：原理/图解/编码/对照/迁移/验收的课程质量要求。
- course_workspace.py / retrieval_bridge.py：统一模块界面及本人RAG实际输入衔接，不含学生算法兜底。
- INTERACTION_DESIGN.md / interaction.py：统一接待台与选择题；各章提供设施，本人完成module_agent后接线，缺实现不回退。
- module_blueprints.json / blueprints/：逐模块业务项目、完整原理、架构、故障矩阵与来源，嵌入首关与模块首页。
- PRODUCTION_RESEARCH.md：十章分别调研的文档事实、工程选择、实际验证与部署边界。
- enterprise_course.py / enterprise_narrative.py：同步三级项目、章末实训与独立案例，再同步章节事件、分步实践和模块规则。
- institution.py / institution_http.py：可读业务环境，真实SQLite/HTTP、身份、版本、审批和事务；不包含本人Agent算法。
- enterprise_acceptance.py：只调用明确传入的本人入口，独立准备环境并记录实际输入/事务；原生回调保留模型类型，grader目标不交runtime。
- check_enterprise_fixtures.py：实际准备20案例，明确未执行本人入口；record_validation.py从当前执行副本和真实检查整理证据。
- publish_walkthroughs.py：审校后的讲解进入共同教案；模型草稿不直接发布，引用是原格中的语句片段。
- qa/：本机逐字问答记录，不发布到公开仓库。

准备一关时，先编写情景、实际prompt、必要Python、完整示范、本人核心实现、真实验收、作品展示与休息点。Notebook完整且验证后才从draft改为ready；planned只代表委托设计。生成地图或prompt不代表完成教材，不把教师运行写成玩家通关。

复盘采用选择题，核心编码不变。老师负责从当前cell与真实产物整理交接；不要再要求学习者填写总结表。开始下一模块前，读取state.json中的interface_delivery，把本人作品接到该模块界面后验收；规格已写不等于界面已运行。

结构变更的维护顺序是enterprise_course → enterprise_narrative → render_curriculum → check。只改原理/选择题用render_curriculum。教师源码或prompt修改后真实重验；文档改动不需要重跑无关模型。本人格的源码、元数据与输出保留，check与测试通过也不自动推进玩家状态。
