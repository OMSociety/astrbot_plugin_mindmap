"""标准 Markdown 表格解析、自动列宽与 Pillow 绘制。"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from .fonts import FontManager
from .layout import wrap_text
from .render import RenderResult, safe_canvas_scale
from .theme import Theme

MAX_COLUMNS = 8
MAX_ROWS = 50
MAX_CELL_CHARS = 200
MAX_TITLE_CHARS = 80
MAX_TITLE_TEXT_W = 1000
TITLE_LINE_GAP = 12
CELL_FS = 30
HEADER_FS = 32
TITLE_FS = 48
CELL_PAD_X = 22
CELL_PAD_Y = 18
MAX_CELL_TEXT_W = 360
MIN_COLUMN_W = 112
TITLE_GAP = 34
PAD = 56
GRID_W = 2

_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")


class TableError(ValueError):
    """表格输入不符合标准 Markdown 表格约束。"""


@dataclass
class TableDocument:
    headers: list[str]
    rows: list[list[str]]
    title: str = ""

    @property
    def columns(self) -> int:
        return len(self.headers)


def _split_row(line: str, line_no: int) -> list[str]:
    text = line.strip()
    if "|" not in text:
        raise TableError(f"第 {line_no} 行不是表格行：请用竖线分隔各列。")
    cells: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text) and text[i + 1] in ("|", "\\"):
            buf.append(text[i + 1])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    if text.startswith("|"):
        cells = cells[1:]
    trailing_backslashes = len(text[:-1]) - len(text[:-1].rstrip("\\"))
    if (
        cells
        and cells[-1] == ""
        and text.endswith("|")
        and trailing_backslashes % 2 == 0
    ):
        cells = cells[:-1]
    if not cells:
        raise TableError(f"第 {line_no} 行没有可用单元格。")
    return cells


def parse_table(markdown: str) -> TableDocument:
    """解析含表头与分隔行的标准 Markdown 表格。"""
    if not isinstance(markdown, str) or not markdown.strip():
        raise TableError("表格为空：请提供含表头和分隔行的 Markdown 表格。")
    lines = [
        (i, line) for i, line in enumerate(markdown.splitlines(), 1) if line.strip()
    ]
    if len(lines) < 2:
        raise TableError("表格至少需要表头行和分隔行，例如 | 列 | 后跟 | --- |。")
    parsed = [_split_row(line, no) for no, line in lines]
    headers = parsed[0]
    if len(headers) > MAX_COLUMNS:
        raise TableError(
            f"表格共 {len(headers)} 列，超过 {MAX_COLUMNS} 列上限，请拆分表格。"
        )
    if not all(headers):
        raise TableError("表头不能为空：请为每一列填写名称。")
    separators = parsed[1]
    if len(separators) != len(headers) or not all(
        _SEPARATOR_RE.fullmatch(cell.replace(" ", "")) for cell in separators
    ):
        raise TableError(
            "第二行必须是与表头等列数的 Markdown 分隔行，例如 | --- | --- |。"
        )
    rows = parsed[2:]
    if len(rows) > MAX_ROWS:
        raise TableError(
            f"表格共 {len(rows)} 行数据，超过 {MAX_ROWS} 行上限，请拆分表格。"
        )
    for index, row in enumerate(rows, start=3):
        if len(row) != len(headers):
            raise TableError(
                f"第 {lines[index - 1][0]} 行有 {len(row)} 列，表头有 {len(headers)} 列：请补齐或删除多余单元格。"
            )
    for row in [headers, *rows]:
        for cell in row:
            if len(cell) > MAX_CELL_CHARS:
                raise TableError(
                    f"单元格共 {len(cell)} 字，超过 {MAX_CELL_CHARS} 字上限，请拆分内容。"
                )
    return TableDocument(headers=headers, rows=rows)


def validate_table_title(title: str) -> str:
    title = title.strip()
    if len(title) > MAX_TITLE_CHARS:
        raise TableError(
            f"表格标题共 {len(title)} 字，超过 {MAX_TITLE_CHARS} 字上限，请缩短标题。"
        )
    return title


@dataclass
class _CellLayout:
    lines: list[str]
    x: float
    y: float
    w: int
    h: int


def _column_widths(doc: TableDocument, fm: FontManager) -> list[int]:
    widths: list[int] = []
    for col in range(doc.columns):
        body_natural = max(
            (fm.get(CELL_FS, False).getlength(row[col]) for row in doc.rows),
            default=0,
        )
        header_natural = fm.get(HEADER_FS, True).getlength(doc.headers[col])
        natural = max(body_natural, header_natural)
        text_w = min(MAX_CELL_TEXT_W, max(48, int(math.ceil(natural))))
        widths.append(max(MIN_COLUMN_W, text_w + 2 * CELL_PAD_X))
    return widths


def _table_cells(
    doc: TableDocument, fm: FontManager, widths: list[int]
) -> tuple[list[list[_CellLayout]], list[int], int, int]:
    xs: list[float] = []
    table_x = PAD
    title_lines = (
        wrap_text(doc.title, fm, TITLE_FS, True, MAX_TITLE_TEXT_W) if doc.title else []
    )
    title_h = (
        len(title_lines) * (TITLE_FS + TITLE_LINE_GAP) + TITLE_GAP if title_lines else 0
    )
    header_y = PAD + title_h
    title_w = max(
        (fm.get(TITLE_FS, True).getlength(line) for line in title_lines),
        default=0,
    )
    table_w = sum(widths)
    width = int(max(table_w, title_w)) + 2 * PAD
    table_x = (width - table_w) / 2
    xs = [table_x]
    for column_width in widths[:-1]:
        xs.append(xs[-1] + column_width)
    cells: list[list[_CellLayout]] = []
    heights: list[int] = []
    y = header_y
    for row_index, values in enumerate([doc.headers, *doc.rows]):
        is_header = row_index == 0
        fs = HEADER_FS if is_header else CELL_FS
        wrapped = [
            wrap_text(value, fm, fs, is_header, widths[col] - 2 * CELL_PAD_X)
            for col, value in enumerate(values)
        ]
        height = max(len(lines) for lines in wrapped) * (fs + 12) + 2 * CELL_PAD_Y
        heights.append(height)
        cells.append(
            [
                _CellLayout(lines=lines, x=xs[col], y=y, w=widths[col], h=height)
                for col, lines in enumerate(wrapped)
            ]
        )
        y += height
    return cells, heights, width, y + PAD


def render_table_png(
    doc: TableDocument,
    theme: Theme,
    fm: FontManager,
    out_path: Path,
    max_img_width: int = 4000,
    output_scale: float = 1.0,
) -> RenderResult:
    """按主题绘制表格并输出 PNG。"""
    widths = _column_widths(doc, fm)
    cells, heights, width, height = _table_cells(doc, fm, widths)
    scale = safe_canvas_scale(width, height, output_scale)
    img = Image.new("RGB", (int(width * scale), int(height * scale)), theme.bg)
    dr = ImageDraw.Draw(img)

    header_y = cells[0][0].y
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

    body_top = header_y + heights[0]
    body_bottom = cells[-1][0].y + heights[-1]
    table_x = cells[0][0].x * scale
    table_right = (cells[0][-1].x + cells[0][-1].w) * scale
    dr.rectangle(
        [table_x, header_y * scale, table_right, body_bottom * scale],
        fill=theme.deep_fill,
    )
    dr.rectangle(
        [table_x, header_y * scale, table_right, body_top * scale],
        fill=theme.root_fill,
    )
    for index in range(2, len(cells), 2):
        row = cells[index]
        y0 = row[0].y * scale
        y1 = (row[0].y + row[0].h) * scale
        dr.rectangle([table_x, y0, table_right, y1], fill=theme.bg)

    grid = theme.branch_3
    for row_index, row in enumerate(cells):
        is_header = row_index == 0
        fs = HEADER_FS if is_header else CELL_FS
        fnt = fm.get(fs * scale, is_header)
        color = theme.text_on_dark if is_header else theme.text_on_light
        for cell in row:
            lh = (fs + 12) * scale
            ty = (cell.y + cell.h / 2) * scale - len(cell.lines) * lh / 2 + lh / 2
            for line in cell.lines:
                dr.text(
                    ((cell.x + CELL_PAD_X) * scale, ty),
                    line,
                    font=fnt,
                    fill=color,
                    anchor="lm",
                )
                ty += lh
        y = (row[0].y + row[0].h) * scale
        dr.line(
            [(table_x, y), (table_right, y)],
            fill=grid,
            width=max(1, int(GRID_W * scale)),
        )
    for x in [
        table_x / scale,
        *((cells[0][i].x + cells[0][i].w) for i in range(len(widths))),
    ]:
        dr.line(
            [(x * scale, header_y * scale), (x * scale, body_bottom * scale)],
            fill=grid,
            width=max(1, int(GRID_W * scale)),
        )

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
        nodes=len(doc.rows) * doc.columns,
        layout="table",
    )
