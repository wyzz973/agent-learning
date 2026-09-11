"""教师示范：字典、JSON、Pydantic；用在 D18。

练到的 Python：类、属性、异常、字典；不要求自己实现框架校验器。
"""

import json

from pydantic import BaseModel, ConfigDict, ValidationError


class Answer(BaseModel):
    """结构契约：summary 是摘要，paths 是路径列表，禁止多余字段。"""

    model_config = ConfigDict(extra="forbid", strict=True)
    summary: str
    paths: list[str]


if __name__ == "__main__":
    raw = {"summary": "找到一个文件", "paths": ["src/retry.py"]}
    text = json.dumps(raw, ensure_ascii=False)
    print("普通对象：", type(raw), raw)
    print("JSON 字符串：", type(text), text)
    restored = json.loads(text)
    answer = Answer.model_validate(restored)
    print("校验后的对象与属性：", answer, answer.paths)
    try:
        Answer.model_validate({"summary": "缺少 paths"})
    except ValidationError as error:
        print("预期的校验错误：", error.errors())
    print("字段合法仍可能引用不存在的文件；还需 ex1_eval 的来源检查。")
    print("create_agent 的 response_format 约束模型最终回答；本示范只做本地数据校验。")
