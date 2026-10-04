"""公开的评估尺子与数据读取设施，不实现本人检索或研究控制循环。"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any


def load_retrieval_cases(root: Path) -> dict[str, Any]:
    """读取雾岛中英文资料与评估卡，参考条件仅供评分。

    Args:
        root: 本课程根目录。
    Returns:
        corpus与cases；调用方只把case.request交给检索器。
    Raises:
        ValueError: 编号重复、原文为空、参考编号不在当前语料。
        OSError: 数据文件无法读取。
    """
    data: dict[str, Any] = json.loads(
        (root / "world/acceptance/retrieval-cases.json").read_text(encoding="utf-8")
    )
    docs = data["corpus"]
    ids = {doc["id"] for doc in docs}
    case_ids = {case["id"] for case in data["cases"]}
    if len(ids) != len(docs) or len(case_ids) != len(data["cases"]):
        raise ValueError("语料或评估卡编号重复")
    for doc in docs:
        if not doc["text"].strip() or doc["language"] not in {"en", "zh"}:
            raise ValueError("资料正文或语言字段不合法")
    for case in data["cases"]:
        if not set(case["expected"]["relevant_ids"]) <= ids:
            raise ValueError("参考条件指向不存在的原文")
        if not case["request"]["query"].strip():
            raise ValueError("查询为空")
    return data


def retrieval_metrics(ranked_ids: list[str], relevant_ids: set[str], k: int) -> dict[str, Any]:
    """计算固定k的检索指标，无答案卡与正例分开。

    Args:
        ranked_ids: 不重复的实际结果；relevant_ids: 人工标注的相关身份；k: 正整数。
    Returns:
        Recall@k、固定分母Precision@k、MRR@k、二元nDCG@k；无答案的recall等为None。
    Raises:
        ValueError: k、身份或重复结果不合法。
    """
    if type(k) is not int or k < 1 or not isinstance(ranked_ids, list):
        raise ValueError("k必须为正整数，排名必须是身份列表")
    if any(not isinstance(item, str) or not item for item in [*ranked_ids, *relevant_ids]):
        raise ValueError("检索身份必须为非空字符串")
    if len(ranked_ids) != len(set(ranked_ids)):
        raise ValueError("k必须为正整数，实际排名不能重复计数")
    selected = ranked_ids[:k]
    hits = [index + 1 for index, item in enumerate(selected) if item in relevant_ids]
    dcg = sum(1 / math.log2(rank + 1) for rank in hits)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant_ids)) + 1))
    return {
        "recall_at_k": len(hits) / len(relevant_ids) if relevant_ids else None,
        "precision_at_k": len(hits) / k,
        "mrr_at_k": 1 / hits[0] if hits else 0.0 if relevant_ids else None,
        "ndcg_at_k": dcg / ideal if ideal else None,
        "no_answer_clean": not selected if not relevant_ids else None,
        "k": k,
    }


def summarize_retrieval(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """按语言和查询类型汇总实际测量，未知不填零。

    Args:
        rows: 含group/status/metrics的真实评估行，不接收教师替代结果。
    Returns:
        各组指标的已测平均、测量数、缺测数与失败数。
    Raises:
        ValueError: 空记录或缺少分组、状态字段。
    """
    if not rows or any("group" not in row or "status" not in row for row in rows):
        raise ValueError("评估需要真实行与分组/状态")
    result: dict[str, Any] = {}
    for group in sorted({row["group"] for row in rows}):
        members = [row for row in rows if row["group"] == group]
        metrics = {}
        for key in ("recall_at_k", "precision_at_k", "mrr_at_k", "ndcg_at_k", "no_answer_clean"):
            values = [row.get("metrics", {}).get(key) for row in members]
            measured = [float(value) for value in values if value is not None]
            metrics[key] = {
                "mean": sum(measured) / len(measured) if measured else None,
                "measured": len(measured), "unmeasured": len(members) - len(measured),
            }
        result[group] = {
            "cases": len(members), "failed": sum(row["status"] == "failed" for row in members),
            "metrics": metrics,
        }
    return result


def wilson_interval(successes: int, total: int) -> list[float] | None:
    """给独立二元试验估计95% Wilson区间；无测量返回未知。

    Args:
        successes: 通过数；total: 独立试验数，不能将同一任务相关重复冒称独立样本。
    Returns:
        下界/上界；total为0时None。
    Raises:
        ValueError: 计数不是整数或超出范围。
    """
    if type(successes) is not int or type(total) is not int or not 0 <= successes <= total:
        raise ValueError("成功数与总数不合法")
    if total == 0:
        return None
    z, rate = 1.96, successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    width = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - width), min(1.0, center + width)]


def paired_bootstrap_delta(
    baseline: list[float], candidate: list[float], seed: int = 41, repeats: int = 500,
) -> dict[str, Any]:
    """按配对任务重采样改进差值，不混用两组不同任务。

    Args:
        baseline/candidate: 已按同一case身份配对的数值；seed: 固定种子；repeats: 100至5000。
    Returns:
        当前配对均值差、2.5/97.5百分位区间与样本数；小样本不支持普遍结论。
    Raises:
        ValueError: 数量不等、空列表、非有限值或重采样范围不合法。
    """
    if (
        len(baseline) != len(candidate) or not baseline or type(repeats) is not int
        or not 100 <= repeats <= 5000
    ):
        raise ValueError("配对样本或重采样次数不合法")
    if any(not math.isfinite(value) for value in [*baseline, *candidate]):
        raise ValueError("缺失或非有限测量不能当零")
    deltas = [right - left for left, right in zip(baseline, candidate, strict=True)]
    rng = random.Random(seed)
    samples = sorted(
        sum(rng.choices(deltas, k=len(deltas))) / len(deltas) for _ in range(repeats)
    )
    return {
        "mean_delta": sum(deltas) / len(deltas),
        "interval": [samples[int(repeats * 0.025)], samples[int(repeats * 0.975)]],
        "cases": len(deltas), "seed": seed, "repeats": repeats,
        "scope": "当前配对任务的重采样；未覆盖输入不能据此保证提升。",
    }


def summarize_judge_trials(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """按答案身份审计真实裁判回执与人工标签。

    Args:
        rows: case_id/order/repeat/winner/gold/error字段；winner为答案身份而非A/B位置。
    Returns:
        已测一致率、失败数、顺序或重复不稳定案例，以及未知字段。
    Raises:
        ValueError: 空记录、重复运行身份或缺少必需字段。
    """
    required = {"case_id", "order", "repeat", "winner", "gold", "error"}
    identities = [
        (row.get("case_id"), tuple(row.get("order", [])), row.get("repeat")) for row in rows
    ]
    if not rows or len(identities) != len(set(identities)):
        raise ValueError("裁判实验为空或同一运行被重复计数")
    if any(not required <= row.keys() for row in rows):
        raise ValueError("裁判回执缺身份、人工标签或错误字段")
    if any(
        row["winner"] not in [None, "tie", *row["order"]]
        or row["gold"] not in ["tie", *row["order"]] for row in rows
    ):
        raise ValueError("裁判结果或人工标签不属于当前候选身份")
    measured = [row for row in rows if row["error"] is None and row["winner"] is not None]
    correct = sum(row["winner"] == row["gold"] for row in measured)
    unstable = [case for case in sorted({row["case_id"] for row in rows}) if len({
        row["winner"] for row in measured if row["case_id"] == case
    }) > 1]
    return {
        "runs": len(rows), "measured": len(measured), "errors": len(rows) - len(measured),
        "wrong_runs": len(measured) - correct,
        "gold_agreement": correct / len(measured) if measured else None,
        "unstable_cases": unstable,
        "needs_review": bool(unstable) or correct != len(measured) or len(measured) != len(rows),
        "independent_population_interval": None,
        "scope": "重复运行相关且样本小，人工一致率不是总体正确率或独立区间。",
    }
