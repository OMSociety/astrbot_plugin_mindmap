"""有向无环基础流程图：节点声明、逐层连线校验、布局与绘制。"""

from __future__ import annotations

import math
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from .fonts import FontManager
from .layout import wrap_text
from .render import RenderResult, safe_canvas_scale
from .theme import Theme

MAX_FLOW_NODES = 30
MAX_LABEL_CHARS = 120
MAX_TITLE_CHARS = 80
MAX_TITLE_TEXT_W = 1000
TITLE_LINE_GAP = 12
MAX_TEXT_W = 320
MAX_DECISION_TEXT_W = 160
NODE_FS = 32
TITLE_FS = 48
NODE_PAD_X = 28
NODE_PAD_Y = 28
LAYER_GAP = 120
SIBLING_GAP = 64
PAD = 64
TITLE_GAP = 56
EDGE_W = 4
ARROW_SIZE = 16
DIAMOND_MIN_ASPECT = 3.0
DIAMOND_TEXT_PADDING = 16

_NODE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)(?:\s+\[([a-z]+)\])?\s+(.+)$")
_EDGE_RE = re.compile(
    r"^([A-Za-z][A-Za-z0-9_-]*)\s*->\s*([A-Za-z][A-Za-z0-9_-]*)(?:\s*[:：]\s*(.+))?$"
)
_KINDS = {"start", "process", "decision", "end"}


class FlowchartError(ValueError):
    """流程声明不满足无环、逐层连接等输入约束。"""


@dataclass
class FlowNode:
    id: str
    kind: str
    text: str
    line_no: int


@dataclass
class FlowEdge:
    source: str
    target: str
    label: str = ""


@dataclass
class FlowchartDocument:
    title: str
    nodes: dict[str, FlowNode]
    edges: list[FlowEdge]


@dataclass
class _FlowBox:
    node: FlowNode
    layer: int
    lines: list[str]
    w: int
    h: int
    x: float = 0.0
    y: float = 0.0
    children: list["_FlowBox"] = field(default_factory=list)

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


def _edge_sort_key(edge: FlowEdge) -> tuple[int, str]:
    return (0 if edge.label in ("是", "yes", "Yes", "YES") else 1, edge.target)


def parse_flowchart(spec: str) -> FlowchartDocument:
    """解析节点与箭头声明，并校验为所有边只跨一层的 DAG。"""
    if not isinstance(spec, str) or not spec.strip():
        raise FlowchartError("流程为空：请提供节点声明和 '起点 -> 终点' 连线。")
    title = ""
    nodes: dict[str, FlowNode] = {}
    edges: list[FlowEdge] = []
    for line_no, raw in enumerate(spec.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#") and not nodes and not edges and not title:
            title = line.lstrip("#").strip()
            if not title:
                raise FlowchartError(f"第 {line_no} 行标题为空。")
            if len(title) > MAX_TITLE_CHARS:
                raise FlowchartError(
                    f"流程标题共 {len(title)} 字，超过 {MAX_TITLE_CHARS} 字上限，请缩短标题。"
                )
            continue
        if "->" in line:
            match = _EDGE_RE.fullmatch(line)
            if not match:
                raise FlowchartError(
                    f"第 {line_no} 行连线格式有误：请写成 '起点 -> 终点: 条件'。"
                )
            edges.append(
                FlowEdge(match.group(1), match.group(2), (match.group(3) or "").strip())
            )
            continue
        match = _NODE_RE.fullmatch(line)
        if not match:
            raise FlowchartError(
                f"第 {line_no} 行无法识别：节点 ID 须以 ASCII 字母开头，"
                "声明格式为 'id [process] 内容'。"
            )
        node_id, kind, text = match.groups()
        kind = kind or "process"
        if kind not in _KINDS:
            raise FlowchartError(
                f"第 {line_no} 行节点类型 {kind} 不可用：请选 start、process、decision 或 end。"
            )
        if node_id in nodes:
            raise FlowchartError(f"第 {line_no} 行节点 {node_id} 重复声明。")
        if len(text) > MAX_LABEL_CHARS:
            raise FlowchartError(
                f"第 {line_no} 行节点共 {len(text)} 字，超过 {MAX_LABEL_CHARS} 字上限。"
            )
        nodes[node_id] = FlowNode(node_id, kind, text.strip(), line_no)
    if not nodes:
        raise FlowchartError("流程没有节点：请先声明节点，再添加连线。")
    if len(nodes) > MAX_FLOW_NODES:
        raise FlowchartError(
            f"流程共 {len(nodes)} 个节点，超过 {MAX_FLOW_NODES} 个上限，请拆图。"
        )
    if not edges and len(nodes) > 1:
        raise FlowchartError("流程缺少连线：请用 '起点 -> 终点' 声明执行顺序。")
    seen_edges: set[tuple[str, str]] = set()
    for edge in edges:
        pair = (edge.source, edge.target)
        if pair in seen_edges:
            raise FlowchartError(
                f"连线 {edge.source} -> {edge.target} 重复声明：请只保留一条并明确条件。"
            )
        seen_edges.add(pair)
        for node_id in (edge.source, edge.target):
            if node_id not in nodes:
                raise FlowchartError(
                    f"连线引用了未声明节点 {node_id}：请先声明该节点。"
                )
        if edge.source == edge.target:
            raise FlowchartError(
                f"节点 {edge.source} 指向自身，形成回环；请改为顺序或分支汇合。"
            )

    children: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    indegree = {node_id: 0 for node_id in nodes}
    for edge in edges:
        children[edge.source].append(edge.target)
        indegree[edge.target] += 1
    queue = deque(node_id for node_id in nodes if indegree[node_id] == 0)
    levels: dict[str, int] = {}
    visited = 0
    while queue:
        node_id = queue.popleft()
        visited += 1
        for child in children[node_id]:
            levels[child] = max(levels.get(child, 0), levels.get(node_id, 0) + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if visited != len(nodes):
        raise FlowchartError(
            "流程包含回环：请移除返回前序节点的连线，或拆成多张顺序流程图。"
        )
    levels.update({node_id: 0 for node_id in nodes if node_id not in levels})
    roots = [
        node_id for node_id in nodes if not any(e.target == node_id for e in edges)
    ]
    if len(roots) != 1:
        raise FlowchartError(
            "流程必须有且只有一个入口；当前存在多个入口或不可达节点，请连接所有节点。"
        )
    if nodes[roots[0]].kind != "start":
        raise FlowchartError(f"入口节点 {roots[0]} 必须使用 [start] 类型。")
    incoming = {edge.target for edge in edges}
    outgoing = {edge.source for edge in edges}
    for node_id, node in nodes.items():
        if node.kind == "start" and node_id in incoming:
            raise FlowchartError(f"开始节点 {node_id} 不能有入边。")
        if node.kind == "end" and node_id in outgoing:
            raise FlowchartError(f"结束节点 {node_id} 不能有出边。")
        if node.kind not in ("start", "end") and (
            node_id not in incoming or node_id not in outgoing
        ):
            raise FlowchartError(
                f"节点 {node_id} 孤立在流程末端：请连接到 [end] 节点，或将它改为 [end] 类型。"
            )
    if not any(node.kind == "end" for node in nodes.values()):
        raise FlowchartError("流程至少需要一个 [end] 结束节点。")
    for edge in edges:
        if levels[edge.target] != levels[edge.source] + 1:
            raise FlowchartError(
                f"连线 {edge.source} -> {edge.target} 跨层：请补充中间节点，使每条边只进入下一层。"
            )
    return FlowchartDocument(title=title, nodes=nodes, edges=edges)


def _make_box(node: FlowNode, layer: int, fm: FontManager) -> _FlowBox:
    bold = node.kind in ("start", "end")
    max_text_w = MAX_DECISION_TEXT_W if node.kind == "decision" else MAX_TEXT_W
    lines = wrap_text(node.text, fm, NODE_FS, bold, max_text_w)
    fnt = fm.get(NODE_FS, bold)
    text_widths = [fnt.getlength(line) for line in lines]
    text_h = len(lines) * (NODE_FS + 12)
    if node.kind == "decision":
        # 菱形在每一行的高度处收窄，宽度须按各行离中心的距离分别计算。
        line_h = NODE_FS + 12
        half_h = text_h / 2 + NODE_PAD_Y
        needed_w = max(
            2
            * text_width
            * half_h
            / (text_h / 2 - abs((index + 0.5) * line_h - text_h / 2))
            + 2 * DIAMOND_TEXT_PADDING
            for index, text_width in enumerate(text_widths)
        )
        h = max(text_h + 2 * NODE_PAD_Y, needed_w / DIAMOND_MIN_ASPECT)
        w = int(math.ceil(h * DIAMOND_MIN_ASPECT))
    else:
        w = int(math.ceil(max(text_widths))) + 2 * NODE_PAD_X
        h = text_h + 2 * NODE_PAD_Y
    return _FlowBox(node=node, layer=layer, lines=lines, w=w, h=h)


def _layout(doc: FlowchartDocument, direction: str, fm: FontManager):
    if direction not in ("vertical", "horizontal"):
        raise FlowchartError("布局方向仅支持 vertical（纵向）或 horizontal（横向）。")
    levels = {node_id: 0 for node_id in doc.nodes}
    for _ in range(len(doc.nodes)):
        changed = False
        for edge in doc.edges:
            value = levels[edge.source] + 1
            if value > levels[edge.target]:
                levels[edge.target] = value
                changed = True
        if not changed:
            break
    by_layer: dict[int, list[_FlowBox]] = {}
    boxes: dict[str, _FlowBox] = {}
    for node_id, node in doc.nodes.items():
        layer = levels[node_id]
        box = _make_box(node, layer, fm)
        boxes[node_id] = box
        by_layer.setdefault(layer, []).append(box)
    for edge in sorted(doc.edges, key=_edge_sort_key):
        boxes[edge.source].children.append(boxes[edge.target])
    for layer_boxes in by_layer.values():
        layer_boxes.sort(
            key=lambda box: (box.node.kind != "decision", box.node.line_no)
        )

    title_lines = (
        wrap_text(doc.title, fm, TITLE_FS, True, MAX_TITLE_TEXT_W) if doc.title else []
    )
    max_title_w = int(
        max(
            (fm.get(TITLE_FS, True).getlength(line) for line in title_lines),
            default=0,
        )
    )
    title_h = (
        len(title_lines) * (TITLE_FS + TITLE_LINE_GAP) + TITLE_GAP if title_lines else 0
    )
    if direction == "vertical":
        cursor = PAD + title_h
        max_cross = 0
        for layer in sorted(by_layer):
            layer_boxes = by_layer[layer]
            max_node_h = max(box.h for box in layer_boxes)
            total_w = sum(box.w for box in layer_boxes) + SIBLING_GAP * (
                len(layer_boxes) - 1
            )
            max_cross = max(max_cross, total_w)
            x = PAD
            for box in layer_boxes:
                box.x = x
                box.y = cursor + (max_node_h - box.h) / 2
                x += box.w + SIBLING_GAP
            cursor += max_node_h + LAYER_GAP
        width = max(max_cross, max_title_w) + 2 * PAD
        height = cursor - LAYER_GAP + PAD
        for layer_boxes in by_layer.values():
            total_w = sum(box.w for box in layer_boxes) + SIBLING_GAP * (
                len(layer_boxes) - 1
            )
            shift = (width - 2 * PAD - total_w) / 2
            for box in layer_boxes:
                box.x += shift
    else:
        cursor = PAD + title_h
        max_cross = 0
        for layer in sorted(by_layer):
            layer_boxes = by_layer[layer]
            max_node_w = max(box.w for box in layer_boxes)
            total_h = sum(box.h for box in layer_boxes) + SIBLING_GAP * (
                len(layer_boxes) - 1
            )
            max_cross = max(max_cross, total_h)
            y = PAD + title_h
            for box in layer_boxes:
                box.y = y
                box.x = cursor
                y += box.h + SIBLING_GAP
            cursor += max_node_w + LAYER_GAP
        height = max(max_cross, TITLE_FS) + 2 * PAD + title_h
        width = max(cursor - LAYER_GAP + PAD, max_title_w + 2 * PAD)
        for layer_boxes in by_layer.values():
            total_h = sum(box.h for box in layer_boxes) + SIBLING_GAP * (
                len(layer_boxes) - 1
            )
            shift = (height - 2 * PAD - title_h - total_h) / 2
            for box in layer_boxes:
                box.y += shift
    return boxes, int(width), int(height), title_h


def _arrow(
    dr: ImageDraw.ImageDraw,
    end: tuple[float, float],
    previous: tuple[float, float],
    color,
    scale: float,
):
    angle = math.atan2(end[1] - previous[1], end[0] - previous[0])
    size = ARROW_SIZE * scale
    left = (
        end[0] - size * math.cos(angle) + size * 0.65 * math.sin(angle),
        end[1] - size * math.sin(angle) - size * 0.65 * math.cos(angle),
    )
    right = (
        end[0] - size * math.cos(angle) - size * 0.65 * math.sin(angle),
        end[1] - size * math.sin(angle) + size * 0.65 * math.cos(angle),
    )
    dr.polygon([end, left, right], fill=color)


def _draw_edge(
    dr: ImageDraw.ImageDraw,
    source: _FlowBox,
    target: _FlowBox,
    edge: FlowEdge,
    direction: str,
    theme: Theme,
    fm: FontManager,
    scale: float,
):
    color = theme.root_fill
    if direction == "vertical":
        start = (source.cx * scale, (source.y + source.h) * scale)
        end = (target.cx * scale, target.y * scale)
        elbow_y = (start[1] + end[1]) / 2
        points = [start, (start[0], elbow_y), (end[0], elbow_y), end]
    else:
        start = ((source.x + source.w) * scale, source.cy * scale)
        end = (target.x * scale, target.cy * scale)
        elbow_x = (start[0] + end[0]) / 2
        points = [start, (elbow_x, start[1]), (elbow_x, end[1]), end]
    dr.line(points, fill=color, width=max(1, int(EDGE_W * scale)), joint="curve")
    _arrow(dr, end, points[-2], color, scale)
    if edge.label:
        midpoint = (
            (points[1][0] + points[2][0]) / 2,
            (points[1][1] + points[2][1]) / 2,
        )
        fnt = fm.get(24 * scale, False)
        bbox = dr.textbbox(midpoint, edge.label, font=fnt, anchor="mm")
        dr.rounded_rectangle(
            [
                bbox[0] - 7 * scale,
                bbox[1] - 4 * scale,
                bbox[2] + 7 * scale,
                bbox[3] + 4 * scale,
            ],
            radius=5 * scale,
            fill=theme.bg,
        )
        dr.text(midpoint, edge.label, font=fnt, fill=theme.text_on_light, anchor="mm")


def _draw_node(
    dr: ImageDraw.ImageDraw, box: _FlowBox, theme: Theme, fm: FontManager, scale: float
):
    x0, y0 = box.x * scale, box.y * scale
    x1, y1 = (box.x + box.w) * scale, (box.y + box.h) * scale
    if box.node.kind in ("start", "end"):
        fill, text_color, outline = theme.root_fill, theme.text_on_dark, None
    elif box.node.kind == "decision":
        fill, text_color, outline = theme.branch_2, theme.text_on_dark, None
    else:
        fill, text_color, outline = theme.deep_fill, theme.text_on_light, theme.branch_3
    if box.node.kind == "decision":
        dr.polygon(
            [
                ((x0 + x1) / 2, y0),
                (x1, (y0 + y1) / 2),
                ((x0 + x1) / 2, y1),
                (x0, (y0 + y1) / 2),
            ],
            fill=fill,
        )
    elif box.node.kind in ("start", "end"):
        dr.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2, fill=fill)
    else:
        dr.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=16 * scale,
            fill=fill,
            outline=outline,
            width=max(1, int(2 * scale)) if outline else 0,
        )
    fnt = fm.get(NODE_FS * scale, box.node.kind in ("start", "end"))
    lh = (NODE_FS + 12) * scale
    ty = box.cy * scale - len(box.lines) * lh / 2 + lh / 2
    for line in box.lines:
        dr.text((box.cx * scale, ty), line, font=fnt, fill=text_color, anchor="mm")
        ty += lh


def render_flowchart_png(
    doc: FlowchartDocument,
    direction: str,
    theme: Theme,
    fm: FontManager,
    out_path: Path,
    max_img_width: int = 4000,
    output_scale: float = 1.0,
) -> RenderResult:
    """绘制仅含逐层有向无环连线的流程图。"""
    boxes, width, height, _ = _layout(doc, direction, fm)
    scale = safe_canvas_scale(width, height, output_scale)
    img = Image.new("RGB", (int(width * scale), int(height * scale)), theme.bg)
    dr = ImageDraw.Draw(img)
    if doc.title:
        title_lines = wrap_text(doc.title, fm, TITLE_FS, True, MAX_TITLE_TEXT_W)
        line_height = (TITLE_FS + TITLE_LINE_GAP) * scale
        ty = PAD * scale + line_height / 2
        for line in title_lines:
            dr.text(
                (width * scale / 2, ty),
                line,
                font=fm.get(TITLE_FS * scale, True),
                fill=theme.text_on_light,
                anchor="mm",
            )
            ty += line_height
    for edge in doc.edges:
        _draw_edge(
            dr,
            boxes[edge.source],
            boxes[edge.target],
            edge,
            direction,
            theme,
            fm,
            scale,
        )
    for box in boxes.values():
        _draw_node(dr, box, theme, fm, scale)

    target_w = max(1, int(width * output_scale))
    target_h = max(1, int(height * output_scale))
    if img.width != target_w or img.height != target_h:
        img = img.resize((target_w, target_h), Image.LANCZOS)
    if img.width > max_img_width:
        nh = int(img.height * max_img_width / img.width)
        img = img.resize((max_img_width, nh), Image.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    return RenderResult(
        png_path=out_path,
        width=img.width,
        height=img.height,
        nodes=len(doc.nodes),
        layout="flowchart",
    )
