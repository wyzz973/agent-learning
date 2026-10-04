"""同步教师接线设施；不生成、执行或重写学生核心定义。"""

import ast
import copy
import io
import textwrap
import tokenize
from typing import Any


def with_export_preview(source: str) -> str:
    """为已有导出调用加入可见比较与指纹，不改变本人定义。

    Args:
        source: 教师提供的setup/demo或exercise-test接线格。
    Returns:
        含preview_export、差异显示和明确版本参数的代码；已接好时保持原样。
    Raises:
        SyntaxError: 原格代码不合法。
        ValueError: 导出调用嵌在复杂控制语句中，需教师原位审校。
    """
    tree = ast.parse(source)
    pending = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == "export_definitions"
        and not any(keyword.arg == "expected_previous_sha" for keyword in node.keywords)
    ]
    if not pending:
        return source
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    changes: list[tuple[int, int, str]] = []
    for index, call in enumerate(pending):
        statement = next(item for item in tree.body if call in ast.walk(item))
        if not isinstance(statement, (ast.Assign, ast.Expr)):
            raise ValueError("导出调用需要独立接线格，不能隐藏在本人控制流中")
        name = f"export_preview_{index + 1}"
        preview = copy.deepcopy(call)
        preview.func = ast.Name(id="preview_export", ctx=ast.Load())
        introduction = (
            f"{name} = {ast.unparse(preview)}\n"
            f"print('导出比较：', {name}['status'])\n"
            f"print({name}['diff'])\n"
        )
        insertion = offsets[statement.lineno - 1]
        changes.append((insertion, insertion, introduction))
        call_copy = copy.deepcopy(call)
        call_copy.keywords.append(ast.keyword(
            arg="expected_previous_sha",
            value=ast.Subscript(
                value=ast.Name(id=name, ctx=ast.Load()),
                slice=ast.Constant(value="current_sha"), ctx=ast.Load(),
            ),
        ))
        # AST列号按UTF-8字节计数，切片前先转成字符位置。
        start_col = len(lines[call.lineno - 1].encode()[:call.col_offset].decode())
        end_line = (call.end_lineno or call.lineno) - 1
        end_col = len(lines[end_line].encode()[:call.end_col_offset].decode())
        changes.append((
            offsets[call.lineno - 1] + start_col, offsets[end_line] + end_col,
            ast.unparse(call_copy),
        ))
    for start, end, replacement in sorted(changes, reverse=True):
        source = source[:start] + replacement + source[end:]
    return "from instructor.learner_exports import preview_export\n" + source


def current_source_quote(quote: str, source: str) -> str:
    """把已审校的引用定位到当前等价源码，拒绝找不到的片段。

    Args:
        quote: 已审校片段；source: 当前教师格。只忽略空白与字符串引号写法。
    Returns:
        当前源码中的实际片段，包含新的换行和缩进。
    Raises:
        ValueError: 片段已改变机制或无法在当前源码中定位，需要教师复核。
    """
    if quote in source:
        return quote
    source_tree = ast.parse(source)
    try:
        wanted_body = ast.parse(textwrap.dedent(quote)).body
    except SyntaxError:
        wanted_body = []
    if wanted_body:
        signatures = [ast.dump(node, include_attributes=False) for node in wanted_body]
        for parent in ast.walk(source_tree):
            for _, field in ast.iter_fields(parent):
                if not isinstance(field, list) or not all(isinstance(n, ast.stmt) for n in field):
                    continue
                for index in range(len(field) - len(wanted_body) + 1):
                    nodes = field[index:index + len(wanted_body)]
                    if [ast.dump(node, include_attributes=False) for node in nodes] == signatures:
                        first, last = nodes[0], nodes[-1]
                        fragment = ast.get_source_segment(source, first)
                        if len(nodes) == 1 and fragment is not None:
                            return fragment
                        lines = source.splitlines(keepends=True)
                        return "".join(lines[first.lineno - 1:last.end_lineno]).rstrip()
    # 显式展示的可信worker字符串也属于教师源码，定位其解码后的正文。
    for node in ast.walk(source_tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and quote in node.value:
            return quote
    ignored = {
        tokenize.ENCODING, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
        tokenize.DEDENT, tokenize.ENDMARKER, tokenize.COMMENT,
    }

    def tokens(text: str) -> list[tuple[Any, tokenize.TokenInfo]]:
        result = []
        iterator = tokenize.generate_tokens(io.StringIO(text).readline)
        try:
            for token in iterator:
                if token.type in ignored:
                    continue
                value: Any = token.string
                if token.type == tokenize.STRING:
                    try:
                        value = repr(ast.literal_eval(token.string))
                    except (ValueError, SyntaxError):
                        pass
                result.append(((token.type, value), token))
        except (tokenize.TokenError, IndentationError):
            pass  # 不完整的已审校片段仍可按取得的token定位，不执行它。
        return result

    wanted, available = tokens(quote), tokens(source)
    keys = [item[0] for item in wanted]
    if not keys:
        raise ValueError("源码引用没有可定位内容")
    for index in range(len(available) - len(keys) + 1):
        if [item[0] for item in available[index:index + len(keys)]] != keys:
            continue
        start = available[index][1].start
        end = available[index + len(keys) - 1][1].end
        lines = source.splitlines(keepends=True)
        if start[0] == end[0]:
            return lines[start[0] - 1][start[1]:end[1]]
        return (
            lines[start[0] - 1][start[1]:]
            + "".join(lines[start[0]:end[0] - 1]) + lines[end[0] - 1][:end[1]]
        )
    raise ValueError("已审校引用与当前教师代码不再等价，需要原位复核")
