"""布局引擎：树状（根在左，水平展开）与时间线（竖轴左右交替）。"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .fonts import FontManager
from .parser import Node, OutlineError, split_label

PAD = 40
H_GAP = 90  # 树状层间距
V_GAP = 26  # 树状兄弟间距
TL_GAP = 34  # 时间线节点间距
MAX_TEXT_W = 220  # 树状节点文字最大像素宽
MAX_TEXT_W_TL = 260  # 时间线
ROOT_FS = 26
D1_FS = 21
D2_FS = 18
DEEP_FS = 16


@dataclass
class Box:
    node: Node
    depth: int
    x: float = 0.0
    yc: float = 0.0
    w: int = 0
    h: int = 0
    lines: list[str] = field(default_factory=list)
    fs: int = DEEP_FS
    bold: bool = False
    label: str = ""
    children: list["Box"] = field(default_factory=list)

    @property
    def top(self) -> float:
        return self.yc - self.h / 2

    @property
    def bottom(self) -> float:
        return self.yc + self.h / 2


@dataclass
class LayoutResult:
    kind: str  # tree | timeline
    root: Box
    width: int
    height: int
    axis_x: float = 0.0  # 仅 timeline 使用


def _fs_for(depth: int) -> tuple[int, bool]:
    if depth == 0:
        return ROOT_FS, True
    if depth == 1:
        return D1_FS, True
    if depth == 2:
        return D2_FS, False
    return DEEP_FS, False


def _units(text: str) -> list[str]:
    """排版单元：ASCII 词为单元，CJK 单字为单元，空白吸收进词。"""
    out: list[str] = []
    buf = ""
    for ch in text:
        if ord(ch) < 128 and not ch.isspace():
            buf += ch
        else:
            if buf:
                out.append(buf)
                buf = ""
            if ch.isspace():
                if out and not out[-1].endswith(" "):
                    out[-1] += " "
            else:
                out.append(ch)
    if buf:
        out.append(buf)
    return out


def wrap_text(
    text: str, fm: FontManager, size: int, bold: bool, max_w: int
) -> list[str]:
    """贪心折行：逐排版单元试探，超宽硬切。空文本返回 ['']。"""
    fnt = fm.get(size, bold)
    lines: list[str] = []
    for raw in text.split("\n"):
        cur = ""
        for u in _units(raw):
            trial = cur + u
            if fnt.getlength(trial) <= max_w or not cur:
                cur = trial
                while fnt.getlength(cur) > max_w and len(cur) > 1:
                    k = len(cur) - 1
                    while k > 1 and fnt.getlength(cur[:k]) > max_w:
                        k -= 1
                    lines.append(cur[:k])
                    cur = cur[k:]
            else:
                lines.append(cur.rstrip())
                cur = u.lstrip()
        lines.append(cur.rstrip())
    return [line for line in lines if line] or [""]


def _measure_box(node: Node, fm: FontManager, depth: int, max_w: int) -> Box:
    fs, bold = _fs_for(depth)
    lines = wrap_text(node.text, fm, fs, bold, max_w)
    fnt = fm.get(fs, bold)
    lw = max((fnt.getlength(line) for line in lines), default=0)
    box = Box(
        node=node,
        depth=depth,
        lines=lines,
        fs=fs,
        bold=bold,
        w=int(math.ceil(lw)) + 28,
        h=len(lines) * (fs + 8) + 18,
    )
    box.children = [_measure_box(c, fm, depth + 1, max_w) for c in node.children]
    return box


# ---------------- 树状布局 ----------------


def layout_tree(doc_root: Node, fm: FontManager) -> tuple[Box, int, int]:
    root = _measure_box(doc_root, fm, 0, MAX_TEXT_W)
    level_w: dict[int, int] = {}

    def _collect(b: Box) -> None:
        level_w[b.depth] = max(level_w.get(b.depth, 0), b.w)
        for c in b.children:
            _collect(c)

    _collect(root)
    x_of: dict[int, float] = {}
    acc = PAD
    for d in sorted(level_w):
        x_of[d] = acc
        acc += level_w[d] + H_GAP

    cursor = [PAD]

    def _place(b: Box) -> tuple[float, float]:
        b.x = x_of[b.depth]
        if not b.children:
            top = cursor[0]
            b.yc = top + b.h / 2
            cursor[0] = top + b.h + V_GAP
            return top, top + b.h
        tops: list[float] = []
        bots: list[float] = []
        for c in b.children:
            t, bt = _place(c)
            tops.append(t)
            bots.append(bt)
        top, bot = min(tops), max(bots)
        b.yc = (top + bot) / 2
        return top, bot

    _place(root)

    right = 0.0
    bottom = 0.0
    stack = [root]
    while stack:
        b = stack.pop()
        right = max(right, b.x + b.w)
        bottom = max(bottom, b.bottom)
        stack.extend(b.children)
    return root, int(right + PAD), int(bottom + PAD)


# ---------------- 时间线布局 ----------------


def layout_timeline(doc_root: Node, fm: FontManager) -> tuple[Box, int, int, float]:
    # 时间线只承载一层事件；深层节点在此显式拒绝（不静默裁剪内容）。
    if any(c.children for c in doc_root.children):
        raise OutlineError(
            "timeline 布局仅支持一层事件节点；大纲中存在带下级的事件，"
            "请改用 tree 布局（layout='tree'），或把深层条目并入其父节点的描述。"
        )
    title = Box(
        node=doc_root,
        depth=0,
        fs=ROOT_FS,
        bold=True,
        w=int(fm.get(ROOT_FS, True).getlength(doc_root.text)) + 36,
        h=ROOT_FS + 26,
    )
    title.yc = PAD + title.h / 2

    x_left = x_right = 0.0
    y = PAD + title.h + 46
    side = -1  # -1 左, 1 右
    for i, n in enumerate(doc_root.children):
        box = _measure_tl_box(n, fm, i)
        box.yc = y + box.h / 2
        if side < 0:
            box.x = -box.w - 30
            x_left = min(x_left, box.x)
        else:
            box.x = 30
            x_right = max(x_right, box.x + box.w)
        y += box.h + TL_GAP
        side = -side
        title.children.append(box)

    offset = PAD - x_left
    for b in title.children:
        b.x += offset
    axis_x = offset
    title.x = max(axis_x - title.w / 2, PAD)
    bottom = title.children[-1].bottom if title.children else title.bottom
    width = int(max(x_right + offset, title.x + title.w) + PAD)
    return title, width, int(bottom + PAD), axis_x


def _measure_tl_box(node: Node, fm: FontManager, index: int) -> Box:
    label, body_text = split_label(node.text)
    label_fnt = fm.get(D2_FS, True)
    body_fnt = fm.get(DEEP_FS, False)
    body = wrap_text(body_text, fm, DEEP_FS, False, MAX_TEXT_W_TL - 24)
    label_w = label_fnt.getlength(label) + 18 if label else 0
    lw = max([label_w] + [body_fnt.getlength(line) for line in body], default=0)
    return Box(
        node=node,
        depth=1,
        lines=body,
        fs=DEEP_FS,
        bold=False,
        label=label,
        w=int(math.ceil(lw)) + 28,
        h=(D2_FS + 10 if label else 0) + len(body) * (DEEP_FS + 8) + 18,
    )


def build_layout(
    doc_root: Node,
    kind: str,
    fm: FontManager,
) -> LayoutResult:
    if kind == "timeline":
        root, w, h, axis = layout_timeline(doc_root, fm)
        return LayoutResult(kind="timeline", root=root, width=w, height=h, axis_x=axis)
    root, w, h = layout_tree(doc_root, fm)
    return LayoutResult(kind="tree", root=root, width=w, height=h)
