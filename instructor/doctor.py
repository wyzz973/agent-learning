"""检查课程环境，按明确选项准备真实embedding缓存；不运行学生代码。"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from instructor.check import ROOT


def ensure_embedding(root: Path = ROOT) -> dict[str, Any]:
    """取得真实公开模型缓存，不生成替代向量。

    Args:
        root: 仓库目录。
    Returns:
        实际模型名称、维度和缓存相对路径。
    Raises:
        下载、缓存或推理错误原样保留，便于导师处理。
    """
    from fastembed import TextEmbedding

    cache = root / "outputs/model-cache"
    engine = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=str(cache), threads=1)
    vector = next(iter(engine.embed(["library source evidence"])))
    if len(vector) != 384:
        raise ValueError("实际embedding维度与本课契约不同")
    return {
        "model": "BAAI/bge-small-en-v1.5",
        "dimensions": len(vector),
        "cache": "outputs/model-cache",
        "scope": "真实本地模型，不证明检索质量",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-embedding", action="store_true")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "python_ready": sys.version_info >= (3, 12),
        "config_file_exists": (ROOT / ".env").is_file(),
        "learner_entry": "README当前Notebook",
        "credential_values": "不输出",
    }
    try:
        docker = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        result["docker_ready"] = docker.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        result["docker_ready"] = False
    result["docker_note"] = "仅M08代码执行需要；打开Docker后再运行本关"
    if args.prepare_embedding:
        result["embedding"] = ensure_embedding()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(not result["python_ready"] or not result["config_file_exists"])


if __name__ == "__main__":
    raise SystemExit(main())
