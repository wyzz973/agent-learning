"""练习 5：配置加载。

后面每一周都要从这里读模型名、超时、最大轮次。现在花 20 分钟做对，
剩下 11 周不用再管。

一条规则：**误配置要大声失败**。少了 API key 就在启动时报错退出，
不要跑到第 8 轮工具调用时才抛一个看不懂的 401。

练到的 Python：os.environ、字典推导式、None 的处理、Path 对象、
字符串 split、抛出带信息的异常、pydantic 的自动类型转换。

本文件三段坡道：
  1. Settings 类    我已写完
  2. load_settings  骨架给你了，填一个 TODO
  3. resolve_model  独立完成
"""

from __future__ import annotations

import os
from calendar import error
from dataclasses import fields
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ─────────────────────────── 第 1 段：示范，已写完 ───────────────────────────


class Settings(BaseModel):
    """从环境变量加载的运行配置。对照仓库根目录的 .env.example 看。

    【已实现】注意 pydantic 会自动转类型：环境变量永远是字符串，
    但 max_agent_iterations 声明成 int，传 "5" 进来会自动变成 5。
    langsmith_tracing 声明成 bool，"true" / "1" / "yes" 都会变成 True。
    """

    default_model: str = Field(description="形如 deepseek:deepseek-chat")
    max_agent_iterations: int = Field(default=10, ge=1, description="agent 循环上限，防烧钱")
    llm_timeout_seconds: float = Field(default=60.0, gt=0, description="单次 LLM 调用超时")
    langsmith_tracing: bool = Field(default=False, description="是否开启 LangSmith 追踪")


# ────────────────────── 第 2 段：填空，把 TODO 换成代码 ──────────────────────


def load_settings(env_file: Path | None = None) -> Settings:
    """读 .env 并构造 Settings，缺必填项就抛异常。

    要求：已存在的环境变量优先于 .env 文件里的值（所以 override=False）。

    Args:
        env_file: .env 文件路径。传 None 时 load_dotenv 会从当前目录
            往上找最近的 .env——测试里传临时文件，正常运行传 None。

    Returns:
        校验通过的 Settings 实例。

    Raises:
        pydantic.ValidationError: 缺 DEFAULT_MODEL，或某个值转不成声明的类型
            （比如 MAX_AGENT_ITERATIONS 写成了 "abc"）。
    """
    # 第 1 步（已给）：把 .env 文件里的键值读进 os.environ。
    #   override=False 表示：如果某个变量已经在环境里了，不要用文件里的覆盖它。
    #   这样你可以临时 `DEFAULT_MODEL=xxx uv run python ...` 覆盖配置。
    load_dotenv(env_file, override=False)

    # 第 2 步（轮到你）：从 os.environ 里把值取出来，构造 Settings 并返回。
    #
    #   环境变量名是字段名的大写形式：default_model -> DEFAULT_MODEL。
    #   难点是"没设的变量不要传"：如果 MAX_AGENT_ITERATIONS 没设，
    #   你传 None 进去会让 pydantic 报错，而不是用上默认值 10。
    #   所以要先筛掉取不到的，只把真正存在的传进去。
    #
    #   一种写法（自己补完）：
    #       fields = ["default_model", "max_agent_iterations",
    #                 "llm_timeout_seconds", "langsmith_tracing"]
    #       values = {名字: os.environ[名字.upper()] for 名字 in fields
    #                 if 名字.upper() in os.environ}
    #       return Settings(**values)
    #   `**values` 的意思是把字典展开成关键字参数，等于 Settings(default_model="...", ...)。
    #
    #   缺 DEFAULT_MODEL 时 pydantic 自己会抛错，且信息里带字段名——
    #   测试要求异常信息里出现 "DEFAULT_MODEL"，所以想想大小写怎么处理。
    field = ["default_model", "max_agent_iterations", "llm_timeout_seconds", "langsmith_tracing"]
    values = {name: os.environ.get(name.upper()) for name in field if name.upper() in os.environ}
    if "DEFAULT_MODEL" not in os.environ:
        raise ValueError("缺少环境变量 DEFAULT_MODEL,请在 .env 里设置,形如 deepseek:deepseek-chat")
    return Settings(**values)


# ─────────────────── 第 3 段：独立完成，最简单的一个 ───────────────────


def resolve_model(settings: Settings) -> tuple[str, str]:
    """把 "provider:model" 拆成 (provider, model) 两段。

    第 3 周 init_chat_model 吃的就是这个格式，先自己解析一遍。

    要求：格式不对（没有冒号、或有多个冒号、或空字符串）要抛 ValueError，
    异常信息里要带上原始值，方便排查。

    提示：字符串的 .split(":") 返回一个列表，看看它的长度是不是 2。

    Args:
        settings: 已加载的配置，只用到它的 default_model 字段。

    Returns:
        (provider, model) 两元组，例如 ("deepseek", "deepseek-chat")。

    Raises:
        ValueError: default_model 不是恰好一个冒号分隔的两段。
            异常信息里要带上原始值，否则排查时看不出是哪个配置写错了。
    """
    try:
        provider, model = settings.default_model.split(":")
    except ValueError as e:
        raise ValueError(
            f"default_model 不是恰好一个冒号分隔的两段:,{settings.default_model!r}"
        ) from e
    return provider, model


if __name__ == "__main__":
    settings = load_settings()
    provider, model = resolve_model(settings)
    print(f"provider={provider} model={model}")
    print(f"最大轮次={settings.max_agent_iterations} 超时={settings.llm_timeout_seconds}s")
