#!/usr/bin/env python3
"""Repository structure gate.

Checks the mechanically verifiable rules in AGENTS.md so they cannot rot into
suggestions: week directory naming and minimum deliverables, retrospective
presence, dead relative markdown links, and secret hygiene.

Exits non-zero with a Chinese report listing every violation found.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WEEK_DIR = re.compile(r"^w(\d{2})-[a-z0-9-]+$")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCED_CODE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
INLINE_CODE = re.compile(r"`[^`\n]*`")

# templates/ holds placeholder paths written relative to a week directory, not
# to templates/ itself, so its links resolve only after a template is copied.
# notes/qa/ holds verbatim Q&A logs; pasted code and tracebacks there look like
# markdown links (e.g. d['k'](x)) and the log values fidelity over link integrity.
LINK_SCAN_SKIP = {"templates", ".git", ".venv", "node_modules", "qa"}


def week_dirs() -> list[Path]:
    """Locate the week directories.

    Returns:
        Week directories sorted by name, empty when weeks/ does not exist yet.
    """
    weeks = ROOT / "weeks"
    if not weeks.is_dir():
        return []
    return sorted(p for p in weeks.iterdir() if p.is_dir() and not p.name.startswith("."))


def check_weeks() -> list[str]:
    """Every week directory is named wNN-topic and carries README, code, and a test.

    Returns:
        One line per violation; empty when every week directory is complete.
    """
    problems: list[str] = []
    for d in week_dirs():
        rel = d.relative_to(ROOT)
        m = WEEK_DIR.match(d.name)
        if not m:
            problems.append(f"{rel}: 目录名不符合 wNN-topic（两位数字 + 小写短横线主题）")
            continue

        if not (d / "README.md").is_file():
            problems.append(f"{rel}: 缺 README.md（用 templates/week-readme.md）")

        if not (d / "00_warmup.py").is_file():
            problems.append(f"{rel}: 缺 00_warmup.py（本周新语法的最小可运行例子）")

        py = [p for p in d.rglob("*.py") if not p.name.startswith("test_")]
        if not py:
            problems.append(f"{rel}: 没有可运行的 .py 练习文件")

        tests = list(d.rglob("test_*.py"))
        if not tests:
            problems.append(f"{rel}: 没有 test_*.py，至少断言一件事")
        else:
            # pytest 用文件名当模块名，两周同名会在收集阶段直接冲突。
            misnamed = [t.name for t in tests if not t.name.startswith(f"test_w{m.group(1)}")]
            if misnamed:
                problems.append(
                    f"{rel}: 测试文件名要以 test_w{m.group(1)} 开头，否则与其他周冲突：{misnamed}"
                )

        note = ROOT / "notes" / "weekly" / f"w{m.group(1)}.md"
        if not note.is_file():
            problems.append(
                f"{rel}: 缺复盘 notes/weekly/w{m.group(1)}.md"
                "（开周时先 cp templates/weekly-note.md 过去）"
            )
    return problems


def _links_in(text: str) -> list[str]:
    """Return markdown link targets, ignoring anything inside code.

    Args:
        text: Markdown source.

    Returns:
        Link targets in order of appearance.
    """
    text = FENCED_CODE.sub("", text)
    text = INLINE_CODE.sub("", text)
    return MD_LINK.findall(text)


def check_links() -> list[str]:
    """Relative markdown links resolve to real files.

    Returns:
        One line per dead link, naming the source file and the target.
    """
    problems: list[str] = []
    for md in ROOT.rglob("*.md"):
        # CLAUDE.md symlinks AGENTS.md; scanning both double-reports every link.
        if md.is_symlink():
            continue
        if any(part in LINK_SCAN_SKIP for part in md.relative_to(ROOT).parts):
            continue
        for target in _links_in(md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            if not (md.parent / path).resolve().exists():
                problems.append(f"{md.relative_to(ROOT)}: 死链 -> {target}")
    return problems


def _documented_functions(path: Path) -> list[str]:
    """Report functions whose docstring omits Args or Returns coverage.

    Args:
        path: Absolute path to the Python file to inspect. Reported locations are
            shortened to repository-relative form when the file lives under ROOT.

    Returns:
        One line per violation, prefixed with file, line, and function name.
    """
    problems: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path

    # Only module-level and class-level definitions; a nested helper is local detail.
    definitions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            definitions.append(node)
        elif isinstance(node, ast.ClassDef):
            definitions.extend(
                child
                for child in node.body
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
            )

    for fn in definitions:
        # A constructor documents its parameters on the class, per the class docstring.
        if fn.name.startswith("_"):
            continue
        if fn.name == "main":
            continue

        args = fn.args
        names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
        names = [n for n in names if n not in {"self", "cls"}]
        doc = ast.get_docstring(fn) or ""
        where = f"{shown}:{fn.lineno} {fn.name}"

        if not doc:
            problems.append(f"{where}: 没有 docstring")
            continue
        if names and "Args:" not in doc:
            problems.append(f"{where}: 有参数 {names} 但 docstring 缺 Args 段")

        returns_value = fn.returns is not None and not (
            isinstance(fn.returns, ast.Constant) and fn.returns.value is None
        )
        if returns_value and "Returns:" not in doc and "Yields:" not in doc:
            problems.append(f"{where}: 有返回值但 docstring 缺 Returns 段")

    return problems


def check_docstrings() -> list[str]:
    """Functions document their parameters and return values.

    A tool's docstring is the prompt the model reads, so parameter meaning is
    functional code here, not documentation polish. Test files are exempt:
    their names carry the description.

    Returns:
        One line per undocumented parameter list or return value.
    """
    problems: list[str] = []
    for directory in ("src", "weeks", "scripts"):
        root = ROOT / directory
        if not root.is_dir():
            continue
        for py in sorted(root.rglob("*.py")):
            if py.name.startswith("test_"):
                continue
            problems.extend(_documented_functions(py))
    return problems


def check_secrets() -> list[str]:
    """.env stays out of git and .env.example documents the required variables.

    Returns:
        One line per secret-hygiene violation.
    """
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
        "参数说明": check_docstrings,
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
