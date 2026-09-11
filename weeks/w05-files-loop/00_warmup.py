"""练到的 Python：Path、try/except、JSON、对象索引、async/await。

用在 ex1 第 1～3 节，用在 ex2 第 4～6 节；只读只跑，先预测输出。
"""

import asyncio
import json
from pathlib import Path

from langchain.messages import AIMessage
from langchain.tools import tool

print("1. 用在 ex1：路径对象与目录")
root = Path(__file__).resolve().parent
path = root / "00_warmup.py"
print(path.name, path.suffix, path.is_file(), path.is_relative_to(root))
print("绝对路径：", path.is_absolute(), "相对路径：", Path("a.md").is_absolute())
print("解析父目录：", (root / ".." / "w05-files-loop").resolve())
print("字节数：", path.stat().st_size)

print("2. 用在 ex1：读取返回字符串，不是文件对象")
content = path.read_text(encoding="utf-8")
print(type(content), content[:20])
try:
    (root / "missing.md").read_text(encoding="utf-8")
except OSError as error:
    print("捕获读取错误：", type(error).__name__)

print("3. 用在 ex1：两个条件、列表与成功项")
rows = [{"ok": True, "path": "a.md"}, {"ok": False, "path": "b.md"}]
for row in rows:
    print(row["ok"], row["path"])
print(".txt" not in [".py", ".md"])

print("4. 用在 ex2：对象与字典，JSON 字符串与 Python 对象")
data = {"hello": "你好"}
encoded = json.dumps(data, ensure_ascii=False)
print(type(encoded), encoded, json.loads(encoded))


@tool
def greet(name: str) -> str:
    """向指定名字问好。

    Args:
        name: 任意名字字符串。
    Returns:
        问候字符串。
    Raises:
        无：输入由工具参数校验。
    """
    return "你好，" + name  # 普通字符串拼接，外层装饰器负责工具包装。


async def main() -> None:
    print("5. 用在 ex2：取回的是对象，await 才拿到执行结果")
    by_name = {"greet": greet}
    print(by_name["greet"].name, list(by_name.values()))
    call = {"name": "greet", "args": {"name": "Lin"}, "id": "c1", "type": "tool_call"}
    async with asyncio.timeout(5):
        result = await by_name["greet"].ainvoke(call)
    print(type(result), result.content, result.tool_call_id)
    reply = AIMessage(content="完成")
    print("没有工具调用：", not reply.tool_calls)
    print("6. 用在 ex2：有限重复、占位变量与 append")
    history = []
    for _ in range(2):
        history.append("一次")
    print(history, history[-1])
    print("bind_tools 绑定可用工具；ainvoke 收到消息历史，返回下一条 AIMessage。")
    print("return 离开整个函数；只有追加工具结果，下一次模型调用才看得到观察。")


if __name__ == "__main__":
    asyncio.run(main())
