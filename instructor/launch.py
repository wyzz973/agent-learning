"""从唯一进度文件打开当前 Notebook，使用项目自己的 Jupyter 内核。"""

import argparse
import json
import subprocess
import sys

from instructor.check import ROOT, load_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true", help="只显示当前 Notebook，不启动服务")
    parser.add_argument("--no-browser", action="store_true", help="仅启动服务，供远程使用或验收")
    parser.add_argument("--port", type=int, help="指定本机端口，通常无需填写")
    args = parser.parse_args()
    state = json.loads((ROOT / "instructor/state.json").read_text(encoding="utf-8"))
    task = next(row for row in load_catalog()["tasks"] if row["id"] == state["active_task"])
    if task.get("status") != "ready" or not task.get("notebook"):
        parser.error("当前任务完整教材尚未就绪，请导师先编写并验证；不打开未完成教材代替。")
    path = ROOT / task["notebook"]
    print(f"{task['id']} · {task['title']}\n{path}", flush=True)
    if args.show:
        return 0
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ipykernel",
            "install",
            "--sys-prefix",
            "--name",
            "agentlearning",
            "--display-name",
            "Agent Learning (.venv)",
        ],
        check=True,
    )
    command = [
        sys.executable,
        "-m",
        "jupyterlab",
        str(path),
        "--ServerApp.root_dir=" + str(ROOT),
        "--ip=127.0.0.1",
    ]
    if args.no_browser:
        command.append("--no-browser")
    if args.port is not None:
        if not 1024 <= args.port <= 65535:
            parser.error("端口范围为 1024～65535")
        command.extend([f"--port={args.port}", "--ServerApp.port_retries=0"])
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
