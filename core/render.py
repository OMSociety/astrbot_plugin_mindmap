"""绘制与出图：圆角节点、贝塞尔连线、时间线轴；2x 超采样抗锯齿，PNG 落盘。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from .fonts import FontManager
from .layout import (
    BOX_PAD_X,
    D2_FS,
    DEEP_FS,
    LINE_GAP,
    ROOT_FS,
    TL_LABEL_H,
    TL_TITLE_PAD_X,
    Box,
    LayoutResult,
)
from .theme import Theme

SS = 2  # 超采样倍数：先 2x 绘制再 LANCZOS 缩回，消除几何锯齿
MAX_CANVAS_SIDE = 10000  # 限制超采样前的单边像素，避免极端布局触发大额内存分配
MAX_CANVAS_PIXELS = 40_000_000
RADIUS_NODE = 18  # 节点圆角
RADIUS_TITLE = 20  # 标题条圆角
EDGE_W = 4  # 连线宽
DOT_R_TREE = 8  # 树节点圆点半径
DOT_R_TL = 10  # 时间线轴圆点半径
AXIS_W = 6  # 时间线轴宽
TL_AXIS_TOP_GAP = 60  # 轴起点距标题底
TL_AXIS_BOT_INSET = 60  # 轴终点距画布底


@dataclass
class RenderResult:
    png_path: Path
    width: int
    height: int
    nodes: int
    layout: str


def _edge_color(theme: Theme, alpha: int = 150) -> tuple[int, int, int, int]:
    h = theme.root_fill.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, alpha)


def _curve(
    d: ImageDraw.ImageDraw,
    p0: tuple[float, float],
    p2: tuple[float, float],
    color: tuple[int, int, int, int],
    w: int,
) -> None:
    """二次贝塞尔：先水平后垂直的平滑转弯。"""
    p1 = (p2[0], p0[1])
    pts = []
    for i in range(33):
        t = i / 32
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        pts.append((x, y))
    d.line(pts, fill=color, width=int(w), joint="curve")


def _style(b: Box, theme: Theme) -> tuple[str, str, str | None]:
    """返回 (填充, 文字, 描边)。"""
    if b.depth == 0:
        return theme.root_fill, theme.text_on_dark, None
    if b.depth == 1:
        return theme.branch_1, theme.text_on_dark, None
    if b.depth == 2:
        return theme.branch_2, theme.text_on_dark, None
    return theme.deep_fill, theme.text_on_light, theme.branch_3


def _draw_box(
    dr: ImageDraw.ImageDraw, b: Box, theme: Theme, fm: FontManager, s: float
) -> None:
    """绘制节点框与折行文字，文字按行垂直居中堆叠。"""
    bg, fg, ln = _style(b, theme)
    x0, y0 = b.x * s, b.top * s
    dr.rounded_rectangle(
        [x0, y0, x0 + b.w * s, y0 + b.h * s],
        radius=RADIUS_NODE * s,
        fill=bg,
        outline=ln,
        width=int(s) if ln else 0,
    )
    fnt = fm.get(b.fs * s, b.bold)
    lh = (b.fs + LINE_GAP) * s
    total = len(b.lines) * lh
    ty = b.yc * s - total / 2 + lh / 2
    for line in b.lines:
        dr.text((x0 + BOX_PAD_X * s, ty), line, font=fnt, fill=fg, anchor="lm")
        ty += lh


def _draw_tree(
    res: LayoutResult, theme: Theme, fm: FontManager, scale: float
) -> Image.Image:
    s = scale
    img = Image.new("RGB", (int(res.width * s), int(res.height * s)), theme.bg)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dod = ImageDraw.Draw(ov)
    dr = ImageDraw.Draw(img)
    edge = _edge_color(theme)

    def _draw(b: Box) -> None:
        for c in b.children:
            _curve(
                dod,
                ((b.x + b.w) * s, b.yc * s),
                (c.x * s, c.yc * s),
                edge,
                EDGE_W * s,
            )
            r = DOT_R_TREE * s
            dod.ellipse(
                [c.x * s - r, c.yc * s - r, c.x * s + r, c.yc * s + r], fill=edge
            )
            _draw(c)
        _draw_box(dr, b, theme, fm, s)

    _draw(res.root)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def _draw_timeline(
    res: LayoutResult, theme: Theme, fm: FontManager, scale: float
) -> Image.Image:
    s = scale
    root = res.root
    img = Image.new("RGB", (int(res.width * s), int(res.height * s)), theme.bg)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dod = ImageDraw.Draw(ov)
    dr = ImageDraw.Draw(img)
    edge = _edge_color(theme)

    top = (root.bottom + TL_AXIS_TOP_GAP) * s
    bot = (res.height - TL_AXIS_BOT_INSET) * s
    dod.line(
        [(res.axis_x * s, top), (res.axis_x * s, bot)], fill=edge, width=int(AXIS_W * s)
    )

    # 标题条
    dr.rounded_rectangle(
        [root.x * s, root.top * s, (root.x + root.w) * s, root.bottom * s],
        radius=RADIUS_TITLE * s,
        fill=theme.root_fill,
    )
    dr.text(
        ((root.x + TL_TITLE_PAD_X) * s, root.yc * s),
        root.node.text,
        font=fm.get(ROOT_FS * s, True),
        fill=theme.text_on_dark,
        anchor="lm",
    )

    for c in root.children:
        left = c.x < res.axis_x
        edge_x = (c.x + c.w) * s if left else c.x * s
        dod.line(
            [(res.axis_x * s, c.yc * s), (edge_x, c.yc * s)],
            fill=edge,
            width=int(EDGE_W * s),
        )
        r = DOT_R_TL * s
        dod.ellipse(
            [res.axis_x * s - r, c.yc * s - r, res.axis_x * s + r, c.yc * s + r],
            fill=_edge_color(theme, 220),
        )
        bg, fg, ln = theme.deep_fill, theme.text_on_light, theme.branch_3
        x0, y0 = c.x * s, c.top * s
        dr.rounded_rectangle(
            [x0, y0, x0 + c.w * s, y0 + c.h * s],
            radius=RADIUS_NODE * s,
            fill=bg,
            outline=ln,
            width=int(s),
        )
        lh = DEEP_FS + LINE_GAP
        total = (D2_FS + TL_LABEL_H if c.label else 0) + len(c.lines) * lh
        ty = c.yc * s - (total * s) / 2 + ((D2_FS + TL_LABEL_H) * s) / 2
        if c.label:
            dr.text(
                (x0 + BOX_PAD_X * s, ty),
                c.label,
                font=fm.get(D2_FS * s, True),
                fill=theme.root_fill,
                anchor="lm",
            )
            ty += (D2_FS + TL_LABEL_H) * s
        body_fnt = fm.get(DEEP_FS * s, False)
        for line in c.lines:
            dr.text((x0 + BOX_PAD_X * s, ty), line, font=body_fnt, fill=fg, anchor="lm")
            ty += lh * s

    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def safe_canvas_scale(width: int, height: int, output_scale: float) -> float:
    """在创建位图前限制超采样倍率，保留比例并限定内存上界。"""
    requested = SS * max(0.5, min(output_scale, 4.0))
    budget = min(
        MAX_CANVAS_SIDE / max(1, width),
        MAX_CANVAS_SIDE / max(1, height),
        math.sqrt(MAX_CANVAS_PIXELS / max(1, width * height)),
    )
    if budget < 0.25:
        raise ValueError("图表布局过大，无法安全生成图片：请减少内容或拆成多张图。")
    return min(requested, budget)


def render_to_png(
    res: LayoutResult,
    theme: Theme,
    fm: FontManager,
    out_path: Path,
    max_img_width: int = 4000,
    output_scale: float = 1.0,
) -> RenderResult:
    """绘制并在 output_scale 倍输出尺寸上落盘。

    超采样 SS 负责抗锯齿；output_scale 负责最终分辨率——两者乘积是绘制倍率。
    """
    scale = safe_canvas_scale(res.width, res.height, output_scale)
    if res.kind == "timeline":
        img = _draw_timeline(res, theme, fm, scale)
    else:
        img = _draw_tree(res, theme, fm, scale)
    target_w = max(1, int(res.width * output_scale))
    target_h = max(1, int(res.height * output_scale))
    if img.width != target_w or img.height != target_h:
        img = img.resize((target_w, target_h), Image.LANCZOS)
    if img.width > max_img_width:
        nh = int(img.height * max_img_width / img.width)
        img = img.resize((max_img_width, nh), Image.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    nodes = 0
    stack = [res.root]
    while stack:
        b = stack.pop()
        nodes += 1
        stack.extend(b.children)
    return RenderResult(
        png_path=out_path,
        width=img.width,
        height=img.height,
        nodes=nodes,
        layout=res.kind,
    )
