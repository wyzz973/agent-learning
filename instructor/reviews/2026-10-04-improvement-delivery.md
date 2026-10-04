# 雾岛课程审查改进交付与复核

本次按 2026 年 10 月 3 日学生目标审查的十二项问题完善当前课程。主线仍是 LangChain 与 LangGraph，当前入口仍为 M01-T02。改进进入实际 Notebook、统一渲染数据、设施和验收；没有代填本人答案，也没有改变学习通关状态。

课程继续保持 10 个模块、44 份完整 Notebook。新增 35 个原位小步观察，判断卡增加至 115 道；增加本人检索测量、研发对照、消息编解码、开放需求设计与作品证明链。核心会话的可调整估计更新为 159 小时，生产深入另留时间，不能以“一次一小时”承诺复杂任务一小时掌握。

## 十二项问题的落实

| 审查项 | 已进入实际项目的改进 | 核查依据 |
|---|---|---|
| F01 导出依赖 | M01-T02公开前置设施统一STORY_PROMPT与structured_model；导出前检查缺失全局名字 | 独立进程真实当前模型证明；learner_exports与依赖测试 |
| F02 安全迭代 | 先预览差异，再按当前SHA更新；旧代码与origin备份；project独立改动和比较后变化拒绝覆盖 | 预览、修订、竞态及不同来源测试；各关导出格原位说明 |
| F03 跨关接线 | 47处导出声明静态检查；补M07 Literal；运行与来源检查分开；缺实现不回退教师 | check_export_contracts、RAG/研究/权限设施测试、真实服务进程示范 |
| F04 小步支架 | 17关35个具体输入/类型/状态观察；原有16关通用提示改为具体衔接；重复原理正文移除 | course_enrichment.microsteps、Notebook实际执行 |
| F05 复盘偏好 | 当前公告牌的必填文字复盘改为选择卡与真实结果核对；核心编码保留 | 当前M01-T02 pause/debrief与判断卡；没有新增必填学习总结 |
| F06 模型与接口 | 当前页讲token、生成、上下文、训练/推理/文件区别；M09同模型原生HTTP与框架工具循环对照；本人wire编解码 | NativeGateway、真实文本与工具请求、协议配对测试；配置未替换 |
| F07 检索测量 | 16份双语原文、20卡；英文/中文/中文查英文/无答案分组；Recall、Precision、MRR、nDCG及缺测区分 | teacher-retrieval-study与本人run_retrieval_benchmark契约 |
| F08 校准与优化 | 当前模型候选顺序翻转与重复；参考标签隔离；统计区间范围说明；开发失败驱动通用查询改写，再看留出 | 8次真实裁判；真实优化记录、配对统计、本人策略对照练习 |
| F09 工作与求职 | 陌生馆务自由需求、最小架构选择、实际时间与质量；当前代码/origin/验收/演示/运行手册/失败案例证明链 | M10新本人函数、portfolio设施与版本/缺资料测试；岗位判断卡 |
| F10 示范完整性 | 缓存明确绑定内容/prompt/模型/作用域；两次回调与一次实际模型请求分别计数；总期限、参数故障与超时 | teacher-runtime-policy、真实原生工具循环、服务启动失败/取消清理 |
| F11 维护门禁 | 教师格可读规范化；同来源重复导入有准确来源说明；本人样式不当掌握判断；源码引用定位当前代码 | lint_notebooks、AST/字符串引用等价测试、Ruff、mypy、CI模板 |
| F12 学习效果证据 | 各关尝试卡明确帮助程度、程序/迁移/设计信号；当前源码与实际产物指纹；改动使旧内容不匹配；选择题单独记录 | learning_evidence单测与真实浏览器卡片；不写state.progress |

以上是教材和设施交付。本人完整研究、开放项目、独立迁移和作品集仍需学习者实际完成；教师验证、文件存在、参考题答对都不替代这些证据。

## 已取得的真实实验结果

原生接口使用当前ChatDeepSeek对象的模型、地址、温度和thinking参数，教师只读工具在原生与框架两端实际执行。原生公开结果不返回请求头、凭据、原始响应或隐藏推理。该设施对未知提供方和非默认model_kwargs明确拒绝，不冒称通用兼容。

小语料检索中的中文查英文仍有漏检。查询改写会带来新增模型调用，真实运行中也出现平均收益为零的结果；课程保留原始/改写查询、各案退化与小样本区间，不以一项提高宣称全面更好。每次当前输出见实际JSON，不能将一次观察泛化到所有业务。

裁判在两个教师预设参考案例的八次相关重复中曾全部一致。参考标签是本课依据原句预设并核对的素材，未记录真实人工标注流程；相关重复不当作八个独立任务计算总体准确率。本人项目要另外记录标注、分歧与未见输入。

## 显示与使用验收

44份当前Notebook已生成实际HTML预览。Chrome DevTools使用隔离浏览器页检查，代表性检索与作品页在1280和540宽度未观察到页面横向溢出，所查图片没有损坏；长设施源码默认折叠，原文和实际依据保留展开入口。中文标签的粗体边界已修正。

统一接待台实际复用第一关已保存的本人answer_reader，当前临时公告收到18:00闭馆与14:00开门的真实答复。返回后控件可再次使用。尝试卡未预选独立程度或证据，未选择时拒绝保存；诊断留在学习者区域，不自动记通关。

截图通过MCP原生图像查看。该MCP的文件保存根与当前工作区不匹配，因此未把截图文件存在冒充已保存；结构、响应与视口核查记录在visual-delivery-evidence.json。CI模板按[uv官方集成说明](https://docs.astral.sh/uv/guides/integration/github/)固定action版本并只用无凭据设施检查，本地对应命令已运行，未推送或触发远端CI，也未部署公网服务。

## 验收命令与证据位置

使用锁定环境运行：

```sh
uv run --locked python -m instructor.check
uv run --locked python -m instructor.check_export_contracts
uv run --locked python -m instructor.lint_notebooks
uv run --locked ruff check instructor tests modules --exclude '*.ipynb'
uv run --locked mypy
uv run --locked pytest -q
uv run --locked python -m instructor.validate_notebooks --refresh-demo-outputs
uv run --locked python -m instructor.record_validation --verified-on 2026-10-04
```

教师执行器明确跳过exercise/exercise-test，不登记本人完成。当前验收数量以instructor/validation.json为准；十二项追踪在instructor/improvement_plan.json，最终内容身份与范围在outputs/improvements/2026-10-04/delivery-audit.json。

实际专项记录：M05-T05的teacher-retrieval-study.json与teacher-retrieval-optimization.json；M06-T05的teacher-judge-calibration.json；M09-T02的teacher-runtime-policy.json；M09-T03的teacher-native-message-comparison.json与teacher-native-tool-comparison.json。这些文件均为教师实验，本人输出另用owned前缀。

保留检查确认原有80个核心格未变化，首关全部本人格的源码、元数据和已保存输出一致，学习progress一致。没有提交、推送、清空配置或修改模型选择。

课程现在具备较完整的应用工程、独立设计、质量实验与职业交付路径。对标结论仍限定为公开课程中的能力与教学形式；不宣称市场唯一、所有组件最新或学习者已经掌握。实际学习效果会由后续本人尝试、帮助程度与迁移记录持续检验。
