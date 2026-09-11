"""练到的 Python：列表成员、计数、除法、None；用在 ex1_eval。"""

from pydantic import BaseModel, ConfigDict, ValidationError

print("1. 用在 ex1：in 与 not in")
names = ["Lin", "Chen"]
print("Lin" in names, "Wang" not in names)
print("2. 用在 ex1：循环计数")
count = 0
for number in [3, 8, 2]:
    if number > 5:
        count = count + 1
print(count)
print("3. 用在 ex1：除法与零样本")
print(2 / 3, len([]), None)
print("不能计算 0/0；没有观测结果时用 None 表示未知。")
print("4. 用在 structured_demo：JSON 编码是字符串，模型校验是另一个动作。")


class Label(BaseModel):
    """字段声明用于框架校验；name 要求字符串，不允许额外字段。"""

    model_config = ConfigDict(extra="forbid", strict=True)
    name: str


label = Label.model_validate({"name": "Lin"})
print("5. 用在 structured_demo：继承 BaseModel，声明字段，通过属性取值：", label.name)
try:
    Label.model_validate({"name": 42})
except ValidationError as error:
    print("类型不符合要求：", error.errors())
