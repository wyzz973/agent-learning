"""验证评分尺子的边界，避免重复、缺测或裁判错误制造好成绩。"""

import math
from pathlib import Path

import pytest

from instructor.evaluation_facilities import (
    load_retrieval_cases,
    paired_bootstrap_delta,
    retrieval_metrics,
    summarize_judge_trials,
    summarize_retrieval,
    wilson_interval,
)


def test_rank_quality_and_empty_gold_are_separate() -> None:
    metrics = retrieval_metrics(["wrong", "a", "b"], {"a", "b"}, 2)
    assert metrics["recall_at_k"] == 0.5
    assert metrics["precision_at_k"] == 0.5 and metrics["mrr_at_k"] == 0.5
    assert 0 < metrics["ndcg_at_k"] < 1
    unknown = retrieval_metrics([], set(), 2)
    assert unknown["recall_at_k"] is None and unknown["mrr_at_k"] is None
    assert unknown["no_answer_clean"] is True
    with pytest.raises(ValueError, match="重复"):
        retrieval_metrics(["a", "a"], {"a"}, 2)


def test_failure_and_unmeasured_values_do_not_improve_macro_average() -> None:
    summary = summarize_retrieval([
        {"group": "zh", "status": "measured", "metrics": {"recall_at_k": 0.5}},
        {"group": "zh", "status": "failed", "metrics": {}},
    ])["zh"]
    assert summary["failed"] == 1
    assert summary["metrics"]["recall_at_k"] == {
        "mean": 0.5, "measured": 1, "unmeasured": 1,
    }


def test_calibration_flags_consistently_wrong_as_well_as_order_instability() -> None:
    wrong = [
        {"case_id": "seat", "order": ["good", "bad"], "repeat": 0,
         "winner": "bad", "gold": "good", "error": None},
        {"case_id": "seat", "order": ["bad", "good"], "repeat": 0,
         "winner": "bad", "gold": "good", "error": None},
    ]
    report = summarize_judge_trials(wrong)
    assert report["gold_agreement"] == 0 and report["needs_review"]
    assert report["unstable_cases"] == [] and report["wrong_runs"] == 2
    wrong[1]["winner"] = "good"
    assert summarize_judge_trials(wrong)["unstable_cases"] == ["seat"]
    wrong[1]["winner"] = None
    wrong[1]["error"] = "TimeoutError"
    assert summarize_judge_trials(wrong)["errors"] == 1
    with pytest.raises(ValueError, match="重复"):
        summarize_judge_trials([wrong[0], wrong[0]])


def test_uncertainty_rejects_unpaired_or_missing_measurements() -> None:
    assert wilson_interval(0, 0) is None
    interval = wilson_interval(1, 1)
    assert interval is not None and interval[0] < 0.3 and interval[1] == 1
    measured = paired_bootstrap_delta([0, 1, 0.5], [1, 1, 0.5])
    assert measured["mean_delta"] == pytest.approx(1 / 3)
    assert measured == paired_bootstrap_delta([0, 1, 0.5], [1, 1, 0.5])
    with pytest.raises(ValueError, match="配对"):
        paired_bootstrap_delta([0], [1, 1])
    with pytest.raises(ValueError, match="缺失"):
        paired_bootstrap_delta([math.nan], [1])


def test_world_reference_conditions_are_separate_from_runtime_requests() -> None:
    root = Path(__file__).resolve().parents[2]
    data = load_retrieval_cases(root)
    assert {case["group"] for case in data["cases"]} == {"en", "zh", "zh_to_en", "no_answer"}
    assert {case["split"] for case in data["cases"]} == {"development", "holdout"}
    assert all("expected" not in case["request"] for case in data["cases"])
    assert len(data["corpus"]) == 16 and len(data["cases"]) == 20
