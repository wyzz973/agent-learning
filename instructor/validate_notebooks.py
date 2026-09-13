"""真实执行 setup/demo；练习保留原样，结果只证明教师材料可运行。"""

import argparse
import copy
import json
import time
from typing import Any

import nbformat
from nbclient import NotebookClient

from instructor.check import ROOT, load_catalog


def demo_copy(notebook: Any) -> tuple[Any, list[str]]:
    """建立仅执行教师格的副本，不修改学习者源文件或补答案。

    Args:
        notebook: 已解析的完整 Notebook。
    Returns:
        执行副本与跳过的 cell ID。
    Raises:
        无：只复制数据。
    """
    result = copy.deepcopy(notebook)
    skipped = []
    for cell in result.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
        if set(cell.metadata.get("tags", [])) & {"exercise", "exercise-test"}:
            skipped.append(cell.get("id", "unknown"))
            cell.metadata["tags"] = list(cell.metadata.get("tags", [])) + ["skip-execution"]
    return result, skipped


def validate_one(task: dict[str, Any], refresh_demo_outputs: bool = False) -> dict[str, Any]:
    """为一份 Notebook 启动全新内核，使用已配置真实模型验证教师内容。

    Args:
        task: 目录中的 task 对象。
        refresh_demo_outputs: 是否把实际教师输出写回源 Notebook，练习输出不动。
    Returns:
        成功/失败、耗时、跳过格、执行格数及产物位置。
    Raises:
        OSError: Notebook 或报告无法读取/写入。
        ValueError: 任务没有可执行的教师示范。
    """
    if not task.get("notebook") or task.get("status") == "planned":
        raise ValueError("任务只有演进设计，尚无 Notebook；不能把空运行登记为通过。")
    path = ROOT / task["notebook"]
    source = nbformat.read(path, as_version=4)
    executed, skipped = demo_copy(source)
    started = time.monotonic()
    error: str | None = None
    try:
        NotebookClient(
            executed,
            timeout=150,
            kernel_name="agentlearning",
            resources={"metadata": {"path": str(ROOT)}},
        ).execute()
    except Exception as exc:
        # 完整异常可能包含请求正文；只记录类型，细节保留在执行副本的出错格。
        error = type(exc).__name__
    directory = ROOT / "outputs/validation" / task["id"]
    directory.mkdir(parents=True, exist_ok=True)
    nbformat.write(executed, directory / "executed.ipynb")
    count = sum(c.cell_type == "code" and c.execution_count is not None for c in executed.cells)
    if not error and refresh_demo_outputs:
        for original, actual in zip(source.cells, executed.cells, strict=True):
            if original.cell_type == "code" and not set(original.metadata.get("tags", [])) & {
                "exercise",
                "exercise-test",
            }:
                original.outputs = actual.outputs
                original.execution_count = actual.execution_count
        nbformat.write(source, path)
    result = {
        "task": task["id"],
        "notebook": task["notebook"],
        "passed": error is None,
        "scope": "仅 setup/demo；不代表本人完成",
        "executed_cells": count,
        "skipped_exercise_cells": skipped,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "error": error,
        "executed_notebook": str((directory / "executed.ipynb").relative_to(ROOT)),
    }
    (directory / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", action="append", help="只执行指定 task，可重复")
    parser.add_argument("--refresh-demo-outputs", action="store_true")
    args = parser.parse_args()
    catalog_tasks = load_catalog()["tasks"]
    if args.task:
        requested = set(args.task)
        known = {t["id"] for t in catalog_tasks}
        if requested - known:
            parser.error("未知 task：" + ", ".join(sorted(requested - known)))
        unavailable = [t["id"] for t in catalog_tasks if t["id"] in requested and not t["notebook"]]
        if unavailable:
            parser.error("这些任务尚未编写 Notebook：" + ", ".join(unavailable))
    tasks = [t for t in catalog_tasks if t["notebook"] and (not args.task or t["id"] in args.task)]
    if not tasks:
        parser.error("没有匹配的 task")
    results = []
    print("只验证本关教师示范；不执行规划任务，也不登记玩家完成。", flush=True)
    for task in tasks:
        print("开始教师真实验证：", task["id"], flush=True)
        result = validate_one(task, args.refresh_demo_outputs)
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
