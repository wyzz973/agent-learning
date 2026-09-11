#!/usr/bin/env bash
# 教师维护的统一 gate；每周测试在独立进程运行。
set -uo pipefail
cd "$(dirname "$0")"
failed=0
wip=0
selected_week=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --wip) wip=1; shift ;;
        --week)
            if [ "$#" -lt 2 ]; then
                echo "--week 后需要周编号，例如 w04"; exit 2
            fi
            selected_week="$2"; shift 2 ;;
        *) echo "未知参数：$1；支持 --wip 和 --week w04"; exit 2 ;;
    esac
done
if [ -n "$selected_week" ] && [[ ! "$selected_week" =~ ^w[0-9][0-9]$ ]]; then
    echo "周编号格式为 w04"; exit 2
fi
if [ -n "$selected_week" ]; then
    found_week=0
    for candidate in weeks/"$selected_week"-*/; do
        [ -d "$candidate" ] && found_week=1
    done
    if [ "$found_week" -eq 0 ]; then
        echo "没有找到 $selected_week 的可运行教材"; exit 2
    fi
fi

step() {
    local name="$1"; shift
    printf '\n▸ %s\n' "$name"
    if "$@"; then
        printf '✓ %s\n' "$name"
    else
        printf '✗ %s\n' "$name"
        failed=1
    fi
}

# WIP 只跳过未完成的练习测试，教师基础设施仍须通过。
step "格式化" uv run ruff format .
step "lint" uv run ruff check --fix .
step "类型检查" uv run mypy
step "教师基础设施测试" uv run pytest tests -q
step "结构检查" uv run python scripts/check_structure.py
step "课程与交接检查" uv run python scripts/check_course.py

run_week_tests() {
    local status=0
    local matched=0
    for week_path in weeks/w*/; do
        [ -d "$week_path" ] || continue
        if [ -n "$selected_week" ] && [[ "$week_path" != weeks/"$selected_week"-*/ ]]; then
            continue
        fi
        matched=1
        uv run pytest -q "$week_path" || status=1
    done
    if [ "$matched" -eq 0 ]; then
        echo "没有找到对应周的教材"; return 2
    fi
    return "$status"
}
if [ "$wip" -eq 0 ]; then
    step "学习者练习测试" run_week_tests
else
    echo "练习测试已按 --wip 跳过；这不代表学习者已完成。"
fi
if [ "$failed" -ne 0 ]; then
    echo "检查未通过。"; exit 1
fi
echo "本次检查全部通过。"
