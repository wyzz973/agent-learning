"""在Notebook按需要展开公开教师设施，保持原位可读。"""

import html
import inspect
from typing import Any, cast


def show_teacher_source(function: Any) -> None:
    """折叠展示实际设施源码；不提供本人函数或模型草稿。

    Args:
        function: 当前实际导入的教师函数或设施类。
    Returns:
        无；展示完整源码，默认折叠。
    Raises:
        OSError/TypeError: 源码无法定位时明确失败。
    """
    from IPython.display import HTML, display

    source = inspect.getsource(function)
    label = html.escape(getattr(function, "__name__", "公开设施"))
    content = (
        '<details class="fog-teacher-source"><summary>展开公开设施源码：' + label
        + '</summary><pre style="max-height:38rem;overflow:auto;line-height:1.55;'
        'padding:1rem;border:1px solid #d8dfd5;white-space:pre;">'
        + html.escape(source) + "</pre></details>"
    )
    cast(Any, display)(cast(Any, HTML)(content))
