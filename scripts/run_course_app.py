"""运行跨周应用；默认离线剧本，--live 才读取模型配置并发出请求。"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agentlab.course_runtime import replay_model, run_app  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["tool", "loop", "langchain", "graph", "evaluate"], default="tool"
    )
    parser.add_argument("--query", default="retry")
    parser.add_argument("--live", action="store_true", help="使用 .env 模型，可能产生费用")
    args = parser.parse_args()
    if (
        not args.live
        and args.mode in ["loop", "langchain", "graph"]
        and args.query != "retry"
        and args.query.strip()
    ):
        parser.error("回放仅演示 retry；其他非空查询请显式使用 --live")
    model: Any = replay_model()
    if args.live and args.mode not in ["tool", "evaluate"]:
        from dotenv import load_dotenv
        from langchain.chat_models import init_chat_model

        load_dotenv()
        model = init_chat_model(
            os.environ.get("DEFAULT_MODEL", "deepseek:deepseek-chat"),
            temperature=0,
            timeout=20,
            max_retries=0,
        )
        print("真实模型模式：请检查实际工具消息与最终产物。")
    else:
        print("离线模式：回放回复固定；工具执行和学习者逻辑仍会真实运行。")
    result = await run_app(args.mode, model, args.query)
    print(result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except NotImplementedError:
        print("前置练习尚未完成。查看 COURSE_STATE.json，按当前任务完成 TODO，不要让模型代写。")
        raise
