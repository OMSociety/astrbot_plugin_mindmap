"""大纲解析：Markdown 标题 / 列表缩进两种风格，时间线标签切分，布局自动检测，硬上限检查。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_DEPTH = 8
DEFAULT_MAX_NODES = 200
DEFAULT_MAX_NODE_CHARS = 200

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.+?)\s*$")
_LABEL_RE = re.compile(
    r"^\s*([^\n:：]{1,24}?)\s*[:：]\s*(.+)$",
    re.S,
)
_DATE_PATTERNS = [
    re.compile(r"\d{4}\s*[-–~至]\s*\d{4}"),
    re.compile(r"\d{4}\s*年"),
    re.compile(r"公元前\d+"),
    re.compile(r"\d{1,2}\s*世纪"),
    re.compile(r"^\d{3,4}\s*[-/]"),
    re.compile(r"^\d{3,4}\s*[:：]"),
    re.compile(r"^[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}"),
    re.compile(r"^\d{4}\s*$"),
]


class OutlineError(ValueError):
    """大纲解析失败，message 面向 LLM/用户，含行号定位。"""


class OutlineTooLargeError(OutlineError):
    """超过硬上限。属性：nodes / max_node_chars。"""

    def __init__(self, nodes: int, max_node_chars: int):
        super().__init__(f"nodes={nodes} max_node_chars={max_node_chars}")
        self.nodes = nodes
        self.max_node_chars = max_node_chars


@dataclass
class Node:
    text: str
    depth: int
    line_no: int
    children: list["Node"] = field(default_factory=list)
    label: str = ""

    @property
    def is_leaf(self) -> bool:
        return not self.children


@dataclass
class OutlineDocument:
    root: Node
    total_nodes: int
    max_depth: int

    def leaves(self) -> list[Node]:
        out: list[Node] = []

        def walk(n: Node) -> None:
            if n.is_leaf:
                out.append(n)
            for c in n.children:
                walk(c)

        walk(self.root)
        return out


def _count_and_check(
    root: Node,
    max_nodes: int,
    max_node_chars: int,
) -> tuple[int, int, int]:
    total = 0
    deepest = 0
    longest = 0

    def walk(n: Node) -> None:
        nonlocal total, deepest, longest
        total += 1
        deepest = max(deepest, n.depth)
        longest = max(longest, len(n.text))
        for c in n.children:
            walk(c)

    walk(root)
    if deepest > MAX_DEPTH:
        raise OutlineError(
            f"大纲层级 {deepest} 层，超过 {MAX_DEPTH} 层上限：请精简结构（合并浅层、拆分多张图）。"
        )
    if total > max_nodes:
        raise OutlineTooLargeError(total, 0)
    if longest > max_node_chars:
        raise OutlineTooLargeError(0, longest)
    return total, deepest, longest


def parse_outline(
    text: str,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_node_chars: int = DEFAULT_MAX_NODE_CHARS,
) -> OutlineDocument:
    """把大纲文本解析成节点树。支持 '# ' 标题（最多四级参与层级）与 '- ' 列表缩进两种混写。"""
    if not isinstance(text, str) or not text.strip():
        raise OutlineError(
            "大纲为空：请提供非空的大纲文本（Markdown 标题或 '-' 列表）。"
        )

    root = Node(text="__root__", depth=0, line_no=0)
    stack: list[Node] = [root]
    prev_list_depth = 0
    prev_node: Node | None = None
    title_holder: Node | None = None

    lines = text.splitlines()
    for idx, raw in enumerate(lines, start=1):
        if not raw.strip() or raw.lstrip().startswith("```"):
            continue

        hm = _HEADING_RE.match(raw)
        lm = _LIST_RE.match(raw) if not hm else None

        if hm:
            level = len(hm.group(1))
            node = Node(text=hm.group(2), depth=level, line_no=idx)
            target = min(level, 4)
            if target < 1:
                target = 1
            stack[:] = stack[:target]
            stack[-1].children.append(node)
            stack.append(node)
            prev_list_depth = 0
            prev_node = node
            continue

        if lm:
            indent = lm.group(1)
            if "\t" in indent:
                rel = len(indent)  # 每个 tab 一级
            else:
                spaces = len(indent)
                if spaces % 2 == 0:
                    rel = spaces // 2 + 1
                else:
                    raise OutlineError(
                        f"第 {idx} 行：列表缩进 {spaces} 个空格不是 2 的倍数，无法确定层级。"
                    )
            if prev_node is None:
                depth = max(rel, 1)
            elif prev_list_depth == 0:
                # 列表在标题/主题行之后开始：首项比上下文深一级，缩进量不决定绝对层级。
                depth = prev_node.depth + 1
            else:
                depth = prev_node.depth + (rel - prev_list_depth)
                if depth < 1:
                    depth = 1
            depth = min(depth, MAX_DEPTH + 1)
            node = Node(text=lm.group(3), depth=depth, line_no=idx)
            while len(stack) > depth:
                stack.pop()
            if len(stack) <= depth:
                stack.extend([stack[-1]] * (depth - len(stack) + 1))
            stack[depth - 1].children.append(node)
            stack[:] = stack[:depth]
            stack.append(node)
            prev_list_depth = rel
            prev_node = node
            continue

        stripped = raw.strip()
        if prev_node is not None and stripped:
            # 续行：并入上一个节点文本。
            prev_node.text = (prev_node.text + " " + stripped).strip()
            continue

        if stripped and prev_node is None and title_holder is None:
            # 首行自由文本作为主题（QQ 用户直接贴「主题 + 列表」形态）。
            title_holder = Node(text=stripped, depth=0, line_no=idx)
            root.children.append(title_holder)
            stack[:] = [root, title_holder]
            prev_node = title_holder
            prev_list_depth = 0
            continue

    if not root.children:
        raise OutlineError(
            "大纲中没有可用节点：请使用 Markdown 标题或 '-' 列表组织内容。"
        )

    if title_holder is not None:
        # 自由文本主题：其余一级节点并入其下。
        top = title_holder
        for sib in root.children[1:]:
            if sib is not title_holder:
                top.children.append(sib)
        _shift_depths(top)
    elif len(root.children) == 1 and root.children[0].depth == 1:
        # 单 '# 主题'：吸收为根，后代层级整体上移。
        top = root.children[0]
        top.depth = 0
        _shift_depths(top)
    else:
        top = Node(
            text=root.children[0].text if len(root.children) == 1 else "",
            depth=0,
            line_no=root.children[0].line_no,
            children=root.children,
        )
    total, deepest, _ = _count_and_check(top, max_nodes, max_node_chars)
    return OutlineDocument(root=top, total_nodes=total, max_depth=deepest)


def _shift_depths(node: Node, base: int = 0) -> None:
    """把子树深度归一到 base 起（吸收根后后代整体上移一级）。"""
    for c in node.children:
        c.depth = base + 1
        _shift_depths(c, base + 1)


def detect_layout(doc: OutlineDocument) -> str:
    """auto 规则：叶子节点 >=60% 匹配日期/世纪/朝代模式 -> timeline，否则 tree。"""
    leaves = doc.leaves()
    if not leaves:
        return "tree"
    hits = sum(1 for leaf in leaves if _looks_like_time(leaf.text))
    return "timeline" if hits / len(leaves) >= 0.6 else "tree"


def _looks_like_time(text: str) -> bool:
    probe = text.splitlines()[0] if text else ""
    return any(p.search(probe) for p in _DATE_PATTERNS)


def split_label(text: str) -> tuple[str, str]:
    """时间线节点 '标签: 描述' 切分；无标签返回 ('', text)。"""
    m = _LABEL_RE.match(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", text.strip()
