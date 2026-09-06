"""The structure gate is only useful if its own matching is correct."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from check_structure import MD_LINK, WEEK_DIR, _documented_functions  # noqa: E402


def test_week_dir_accepts_the_documented_naming() -> None:
    assert WEEK_DIR.match("w01-python-foundations")
    assert WEEK_DIR.match("w12-capstone")


def test_week_dir_rejects_naming_that_breaks_the_retrospective_lookup() -> None:
    # The two-digit group is what maps a week directory to notes/weekly/wNN.md.
    assert not WEEK_DIR.match("w1-bare-agent")
    assert not WEEK_DIR.match("week01-bare-agent")
    assert not WEEK_DIR.match("w01_bare_agent")
    assert not WEEK_DIR.match("w01-Bare-Agent")


def test_md_link_extracts_targets_and_ignores_bare_urls() -> None:
    text = (
        "见 [路线](LEARNING_PATH.md) 和 [第二周](weeks/w02-bare-agent/README.md#运行)，"
        "裸链 https://x.dev 不算"
    )
    assert MD_LINK.findall(text) == [
        "LEARNING_PATH.md",
        "weeks/w02-bare-agent/README.md#运行",
    ]


class TestDocstringCoverage:
    """A tool's docstring is the prompt the model reads, so the gate enforces it."""

    def _check(self, tmp_path, source: str) -> list[str]:
        target = tmp_path / "sample.py"
        target.write_text(source, encoding="utf-8")
        return _documented_functions(target)

    def test_parameters_without_an_args_section_are_reported(self, tmp_path) -> None:
        problems = self._check(tmp_path, 'def f(a: int) -> None:\n    """Do a thing."""\n')
        assert len(problems) == 1
        assert "缺 Args 段" in problems[0]

    def test_documented_parameters_and_return_pass(self, tmp_path) -> None:
        source = (
            "def f(a: int) -> int:\n"
            '    """Do a thing.\n\n    Args:\n        a: The input.\n\n'
            "    Returns:\n        The output.\n"
            '    """\n'
        )
        assert self._check(tmp_path, source) == []

    def test_return_value_without_a_returns_section_is_reported(self, tmp_path) -> None:
        source = 'def f() -> int:\n    """Do a thing."""\n'
        assert "缺 Returns 段" in self._check(tmp_path, source)[0]

    def test_none_returning_function_needs_no_returns_section(self, tmp_path) -> None:
        assert self._check(tmp_path, 'def f() -> None:\n    """Do a thing."""\n') == []

    def test_private_helpers_and_constructors_are_exempt(self, tmp_path) -> None:
        # A constructor documents its parameters on the class, per dsh's convention.
        source = (
            'def _helper(a: int) -> int:\n    """Private."""\n\n\n'
            "class C:\n"
            '    """A class."""\n\n'
            "    def __init__(self, a: int) -> None:\n        pass\n"
        )
        assert self._check(tmp_path, source) == []

    def test_nested_functions_are_local_detail(self, tmp_path) -> None:
        source = (
            "def outer() -> None:\n"
            '    """Outer."""\n\n'
            "    def inner(a: int) -> int:\n        return a\n"
        )
        assert self._check(tmp_path, source) == []
