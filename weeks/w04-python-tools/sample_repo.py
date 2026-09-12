# 全周数据｜内存里的迷你仓库，不用改
"""练习数据：内存中的迷你仓库；这些路径不对应磁盘文件。

练到的 Python：list[dict[str, str]]；列表里的一项是一个字典。
"""

FILES: list[dict[str, str]] = [
    {"path": "src/retry.py", "content": "Retry failed requests with a maximum attempt count."},
    {"path": "src/chat.py", "content": "Send messages to a model and receive a reply."},
    {"path": "README.md", "content": "Configure retry and timeout before running the agent."},
    {"path": "tests/test_chat.py", "content": "Check that message history keeps its order."},
]
