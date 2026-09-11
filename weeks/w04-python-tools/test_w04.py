"""行为规格：学习者尚未完成的函数必须明确失败。"""

from copy import deepcopy

import pytest
from ex1_records import collect_paths, find_matches, make_hits
from ex2_search_tool import error_result, search_repository, success_result


@pytest.fixture
def files() -> list[dict[str, str]]:
    return [
        {"path": "src/retry.py", "content": "Retry failed requests."},
        {"path": "README.md", "content": "Use retry for network errors."},
        {"path": "tests/test_chat.py", "content": "Check message history."},
    ]


def test_demo_collect_paths(files: list[dict[str, str]]) -> None:
    assert collect_paths(files) == ["src/retry.py", "README.md", "tests/test_chat.py"]


def test_demo_collect_paths_empty() -> None:
    assert collect_paths([]) == []


def test_demo_error_result() -> None:
    assert error_result("keyword must not be blank") == {
        "ok": False,
        "items": [],
        "count": 0,
        "error": "keyword must not be blank",
    }


def test_find_matches_path_and_content(files: list[dict[str, str]]) -> None:
    assert find_matches(files, "retry") == files[:2]
    assert find_matches(files, "test_chat") == [files[2]]
    assert find_matches(files, "py Retry") == []


def test_find_matches_normalizes_keyword(files: list[dict[str, str]]) -> None:
    assert find_matches(files, "  RETRY  ") == files[:2]


def test_find_matches_empty_and_missing(files: list[dict[str, str]]) -> None:
    assert find_matches(files, "missing") == []
    assert find_matches([], "retry") == []
    assert find_matches(files, "   ") == []


def test_find_matches_keeps_input(files: list[dict[str, str]]) -> None:
    before = deepcopy(files)
    find_matches(files, "retry")
    assert files == before


def test_make_hits_projects_fields(files: list[dict[str, str]]) -> None:
    assert make_hits(files) == [
        {"path": "src/retry.py"},
        {"path": "README.md"},
        {"path": "tests/test_chat.py"},
    ]


def test_make_hits_empty() -> None:
    assert make_hits([]) == []


def test_make_hits_keeps_input(files: list[dict[str, str]]) -> None:
    before = deepcopy(files)
    make_hits(files)
    assert files == before


def test_success_result(files: list[dict[str, str]]) -> None:
    assert success_result(files[:1]) == {
        "ok": True,
        "items": [{"path": "src/retry.py"}],
        "count": 1,
        "error": None,
    }


def test_success_result_empty() -> None:
    assert success_result([]) == {"ok": True, "items": [], "count": 0, "error": None}


def test_search_repository_found(files: list[dict[str, str]]) -> None:
    assert search_repository(files, "  RETRY ") == {
        "ok": True,
        "items": [{"path": "src/retry.py"}, {"path": "README.md"}],
        "count": 2,
        "error": None,
    }


def test_search_repository_no_match_is_success(files: list[dict[str, str]]) -> None:
    assert search_repository(files, "missing") == {
        "ok": True,
        "items": [],
        "count": 0,
        "error": None,
    }
    assert search_repository([], "retry") == {"ok": True, "items": [], "count": 0, "error": None}


def test_search_repository_blank_is_error(files: list[dict[str, str]]) -> None:
    for keyword in ["", " ", "\t\n"]:
        assert search_repository(files, keyword) == {
            "ok": False,
            "items": [],
            "count": 0,
            "error": "keyword must not be blank",
        }


def test_search_repository_keeps_input(files: list[dict[str, str]]) -> None:
    before = deepcopy(files)
    search_repository(files, "retry")
    assert files == before
