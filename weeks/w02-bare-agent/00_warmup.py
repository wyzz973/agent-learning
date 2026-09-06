"""语法热身：本周练习会用到的新写法。

**做练习之前先跑这个文件**，只读只跑不用写，约 15 分钟。

    uv run python weeks/w02-bare-agent/00_warmup.py

本周的重点从"异步"转到"数据结构和类"——agent 的本质是维护一个消息列表，
所以字典、列表、类这几样要用得顺手。

上周的语法仍然通用，速查见 ../../SYNTAX_CARDS.md。
"""

from __future__ import annotations

import json
from typing import Any, Protocol, TypedDict


def section(title: str) -> None:
    """打印分节标题。

    Args:
        title: 小节名。
    """
    print(f"\n{'=' * 8} {title} {'=' * 8}")


# ═══════════════ 1. 类：把数据和操作放一起 ═══════════════


class Counter:
    """一个最小的类。agent 的消息历史、工具注册表都会做成类。"""

    def __init__(self, start: int = 0) -> None:
        """构造函数，创建实例时自动调用。

        Args:
            start: 初始值。
        """
        # self 指向"这个实例自己"。挂在 self 上的东西，实例活多久它就活多久。
        self.value = start
        self.history: list[int] = []  # 每个实例有自己的一份，互不干扰

    def add(self, n: int) -> int:
        """加 n 并记录。

        Args:
            n: 要加的数。

        Returns:
            加完之后的值。
        """
        self.value += n
        self.history.append(self.value)
        return self.value


def demo_class() -> None:
    """类的定义、实例化、方法调用。"""
    section("1. 类")

    a = Counter()  # 调用 Counter() 就是在调 __init__
    b = Counter(start=100)  # 两个实例互不影响

    a.add(1)
    a.add(2)
    b.add(5)

    print(f"a.value={a.value} a.history={a.history}")
    print(f"b.value={b.value} b.history={b.history}")
    print("调方法时不用传 self，Python 自动把实例传进去")


# ═══════════════ 2. TypedDict：给字典定形状 ═══════════════


class Message(TypedDict):
    """一条对话消息。这就是本周要维护的核心数据结构。"""

    role: str  # "system" / "user" / "assistant" / "tool"
    content: str


def demo_typeddict() -> None:
    """TypedDict 说明字典该有哪些键，但运行时它就是个普通字典。"""
    section("2. TypedDict")

    msg: Message = {"role": "user", "content": "你好"}
    print(f"它就是个普通字典: {msg}")
    print(f"取值也一样: msg['role'] = {msg['role']}")
    print(f"type 是 dict: {type(msg).__name__}")
    print("好处：编辑器知道有哪些键，拼错 msg['rols'] 会被标红")
    print("注意：它不做运行时检查，塞个不存在的键进去也不会报错")


# ═══════════════ 3. 字典的嵌套取值 ═══════════════


def demo_nested_dict() -> None:
    """模型返回的 JSON 是多层嵌套的，取值要防 None。"""
    section("3. 嵌套字典取值")

    # 这就是 LLM 返回的响应大致长的样子
    response: dict[str, Any] = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "上海"}',
                            },
                        }
                    ],
                }
            }
        ]
    }

    message = response["choices"][0]["message"]
    print(f"层层下钻: {message['tool_calls'][0]['function']['name']}")

    # 用 [] 取不存在的键会 KeyError，用 .get 返回 None
    print(f"message.get('content') = {message.get('content')}")
    print(f"message.get('不存在') = {message.get('不存在')}")
    print(f"给个兜底值: {message.get('不存在', '默认')}")

    # 常见写法：先取再判断，而不是假设它一定存在
    tool_calls = message.get("tool_calls") or []
    print(f"or [] 兜底，即使是 None 也能安全遍历: 有 {len(tool_calls)} 个 tool_call")


# ═══════════════ 4. JSON 与 Python 的互转 ═══════════════


def demo_json() -> None:
    """模型的工具参数是 JSON 字符串，要转成字典才能用。"""
    section("4. JSON")

    arguments = '{"city": "上海", "days": 3}'  # 模型给你的就是这样一个字符串
    print(f"这是字符串: {type(arguments).__name__} {arguments}")

    parsed = json.loads(arguments)  # 字符串 -> 字典
    print(f"loads 之后是字典: {type(parsed).__name__} {parsed}")
    print(f"现在能取值了: parsed['city'] = {parsed['city']}")

    back = json.dumps(parsed, ensure_ascii=False)  # 字典 -> 字符串
    print(f"dumps 转回字符串: {back}")
    print("ensure_ascii=False 才会保留中文，否则会变成 \\u4e0a\\u6d77")

    # 模型偶尔会返回不合法的 JSON，要接住
    try:
        json.loads("{坏掉的")
    except json.JSONDecodeError as error:
        print(f"解析失败要接住: {type(error).__name__}")


# ═══════════════ 5. 列表操作与复制的坑 ═══════════════


def demo_list_and_copy() -> None:
    """消息历史是个列表，加元素和复制都有坑。"""
    section("5. 列表与复制")

    messages = [{"role": "user", "content": "hi"}]

    messages.append({"role": "assistant", "content": "hello"})  # 加一个
    messages.extend([{"role": "user", "content": "?"}])  # 加一批
    print(f"append 加一个，extend 加一批，现在 {len(messages)} 条")

    print(f"切片取最后两条: {[m['role'] for m in messages[-2:]]}")
    print(f"切片去掉第一条: {[m['role'] for m in messages[1:]]}")

    # 赋值不是复制，两个名字指向同一个列表
    same = messages
    same.append({"role": "user", "content": "新的"})
    print(f"改 same 之后 messages 也变了: {len(messages)} 条 ← 它们是同一个东西")

    copied = messages.copy()  # 或 list(messages)
    copied.append({"role": "user", "content": "再来"})
    print(f"copy 之后各走各的: messages {len(messages)} 条, copied {len(copied)} 条")


# ═══════════════ 6. 可变默认参数的坑 ═══════════════


def bad_append(item: str, target: list[str] = []) -> list[str]:  # noqa: B006
    """默认值是列表时，所有调用共享同一个列表——经典陷阱。

    Args:
        item: 要加的东西。
        target: 默认参数，只在函数定义时创建一次。

    Returns:
        加完之后的列表。
    """
    target.append(item)
    return target


def good_append(item: str, target: list[str] | None = None) -> list[str]:
    """正确写法：默认值用 None，进函数再造新列表。

    Args:
        item: 要加的东西。
        target: 不传就新建一个。

    Returns:
        加完之后的列表。
    """
    if target is None:
        target = []
    target.append(item)
    return target


def demo_mutable_default() -> None:
    """默认参数只在定义函数时求值一次，不是每次调用都新建。"""
    section("6. 可变默认参数的坑")

    print(f"bad_append('a')  = {bad_append('a')}")
    print(f"bad_append('b')  = {bad_append('b')}  ← 上一次的 a 还在！")
    print(f"good_append('a') = {good_append('a')}")
    print(f"good_append('b') = {good_append('b')}  ← 干净")


# ═══════════════ 7. match：按类型分发 ═══════════════


def demo_match() -> None:
    """按消息角色分发处理，比一长串 if/elif 清楚。"""
    section("7. match 语句")

    for msg in [
        {"role": "user", "content": "问题"},
        {"role": "tool", "content": "工具结果"},
        {"role": "unknown", "content": "?"},
    ]:
        match msg["role"]:
            case "user":
                print("  user  -> 这是我说的话")
            case "assistant":
                print("  assistant -> 模型说的话")
            case "tool":
                print("  tool  -> 工具执行结果")
            case other:  # 兜底，other 会绑定实际值
                print(f"  {other} -> 没见过的角色，兜底处理")


# ═══════════════ 8. Protocol：只看长相不看血统 ═══════════════


class Speaker(Protocol):
    """任何有 speak() 方法的东西都算 Speaker，不用继承。"""

    def speak(self) -> str:
        """说一句话。

        Returns:
            说的内容。
        """
        ...


class Dog:
    """它没有继承 Speaker，但长得像。"""

    def speak(self) -> str:
        """汪。

        Returns:
            叫声。
        """
        return "汪"


def make_it_speak(speaker: Speaker) -> None:
    """只要求"有 speak 方法"，不要求是谁的子类。

    Args:
        speaker: 任何有 speak() 的对象。
    """
    print(f"  它说: {speaker.speak()}")


def demo_protocol() -> None:
    """Protocol 让"真的 LLM"和"假的 LLM"能互换，这是本周测试的基础。"""
    section("8. Protocol")

    make_it_speak(Dog())
    print("Dog 没继承 Speaker，但有 speak() 方法就够了")
    print("本周会用它定义 LLM 接口：真实模型和测试用的假模型都满足同一个 Protocol")
    print("这样测试完全离线，不花钱、不联网、结果确定")


def main() -> None:
    """按顺序跑完所有小节。"""
    demo_class()
    demo_typeddict()
    demo_nested_dict()
    demo_json()
    demo_list_and_copy()
    demo_mutable_default()
    demo_match()
    demo_protocol()
    print("\n跑完了。回去做练习，卡住就回来查对应小节。")


if __name__ == "__main__":
    main()
