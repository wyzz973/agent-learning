"""w04 语法热身：每次只读当天对应的小节，预测 print，再运行。

练到的 Python：变量与类型注解、列表/字典取值、for/if、in、字符串方法、
append、len、函数调用与 return、布尔值与 None、跨文件 import。
第 1～3 节用在 ex1；第 4～6 节用在 ex2。这里没有练习答案。
"""

from typing import Any

from sample_repo import FILES

# 1. 用在 ex1：列表 → 字典 → 字符串。类型注解描述值，不会替你创建值。
print("\n1. 一批、一个、一个字段")
print(type(FILES))
record = FILES[0]
print(type(record))
print(record["path"], type(record["path"]))
print(FILES[0]["path"])

# 2. 用在 ex1：每轮拿到一条记录，再把需要的值收集起来。
print("\n2. for、if、append")
numbers: list[int] = [2, 5, 8]
selected: list[int] = []
for number in numbers:
    print("这一轮的 number:", number)
    if number > 4:
        selected.append(number)
print("收集后:", selected)
print("空列表循环:")
for number in []:
    print(number)

# 3. 用在 ex1：字符串方法返回新字符串，不会修改原字符串。
print("\n3. 字符串方法、in、字典组装")
word = "  HELLO  "
cleaned = word.strip().lower()
print("原值:", word, "新值:", cleaned)
print("hello" in "say hello")
print("hello" in "say goodbye")
print("两个条件满足一个就行:", "hello" in "say hello" or "hello" in "goodbye")
print("  ".strip() == "")
first = "say"
second = "hello"
print(first + " " + second)
person = {"name": "Lin", "city": "Shanghai"}
small_record = {"name": person["name"]}
print("原字典:", person, "新字典:", small_record)

# 4. 用在 ex2：调用方接收 return 的值，不会自动收到 print 的文字。
print("\n4. 参数、调用、接住返回值")


def add_one(number: int) -> int:
    """返回加一后的整数，示范参数和返回值。

    Args:
        number: 一个整数；本例不做运行时类型校验。
    Returns:
        加一后的整数。
    Raises:
        TypeError: 传入无法与整数相加的值。
    """
    result = number + 1  # 计算并把结果保存在本函数的变量中。
    return result  # 把这个值交给调用方。


answer = add_one(4)
print("接住了:", answer)
next_answer = add_one(answer)
print("传给下一个函数:", next_answer)

# 5. 用在 ex2：提前 return 会结束整个函数，不只是结束 if 分支。
print("\n5. 每条路径都返回")


def describe_number(number: int) -> str:
    """按数值返回一句话，示范两条返回路径。

    Args:
        number: 一个整数；允许零和负数。
    Returns:
        正数返回 positive，其余返回 zero or negative。
    Raises:
        TypeError: 传入无法与整数比较的值。
    """
    if number > 0:  # 检查第一条分支。
        return "positive"  # 立即结束本次函数调用。
    return "zero or negative"  # 覆盖剩余的情况。


print(describe_number(2))
print(describe_number(0))
empty: list[str] = []
print("append 的返回值:", empty.append("saved"))
print("列表本身:", empty)
print("print 的返回值:", print("这行是显示给人看的"))

# 6. 用在 ex2：Any 允许这个教学字典中的不同字段拥有不同值类型。
print("\n6. 固定字段、len、True / False、None")
payload: dict[str, Any] = {"ready": True, "names": ["Lin"], "problem": None}
print(payload)
print("一共有:", len(payload["names"]))
print("空列表长度:", len([]))
print("True 和 False 是布尔值；None 表示这里没有值。")
print("Any 只影响类型检查，不会自动校验字典，也不会修正键名。")
print("from sample_repo import FILES 从同目录文件导入数据。")
print("练习里的 NotImplementedError 是留给你写的占位符，写完相应段落后删除。")

# 入口判断区分直接运行与被导入；导入时不自动运行练习调用。
if __name__ == "__main__":
    print("热身结束：今天只需要会指出输入类型、循环中的元素、返回类型。")
