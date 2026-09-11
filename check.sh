#!/usr/bin/env bash
# 提交前的本地 gate。规则见 AGENTS.md。
set -uo pipefail

cd "$(dirname "$0")"
failed=0

# --wip：跳过测试。本周练习没做完时测试必然是红的，但格式、lint 和结构
# 仍然要绿才能提交中间进度。周末收尾跑完整版。
wip=0
[ "${1:-}" = "--wip" ] && wip=1

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
# 每周单独一个 pytest 进程：不同周可能有同名的 exN 模块（如 ex1_messages.py），
# 同一进程里 Python 会复用第一次 import 的缓存，第二周就拿到了上一周的代码。
run_tests() {
    local status=0
    uv run pytest -q tests || status=1
    for week in weeks/w*/; do
        [ -d "$week" ] || continue
        uv run pytest -q "$week" || status=1
    done
    return "$status"
}

if [ "$wip" -eq 0 ]; then
    step "测试" run_tests
else
    printf '\n\033[33m▸ 测试（--wip 跳过）\033[0m\n'
fi
step "结构检查"  uv run python scripts/check_structure.py

if [ "$failed" -ne 0 ]; then
    printf '\n\033[31m检查未通过。修完再提交。\033[0m\n'
    exit 1
fi
printf '\n\033[32m全部通过。\033[0m\n'
