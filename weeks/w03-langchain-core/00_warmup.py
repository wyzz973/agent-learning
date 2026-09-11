"""语法热身：本周练习用到的每一个 Python 写法。

**做练习之前先跑这个**，只读只跑不用写。

    uv run python weeks/w03-langchain-core/00_warmup.py

跑完再跑 01_langchain_api.py（LangChain 的五个入口）。

这个文件的每一节都对应练习里的某一处。卡住时回来查，
按小节标题里写的"用在哪"定位。
"""

from __future__ import annotations

import json

# ═══════════ 1. isinstance：判断一个东西是不是某个类型 ═══════════
#    用在 ex1 extract_tool_calls：只处理 AIMessage，跳过其他消息


def demo_isinstance() -> None:
    """isinstance(对象, 类) 返回 True/False。"""
    print("\n======== 1. isinstance（用在 ex1）========")

    items = [1, "文字", 3.5, "又一个文字", [1, 2]]

    print("只挑出字符串：")
    for item in items:
        if not isinstance(item, str):
            continue  # 不是字符串就跳过这一轮，直接进入下一个 item
        print(f"  {item!r}")

    print("\ncontinue 的意思是'这轮不做了，下一个'。")
    print("等价于把逻辑倒过来写 if isinstance(...): 然后缩进一层，")
    print("但用 continue 能少一层缩进，读起来更平。")


# ═══════════ 2. 两层嵌套循环：列表里装着列表 ═══════════
#    用在 ex1 extract_tool_calls：外层遍历消息，内层遍历每条消息的 tool_calls


def demo_nested_loop() -> None:
    """外层循环拿到一个个"批"，内层循环拿到批里的"个"。"""
    print("\n======== 2. 两层循环（用在 ex1）========")

    # 三个订单，每个订单里有若干商品
    orders = [
        {"user": "小王", "items": [{"name": "键盘", "price": 200}, {"name": "鼠标", "price": 80}]},
        {"user": "小李", "items": []},  # 空列表，内层循环一次都不执行，不会报错
        {"user": "小张", "items": [{"name": "显示器", "price": 1200}]},
    ]

    flat: list[dict[str, object]] = []

    for order in orders:  # 外层：一个个订单
        for item in order["items"]:  # 内层：这个订单里的一个个商品
            # 到这一层，item 才是能用 ['name'] 取值的字典
            flat.append({"user": order["user"], "name": item["name"]})

    print("压平之后：")
    for row in flat:
        print(f"  {row}")

    print("\n关键：order['items'] 是列表，不能直接 order['items']['name']。")
    print("必须再 for 一层，把里面的字典取出来才能用 ['name']。")


# ═══════════ 3. eval：把字符串当成 Python 代码算出来 ═══════════
#    用在 ex2 calculator


def demo_eval() -> None:
    """eval 直接求值，不用自己解析运算符。"""
    print("\n======== 3. eval（用在 ex2）========")

    for expr in ["23 * 17", "10 / 4", "(2 + 3) * 4"]:
        print(f"  eval({expr!r}) = {eval(expr)}")

    print("\n加减乘除、括号优先级，它全都处理好了，你不需要判断表达式里有什么。")
    print("代价：它什么都执行，所以必须先用白名单挡住危险字符。")
    print("ex2 第 1 步那段 set(expression) <= allowed 就是干这个的。")


# ═══════════ 4. try / except / raise ... from ═══════════
#    用在 ex2 calculator：接住 eval 的错误，转成 ValueError


def demo_exception_chaining() -> None:
    """在 except 里抛新异常时，要说明和原异常的关系。"""
    print("\n======== 4. raise ... from（用在 ex2）========")

    def convert(expression: str) -> str:
        try:
            value = eval(expression)
        except Exception as error:
            # error 是接住的原始异常对象。
            # from error 表示"这个新异常是由 error 引起的"，traceback 会显示两层。
            # 不写 from，Python 会自动串联并打印一句
            # "During handling of the above exception, another exception occurred"，
            # 看起来像是你的错误处理本身出了 bug。
            raise ValueError(f"计算 {expression!r} 失败：{error}") from error
        return str(value)

    print(f"  正常: {convert('2 + 2')}")
    try:
        convert("1 / 0")
    except ValueError as error:
        print(f"  出错: {error}")
        print(f"  原始异常还留着: {type(error.__cause__).__name__}")

    print("\n三种写法的区别：")
    print("  raise X(...) from error  保留原因，traceback 显示两层（推荐）")
    print("  raise X(...) from None   明确丢弃原因，traceback 只有一层")
    print("  raise X(...)             不说明，Python 自动串联，信息最乱")


# ═══════════ 5. f-string 的格式说明，以及嵌套大括号 ═══════════
#    用在 ex2 calculator：按 precision 位小数格式化


def demo_fstring_format() -> None:
    """冒号后面是格式说明，大括号可以嵌套。"""
    print("\n======== 5. f-string 格式化（用在 ex2）========")

    value = 2.5
    print(f"  f'{{value}}'      = {value}          ← 原样")
    print(f"  f'{{value:.2f}}'  = {value:.2f}       ← 固定两位小数")
    print(f"  f'{{value:.4f}}'  = {value:.4f}     ← 固定四位小数")

    print("\n位数写死不灵活，要从变量来就嵌一层大括号：")
    for precision in [0, 1, 3]:
        # 内层 {precision} 先被替换成数字，整个格式说明变成 .0f / .1f / .3f
        print(f"  precision={precision} → f'{{value:.{{precision}}f}}' = {value:.{precision}f}")

    print("\n其他常用的格式说明：")
    print(f"  {'左对齐':　<8}|  ← f'{{x:<8}}' 左对齐补到 8 格")
    print(f"  {42:>6}|  ← f'{{x:>6}}' 右对齐补到 6 格")
    print(f"  {0.856:.1%}  ← f'{{x:.1%}}' 百分比")
    print(f"  {'带引号'!r}   ← f'{{x!r}}' 显示引号和转义，调试时用")


# ═══════════ 6. 字典查重：放进去之前先看在不在 ═══════════
#    用在 ex2 build_tool_index


def demo_dict_duplicate_check() -> None:
    """字典赋值会静默覆盖，要主动检查。"""
    print("\n======== 6. 字典查重（用在 ex2）========")

    pairs = [("a", 1), ("b", 2), ("a", 99)]

    silent: dict[str, int] = {}
    for key, value in pairs:
        silent[key] = value  # 重复的键直接覆盖，一声不吭
    print(f"  不检查: {silent}   ← a 的值 1 被 99 悄悄换掉了")

    checked: dict[str, int] = {}
    for key, value in pairs:
        if key in checked:  # in 用在字典上，查的是键
            print(f"  检查后: 发现重复键 {key!r}，抛错")
            break
        checked[key] = value

    print("\n为什么重要：工具重名会让模型调 A 实际执行 B，极难排查。")


# ═══════════ 7. 继承与方法覆盖 ═══════════
#    用在 ex3 ScriptedChatModel（我已写好，但要看懂）


def demo_inheritance() -> None:
    """继承拿到父类的全部能力，覆盖只换掉其中一个方法。"""
    print("\n======== 7. 继承与覆盖（用在 ex3）========")

    class Base:
        """父类：有两个方法。"""

        def greet(self) -> str:
            return "你好"

        def describe(self) -> str:
            return f"我会说：{self.greet()}"

    class Child(Base):  # 括号里写父类，就继承了它的所有方法
        """子类：只改 greet，describe 原样继承。"""

        def greet(self) -> str:  # 同名方法会覆盖父类的
            return "Hello"

    print(f"  Base().describe()  = {Base().describe()}")
    print(f"  Child().describe() = {Child().describe()}")
    print("\n注意 describe 没有重写，但它调用的 self.greet() 变成了子类的版本。")
    print("ex3 的 ScriptedChatModel 就是这么做的：继承 GenericFakeChatModel")
    print("拿到'按顺序吐消息'的能力，只补一个 bind_tools。")


# ═══════════ 8. 取列表最后一个元素 ═══════════
#    用在 ex3 run_agent：最终答案是最后一条消息


def demo_negative_index() -> None:
    """负数下标从末尾数起。"""
    print("\n======== 8. 负数下标（用在 ex3）========")

    messages = ["第一条", "第二条", "第三条", "最后一条"]
    print(f"  messages[0]  = {messages[0]!r}   第一个")
    print(f"  messages[-1] = {messages[-1]!r}  最后一个")
    print(f"  messages[-2] = {messages[-2]!r}   倒数第二个")
    print(f"  messages[-2:] = {messages[-2:]}  最后两个（切片）")


# ═══════════ 9. json.loads：JSON 字符串转字典 ═══════════
#    用在 ex1 from_dicts：w02 的 arguments 是字符串，要转成字典


def demo_json_loads() -> None:
    """w02 的 arguments 是 JSON 字符串，LangChain 的 args 是字典。"""
    print("\n======== 9. json.loads（用在 ex1）========")

    w02_style = '{"city": "上海"}'
    print(f"  w02 的 arguments: {w02_style!r}  类型 {type(w02_style).__name__}")

    langchain_style = json.loads(w02_style)
    print(f"  json.loads 之后:  {langchain_style}  类型 {type(langchain_style).__name__}")
    print(f"  现在能取值了: ['city'] = {langchain_style['city']!r}")


# ═══════════ 10. match：按值分发 ═══════════
#    用在 ex1 from_dicts：按 role 造不同的消息类


def demo_match() -> None:
    """一个值有好几种情况时，match 比一长串 if/elif 清楚。"""
    print("\n======== 10. match（用在 ex1）========")

    for role in ["system", "user", "assistant", "tool", "拼错的"]:
        match role:
            case "system":
                result = "SystemMessage"
            case "user":
                result = "HumanMessage"
            case "assistant":
                result = "AIMessage"
            case "tool":
                result = "ToolMessage"
            case other:  # 兜底，other 绑定实际的值
                result = f"不认识的 role: {other!r} → 要抛 ValueError"
        print(f"  {role:10} → {result}")

    print("\n最后那个 case other 是兜底分支，必须有——")
    print("误配置要大声失败，不能悄悄跳过。这是 w01 学的规则。")


def main() -> None:
    """按顺序跑完所有小节。"""
    demo_isinstance()
    demo_nested_loop()
    demo_eval()
    demo_exception_chaining()
    demo_fstring_format()
    demo_dict_duplicate_check()
    demo_inheritance()
    demo_negative_index()
    demo_json_loads()
    demo_match()
    print("\n跑完了。再跑 01_langchain_api.py，然后开始做练习。")
    print("练习里卡住，按小节标题里的'用在 exN'回来查。")


if __name__ == "__main__":
    main()
