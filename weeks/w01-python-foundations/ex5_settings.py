"""练习 5：配置加载。

后面每一周都要从这里读模型名、超时、最大轮次。现在花 20 分钟做对，
剩下 11 周不用再管。

一条规则：**误配置要大声失败**。少了 API key 就在启动时报错退出，
不要跑到第 8 轮工具调用时才抛一个看不懂的 401。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    """从环境变量加载的运行配置。

    字段（对照仓库根目录的 .env.example）：
    - default_model: str，形如 "deepseek:deepseek-chat"，必填
    - max_agent_iterations: int，默认 10，必须 >= 1
    - llm_timeout_seconds: float，默认 60，必须 > 0
    - langsmith_tracing: bool，默认 False
    """

    default_model: str
    max_agent_iterations: int = 10
    llm_timeout_seconds: float = 60.0
    langsmith_tracing: bool = False


def load_settings(env_file: Path | None = None) -> Settings:
    """读 .env 并构造 Settings，缺必填项就抛异常。

    要求：
    - 用 python-dotenv 的 load_dotenv 读入 env_file（None 时读默认位置）
    - 环境变量名是字段名的大写形式：DEFAULT_MODEL、MAX_AGENT_ITERATIONS ...
    - 已存在的环境变量优先于 .env 文件（override=False）
    - 缺 default_model 时抛出，异常信息里要出现 "DEFAULT_MODEL"
      —— 报错信息要能直接告诉人该去设哪个变量，这是 fail loud 的意思

    注意 "true"/"1"/"yes" 都该解析成 True，pydantic 已经帮你处理了大部分。
    """
    raise NotImplementedError


def resolve_model(settings: Settings) -> tuple[str, str]:
    """把 "provider:model" 拆成 (provider, model)。

    格式不对（没有冒号、或有多个冒号）要抛 ValueError，信息里带上原始值。
    第 3 周 init_chat_model 吃的就是这个格式，先自己解析一遍。
    """
    raise NotImplementedError


if __name__ == "__main__":
    settings = load_settings()
    provider, model = resolve_model(settings)
    print(f"provider={provider} model={model}")
    print(f"最大轮次={settings.max_agent_iterations} 超时={settings.llm_timeout_seconds}s")
