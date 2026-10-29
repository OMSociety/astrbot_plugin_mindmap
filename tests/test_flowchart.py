"""流程 DSL：节点与边、DAG 分层约束、真实双向 PNG 渲染。"""

from PIL import Image
import pytest

from astrbot_plugin_mindmap.core.flowchart import (
    FlowchartError,
    _layout,
    _make_box,
    parse_flowchart,
    render_flowchart_png,
)
from astrbot_plugin_mindmap.core.fonts import FontManager
from astrbot_plugin_mindmap.core.theme import get_theme

BRANCHING_DAG = """# 材料审核
start [start] 收到材料
check [decision] 材料完整？
supplement [process] 补充材料
review 审核材料
finish [end] 完成归档
start -> check
check -> supplement: 否
check -> review: 是
supplement -> finish
review -> finish
"""


def test_parse_branching_dag_with_merge_and_labels():
    doc = parse_flowchart(BRANCHING_DAG)
    nodes = doc.nodes

    assert doc.title == "材料审核"
    assert set(nodes) == {"start", "check", "supplement", "review", "finish"}
    assert nodes["start"].kind == "start"
    assert nodes["check"].kind == "decision"
    assert nodes["review"].kind == "process"
    assert nodes["finish"].kind == "end"
    assert {(edge.source, edge.target) for edge in doc.edges} == {
        ("start", "check"),
        ("check", "supplement"),
        ("check", "review"),
        ("supplement", "finish"),
        ("review", "finish"),
    }
    assert any(edge.label == "否" for edge in doc.edges)
    assert any(edge.label == "是" for edge in doc.edges)


@pytest.mark.parametrize(
    ("spec", "keyword"),
    [
        ("   \n\n", "空"),
        (
            "a [start] 开始\nb [process] 处理\nc [end] 结束\na -> b\nb -> a\nb -> c",
            "回环",
        ),
        (
            "a [start] 开始\nb [process] 处理\nc [process] 复核\nd [end] 结束\n"
            "a -> b\nb -> c\na -> c\nc -> d",
            "跨层",
        ),
        ("a [start] 开始\nb [end] 结束\norphan [process] 孤立\na -> b", "不可达"),
        ("a [start] 开始\nb [end] 结束\na -> missing", "未声明"),
        ("a [start] 开始\na [end] 结束\na -> a", "重复"),
        ("a [start] 开始\nb [end] 结束\na -> b\n# 注释", "行"),
        ("1a [start] 开始\nb [end] 结束\n1a -> b", "ID"),
        ("a 开始\nb [end] 结束\na -> b", "start"),
        ("a [start] 开始\nb [process] 结束\na -> b", "end"),
        ("a [start] 开始\nb [end] 结束\nc [process] 后续\na -> b\nb -> c", "出边"),
        ("a [start] 开始\nb [end] 结束\na -> b: 是\na -> b: 否", "重复"),
    ],
)
def test_reject_invalid_flowchart(spec, keyword):
    with pytest.raises(FlowchartError, match=keyword) as exc_info:
        parse_flowchart(spec)
    assert isinstance(exc_info.value, ValueError)


def test_reject_more_than_thirty_nodes():
    nodes = ["n0 [start] 开始"]
    nodes.extend(f"n{i} [process] 节点{i}" for i in range(1, 30))
    nodes.append("n30 [end] 结束")
    edges = [f"n{i} -> n{i + 1}" for i in range(30)]
    with pytest.raises(FlowchartError, match="30") as exc_info:
        parse_flowchart("\n".join([*nodes, *edges]))
    assert isinstance(exc_info.value, ValueError)


@pytest.mark.parametrize("direction", ["vertical", "horizontal"])
def test_render_real_png_in_both_directions(direction, tmp_path):
    doc = parse_flowchart(BRANCHING_DAG)
    out_path = tmp_path / f"flowchart-{direction}.png"
    rr = render_flowchart_png(doc, direction, get_theme(""), FontManager(), out_path)

    assert rr.png_path.is_file()
    assert rr.width > 0 and rr.height > 0
    with Image.open(rr.png_path) as image:
        image.load()
        assert image.format == "PNG"
        assert image.size == (rr.width, rr.height)
        assert len(set(image.convert("RGB").getdata())) > 2


def test_long_decision_text_stays_inside_diamond():
    fm = FontManager()
    node = parse_flowchart(
        "a [start] 开始\nb [decision] " + "判" * 30 + "\nc [end] 结束\na -> b\nb -> c"
    ).nodes["b"]
    box = _make_box(node, 1, fm)
    font = fm.get(32, False)
    text_h = len(box.lines) * 44
    for index, line in enumerate(box.lines):
        text_w = font.getlength(line)
        available_ratio = 1 - abs((index + 0.5) * 44 - text_h / 2) / (box.h / 2)
        assert text_w + 28 <= box.w * available_ratio


def test_long_title_wraps_in_both_directions():
    doc = parse_flowchart(
        "# " + "流程标题" * 10 + "\na [start] 开始\nb [end] 结束\na -> b"
    )
    fm = FontManager()
    for direction in ("vertical", "horizontal"):
        _, width, height, title_h = _layout(doc, direction, fm)
        assert width >= 1000
        assert title_h > 100
        assert height > title_h


def test_title_length_limit():
    with pytest.raises(FlowchartError, match="80"):
        parse_flowchart("# " + "题" * 81 + "\na [start] 开始\nb [end] 结束\na -> b")


def test_horizontal_render_respects_max_width_at_output_scale(tmp_path):
    doc = parse_flowchart(BRANCHING_DAG)
    out_path = tmp_path / "flowchart-wide.png"
    rr = render_flowchart_png(
        doc,
        "horizontal",
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
