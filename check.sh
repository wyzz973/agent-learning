#!/usr/bin/env bash
# 提交前的本地 gate。规则见 AGENTS.md。
set -uo pipefail

cd "$(dirname "$0")"
failed=0

step() {
    local name="$1"; shift
    printf '\n\033[1m▸ %s\033[0m\n' "$name"
    if "$@"; then
        printf '\033[32m✓ %s\033[0m\n' "$name"
    else
        printf '\033[31m✗ %s\033[0m\n' "$name"
        failed=1
    fi
}

step "格式化"   uv run ruff format .
step "lint"     uv run ruff check --fix .
step "类型检查"  uv run mypy
step "测试"     uv run pytest -q
step "结构检查"  uv run python scripts/check_structure.py

if [ "$failed" -ne 0 ]; then
    printf '\n\033[31m检查未通过。修完再提交。\033[0m\n'
    exit 1
fi
printf '\n\033[32m全部通过。\033[0m\n'
