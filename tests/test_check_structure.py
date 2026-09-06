"""The structure gate is only useful if its own matching is correct."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from check_structure import MD_LINK, WEEK_DIR  # noqa: E402


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
