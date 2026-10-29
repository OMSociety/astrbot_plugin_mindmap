"""Markdown 表格：转义与结构校验、硬上限、真实 PNG 与宽度约束。"""

from PIL import Image
import pytest

from astrbot_plugin_mindmap.core.fonts import FontManager
from astrbot_plugin_mindmap.core.layout import wrap_text
from astrbot_plugin_mindmap.core.table import (
    TableError,
    _column_widths,
    _table_cells,
    parse_table,
    render_table_png,
    validate_table_title,
)
from astrbot_plugin_mindmap.core.theme import get_theme


def _table(columns: int, rows: int) -> str:
    header = "| " + " | ".join(f"列{i}" for i in range(columns)) + " |"
    separator = "| " + " | ".join("---" for _ in range(columns)) + " |"
    body = [
        "| " + " | ".join(f"值{row}-{col}" for col in range(columns)) + " |"
        for row in range(rows)
    ]
    return "\n".join([header, separator, *body])


def test_parse_markdown_table_and_escaped_pipe():
    doc = parse_table(
        "| 概念 | 定义 |\n| --- | ---: |\n| 逻辑或 | 表达式 A \\| B |\n| 空单元 |  |"
    )

    assert len(doc.rows) == 2
    assert "逻辑或" in str(doc.rows[0])
    assert "表达式 A | B" in str(doc.rows[0])
    assert "表达式 A \\| B" not in str(doc.rows[0])


def test_escaped_backslash_before_column_separator():
    doc = parse_table("| A |\n| --- |\n| x \\\\|")

    assert doc.rows == [["x \\"]]

    with pytest.raises(TableError, match="3 列"):
        parse_table("| A | B |\n| --- | --- |\n| x \\\\| y | z |")


def test_escaped_pipe_at_end_of_cell():
    doc = parse_table("| A | B |\n| --- | --- |\n| x \\| | y |")

    assert doc.rows == [["x |", "y"]]


@pytest.mark.parametrize(
    ("markdown", "keyword"),
    [
        ("| A | B |\n| --- | --- |\n| 仅一列 |", "列"),
        ("| A | B |\n| --- |\n| 甲 | 乙 |", "分隔"),
        ("| A | B |\n| --- | --- |\n| 甲 | 乙 |\n不是表格行", "行"),
    ],
)
def test_reject_malformed_table(markdown, keyword):
    with pytest.raises(TableError, match=keyword) as exc_info:
        parse_table(markdown)
    assert isinstance(exc_info.value, ValueError)


def test_reject_more_than_eight_columns():
    with pytest.raises(TableError, match="8") as exc_info:
        parse_table(_table(9, 1))
    assert isinstance(exc_info.value, ValueError)


def test_reject_more_than_fifty_data_rows():
    with pytest.raises(TableError, match="50") as exc_info:
        parse_table(_table(2, 51))
    assert isinstance(exc_info.value, ValueError)


def test_reject_cell_longer_than_two_hundred_characters():
    markdown = "| A |\n| --- |\n| " + "字" * 201 + " |"
    with pytest.raises(TableError, match="200") as exc_info:
        parse_table(markdown)
    assert isinstance(exc_info.value, ValueError)


def test_render_real_png_with_wrapped_chinese_text(tmp_path):
    fm = FontManager()
    theme = get_theme("")
    short_doc = parse_table("| 哲学家 | 学说 |\n| --- | --- |\n| 康德 | 先验批判 |")
    long_doc = parse_table(
        "| 哲学家 | 学说 |\n"
        "| --- | --- |\n"
        "| 康德 | 通过先验批判考察认识何以可能，并说明经验对象与认识形式之间的关系。 |"
    )
    out_path = tmp_path / "table.png"
    rr = render_table_png(long_doc, theme, fm, out_path, max_img_width=360)
    render_table_png(
        short_doc, theme, fm, tmp_path / "short-table.png", max_img_width=360
    )
    long_layout_h = _table_cells(long_doc, fm, _column_widths(long_doc, fm))[3]
    short_layout_h = _table_cells(short_doc, fm, _column_widths(short_doc, fm))[3]

    assert rr.png_path.is_file()
    assert rr.width > 0 and rr.height > 0
    assert long_layout_h > short_layout_h
    with Image.open(rr.png_path) as image:
        image.load()
        assert image.format == "PNG"
        assert image.size == (rr.width, rr.height)
        assert len(set(image.convert("RGB").getdata())) > 2


def test_short_header_is_not_wrapped_by_narrow_body():
    fm = FontManager()
    doc = parse_table("| 关键能力 |\n| --- |\n| 理性 |")
    cells, _, _, _ = _table_cells(doc, fm, _column_widths(doc, fm))

    assert cells[0][0].lines == ["关键能力"]


def test_long_title_wraps_and_expands_canvas(tmp_path):
    fm = FontManager()
    doc = parse_table("| A | B |\n| --- | --- |\n| 甲 | 乙 |")
    doc.title = "表格标题" * 10
    cells, _, width, height = _table_cells(doc, fm, _column_widths(doc, fm))
    rr = render_table_png(doc, get_theme("靛蓝"), fm, tmp_path / "titled.png")

    assert len(wrap_text(doc.title, fm, 48, True, 1000)) > 1
    assert width > 1000
    assert height > cells[0][0].y
    assert rr.width == width


def test_title_length_limit():
    with pytest.raises(TableError, match="80"):
        validate_table_title("题" * 81)


def test_render_respects_max_width_at_output_scale(tmp_path):
    doc = parse_table(_table(8, 8))
    out_path = tmp_path / "wide-table.png"
    rr = render_table_png(
        doc,
        get_theme("朱砂"),
        FontManager(),
        out_path,
        max_img_width=700,
        output_scale=2,
    )

    assert rr.width <= 700
    with Image.open(rr.png_path) as image:
        image.load()
        assert image.format == "PNG"
        assert image.width <= 700
