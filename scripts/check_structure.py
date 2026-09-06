#!/usr/bin/env python3
"""Repository structure gate.

Checks the mechanically verifiable rules in AGENTS.md so they cannot rot into
suggestions: week directory naming and minimum deliverables, retrospective
presence, dead relative markdown links, and secret hygiene.

Exits non-zero with a Chinese report listing every violation found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WEEK_DIR = re.compile(r"^w(\d{2})-[a-z0-9-]+$")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

# templates/ holds placeholder paths written relative to a week directory, not
# to templates/ itself, so its links resolve only after a template is copied.
LINK_SCAN_SKIP = {"templates", ".git", ".venv", "node_modules"}


def week_dirs() -> list[Path]:
    weeks = ROOT / "weeks"
    if not weeks.is_dir():
        return []
    return sorted(p for p in weeks.iterdir() if p.is_dir() and not p.name.startswith("."))


def check_weeks() -> list[str]:
    """Every week directory is named wNN-topic and carries README, code, and a test."""
    problems: list[str] = []
    for d in week_dirs():
        rel = d.relative_to(ROOT)
        m = WEEK_DIR.match(d.name)
        if not m:
            problems.append(f"{rel}: 目录名不符合 wNN-topic（两位数字 + 小写短横线主题）")
            continue

        if not (d / "README.md").is_file():
            problems.append(f"{rel}: 缺 README.md（用 templates/week-readme.md）")

        py = [p for p in d.rglob("*.py") if not p.name.startswith("test_")]
        if not py:
            problems.append(f"{rel}: 没有可运行的 .py 练习文件")

        if not list(d.rglob("test_*.py")):
            problems.append(f"{rel}: 没有 test_*.py，至少断言一件事")

        note = ROOT / "notes" / "weekly" / f"w{m.group(1)}.md"
        if not note.is_file():
            problems.append(
                f"{rel}: 缺复盘 notes/weekly/w{m.group(1)}.md"
                "（开周时先 cp templates/weekly-note.md 过去）"
            )
    return problems


def check_links() -> list[str]:
    """Relative markdown links resolve to real files."""
    problems: list[str] = []
    for md in ROOT.rglob("*.md"):
        # CLAUDE.md symlinks AGENTS.md; scanning both double-reports every link.
        if md.is_symlink():
            continue
        if any(part in LINK_SCAN_SKIP for part in md.relative_to(ROOT).parts):
            continue
        for target in MD_LINK.findall(md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            if not (md.parent / path).resolve().exists():
                problems.append(f"{md.relative_to(ROOT)}: 死链 -> {target}")
    return problems


def check_secrets() -> list[str]:
    """.env stays out of git and .env.example documents the required variables."""
    problems: list[str] = []
    gitignore = ROOT / ".gitignore"
    if not gitignore.is_file():
        problems.append(".gitignore 不存在")
    elif ".env" not in gitignore.read_text(encoding="utf-8").split():
        problems.append(".gitignore 未忽略 .env")

    if not (ROOT / ".env.example").is_file():
        problems.append("缺 .env.example（记录需要哪些变量，不含真值）")

    env = ROOT / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if value.strip() and "example" in key.lower():
                problems.append(".env 里出现了 example 键名，检查是否复制错文件")
    return problems


def main() -> int:
    checks = {
        "周目录": check_weeks,
        "文档链接": check_links,
        "密钥卫生": check_secrets,
    }
    failed = False
    for name, check in checks.items():
        problems = check()
        if problems:
            failed = True
            print(f"\n✗ {name}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"✓ {name}")

    if failed:
        print("\n结构检查未通过。规则见 AGENTS.md。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
