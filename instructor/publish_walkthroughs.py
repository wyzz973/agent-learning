"""将导师已审阅的逐关源码观察整理为共同教案，不发布模型草稿的推测性诊断。"""

import json

import nbformat

from instructor.author_course import write_json
from instructor.authoring_contracts import current_source_quote
from instructor.check import ROOT, load_catalog

# 中文教学段落保留原意，格式规则检查运行代码。
# ruff: noqa: E501

FLOW_CORRECTIONS = {
    (
        "M01-T01",
        1,
    ): "SYSTEM_PROMPT是str，print只显示这次岗位、目标、来源和说话要求，此刻尚未发请求。随后SystemMessage才用它构造控制消息；正文与问题在运行时另交，岗位身份不会自动把公告传给模型。",
    (
        "M01-T03",
        0,
    ): "两个str参数是本次问题和资料。strip判空；成功时返回新的消息列表，含当前SYSTEM_PROMPT和由本次参数构造的HumanMessage。函数会读取岗位提示，但不改传入的字符串。定义函数尚未发请求。",
    (
        "M02-T02",
        1,
    ): 'functions是字典，值保存函数对象。functions["announce"]取出函数存进selected_function；selected_function("请核对申请号")才调用，返回提示字符串。字典取值与执行是两步，函数对象本身不是字典。',
    (
        "M02-T02",
        2,
    ): "local_result是本地字典；json.dumps将Python的False写为JSON的false，并使用JSON规定的双引号。json.loads把文本读回dict，ok再次成为bool。这个语法例子没有实际执行工具。",
    (
        "M03-T04",
        0,
    ): "receipts注解为带operator.add元数据的list[str]。框架用这个reducer拼接两分支的更新；它保留两份列表，不自动去重或稳定排序。并发写未配置reducer的同一普通字段会产生冲突，不能依赖覆盖顺序。",
    (
        "M03-T04",
        1,
    ): 'START分别连到left/right形成fan-out。add_edge(["left", "right"], END)要求两条分支满足汇合后进入终点。终点说明调度结束；operator.add不证明业务成功、执行先后或去重。',
    (
        "M04-T02",
        0,
    ): "节点把draft与问题交给interrupt。图保存暂停信息并把控制交回调用者，此处尚未交回title更新。Command恢复后会重新进入节点，interrupt收到恢复值；不是把原Python调用栈一直挂在内存等待。",
    (
        "M04-T04",
        0,
    ): "example是str；len给出字符数，example[:8]得到新字符串，example原值不变。Python字符串切片不是可共享修改的视图。打印原串与新串可以检查信息损失；字符数也不是模型token数。",
    (
        "M04-T05",
        0,
    ): "required_ids保存必须提供的来源身份，observed_ids记录实际交付的身份。difference取得未提供的ID，再sorted得到稳定的缺口列表。这是输入证据检查，不能单凭missing_ids推断模型内部怎样思考。",
    (
        "M05-T05",
        0,
    ): "enumerate(ranking, 1)提供从1开始的名次；scores按ID累加1/(60+rank)。同一候选在不同排序单出现会得到多份贡献；这个小示范没有防止单内重复累计，本人契约需另处理。k是平滑参数，不是次数上限或可信度。",
    (
        "M06-T02",
        0,
    ): "输入是固定查询persistence与条数上限1。search_official返回候选列表，取第一项URL后fetch_public取得公开来源对象。先检查列表非空，再检查ok；候选命中、正文取得和结论支持分别验收。",
    (
        "M06-T03",
        2,
    ): "snapshot_input([source])将这次取得的来源转成公开文本，拼进新请求。与损坏路径对照的重点是是否交付原文；两条提示的引导措辞也不同。严格消融时，应把引导句固定，只改变原文这一项。",
    (
        "M07-T04",
        1,
    ): "两条消息列表各取最后一项.text，交给Markdown显示。Notebook前端会渲染正文；纯文本导出可能只显示Markdown对象名称，不能把纯文本摘要当完整答复。需要在原Notebook或保存产物核对内容。",
    (
        "M07-T04",
        2,
    ): "遍历AIMessage中的tool_calls，按消息顺序提取申请工具名；普通问题与工具回执不进入列表。它展示模型申请过什么，真实执行需再与ToolMessage、工具日志和副作用账本配对核对。",
    (
        "M08-T01",
        1,
    ): "真实Docker运行返回demo_before，stderr保留失败详情，test_count核对固定五项确实执行，ok为False。save_record保存这次结果；测试条数、失败原因和源码SHA要分别看，不能只读一行截断摘要。",
    (
        "M08-T04",
        2,
    ): "lab.ask明确返回公开答复字符串；它接收当前模型、岗位提示和本次公告文本，await等待真实请求。Markdown显示该字符串，save_public保存answer/notice/scope。这个调用验证输入边界，不证明补丁已运行或通过。",
    (
        "M09-T02",
        0,
    ): "三个字符串question/paper/revision先组成JSON数组文本，再以UTF-8编码为bytes并计算SHA256。hexdigest返回64个十六进制字符，不是64位二进制。资料或提示版本改变应影响键；tenant/user等作用域仍需加入本人实际缓存契约。",
    (
        "M09-T04",
        0,
    ): "先拒绝空expected，再用hmac.compare_digest比较本地演练的同型ASCII字符串。它减少比较内容引起的时序差异，类型与长度仍需约束；这一小函数不提供完整认证、身份授权或秘密存储。",
    (
        "M10-T04",
        0,
    ): "先写真实文件，read_bytes取得bytes，sha256产生32字节摘要，hexdigest返回64个十六进制字符。再次写入后重新计算并比较，证明内容变动使旧指纹失效；一个SHA本身不证明测试或业务质量。",
    (
        "M10-T04",
        2,
    ): "lab.ask使用当前模型和实际公告返回str；display交给Markdown前端呈现，save_public保存answer/notice/scope。本格仅验证当前输入与保存边界，没有完成本人清单或全馆验收。",
}

WHY_CORRECTIONS = {
    "M03-T02": "一次模型调用可能只提出取件申请；取得回执后，如果马上END，模型还没有看见新依据。本页先观察只有一程的教师图，确认回执在哪里出现，再由本人接回模型形成有限循环。明确停止条件防止重复动作；单轮无外部资料的答复不需要这条工具回程。",
    "M03-T04": "两条分支同时交回receipts时，需要明确定义合并。operator.add保留两份列表；本人进一步按来源身份去重、保留版本冲突与失败，并稳定排序。fan-in保证到汇合点再继续，不能由列表顺序推断真实完成顺序。没有独立任务时，不必并行或引入子图。",
    "M07-T04": "比较成熟Harness前，先固定问题、原始资料与允许行为，再记录各自实际启用的设施。本页两端通过不同方式取得文件上下文，这种接线差异本身就要写进比较。申请名、回执和预算分开检查；没有控制输入和默认值的对照，无法把质量变化归因于框架。",
    "M08-T04": "补丁交付要同时核对允许路径、固定测试与当前候选。SHA只识别内容，不执行代码；实际测试回执还须对应同一版源码。测试通过后再改动，旧绿立即失效。单机演练也保留这个区分，后续多人维修才能避免错版本交接。",
    "M09-T01": "astream逐块交回公开片段，一块可能包含多个token，也可能没有可显示正文。消费者记录已经到达的片段，最后确认是否完整；取消或超时后保留partial与停止原因。只需完整一次答复时可用ainvoke；需要进度和中途停止时才加入流式控制。",
    "M09-T04": "认证负责确认身份，授权负责检查这个身份能办什么。身份来自服务可信通道，不能由问题正文或客户传入的authenticated=True冒充。本页比较401/200只是认证设施演练；本人继续检查user、动作和失败回执，健康接口也不能替代这些边界。",
    "M10-T01": "组件注册表把允许路线与各组件实现分开，入口按kind调用当前函数并保留真实结果。少量固定路线用if/else也可成立；注册表便于明确替换与检查缺组件。只有需要途中根据观察改变动作时才引入Agent循环，维护路线仍须先检查许可。",
}


def main() -> None:
    """发布44关的原位解释；三条观察逐字校验，其他模型推测不进入教材。"""
    catalog = load_catalog()
    enrichment = json.loads((ROOT / "instructor/course_enrichment.json").read_text())
    records = {}
    for task in catalog["tasks"]:
        draft = json.loads(
            (
                ROOT / "outputs/enterprise-redesign/walkthrough-drafts" / (task["id"] + ".json")
            ).read_text()
        )
        notebook = nbformat.read(ROOT / task["notebook"], as_version=4)
        sources = {c.id: c.source for c in notebook.cells if c.cell_type == "code"}
        rows = [
            "## 这份示范具体怎样工作",
            WHY_CORRECTIONS.get(task["id"], draft["why"]),
            "下面引用的是已有教师格中的语句片段，用来定位数据流；请回原格运行完整代码，不需要复制这些片段创建新格。",
        ]
        for index, observation in enumerate(draft["observations"][:3]):
            observation["quote"] = current_source_quote(
                observation["quote"], sources[observation["cell_id"]]
            )
            flow = FLOW_CORRECTIONS.get((task["id"], index), observation["data_flow"])
            rows += [
                f"### 观察{index + 1} · `{observation['cell_id']}`",
                "```python\n" + observation["quote"].strip() + "\n```",
                flow,
            ]
        rows += [
            "### 接到本人的实现",
            task["quest"]["player_action"],
            "**做一次单因素对照：**" + task["quest"]["replay"],
            "**换输入迁移：**" + task["quest"]["transfer"],
            "先比较本次参数与实际模型输入，再检查执行回执和最后输出。定位第一处偏差，"
            "只改这一层；类型注解、框架调用成功和故事描述都不能替真实数据证明完成。",
        ]
        text = "\n\n".join(rows) + "\n"
        enrichment["tasks"][task["id"]]["process_walkthrough"] = text
        records[task["id"]] = {
            "reviewed_observations": 3,
            "source_quotes_verified": True,
            "excluded": ["unreviewed_extra_observations", "model_diagnose", "model_bridge"],
            "scope": "讲解教师现有代码；没有本人答案",
        }
    write_json(ROOT / "instructor/course_enrichment.json", enrichment)
    write_json(ROOT / "outputs/enterprise-redesign/walkthrough-review.json", records)
    print("44关解释审核发布；修正错误层次、SHA长度、reducer与interrupt等表述。")


if __name__ == "__main__":
    main()
