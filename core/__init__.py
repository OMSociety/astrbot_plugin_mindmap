"""astrbot_plugin_mindmap：中文思维导图与时间线渲染插件（Pillow 自研布局，零新增依赖）。"""

from .parser import (
    Node,
    OutlineDocument,
    OutlineError,
    OutlineTooLargeError,
    detect_layout,
    parse_outline,
)

__all__ = [
    "Node",
    "OutlineDocument",
    "OutlineError",
    "OutlineTooLargeError",
    "detect_layout",
    "parse_outline",
]
