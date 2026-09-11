"""来源检查与评分规则的行为规格。"""

from ex1_eval import is_known_path, score_cases, unknown_paths


def test_demo_known_path() -> None:
    assert is_known_path("a.py", ["a.py"])
    assert not is_known_path("b.py", ["a.py"])


def test_unknown_paths() -> None:
    assert unknown_paths(["a.py", "fake.py", "other.py"], ["a.py"]) == ["fake.py", "other.py"]
    assert unknown_paths([], ["a.py"]) == []


def test_score_cases() -> None:
    assert score_cases([True, False, True]) == {"passed": 2, "total": 3, "rate": 2 / 3}
    assert score_cases([False]) == {"passed": 0, "total": 1, "rate": 0.0}


def test_score_cases_empty_is_unknown() -> None:
    assert score_cases([]) == {"passed": 0, "total": 0, "rate": None}
