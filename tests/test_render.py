"""端到端渲染：PNG 存在、尺寸在界、红系主色采样、节点数回传。"""

from PIL import Image

from astrbot_plugin_mindmap.core.fonts import FontManager
from astrbot_plugin_mindmap.core.layout import build_layout
from astrbot_plugin_mindmap.core.parser import parse_outline
from astrbot_plugin_mindmap.core.render import render_to_png
from astrbot_plugin_mindmap.core.theme import get_theme

TREE_MD = "# 康德的批判哲学体系\n## 纯粹理性批判\n- 先验感性论\n  - 细节\n## 实践理性批判\n- 定言令式"


def _render(md: str, kind: str, tmp_path, **kwargs):
    fm = FontManager()
    doc = parse_outline(md)
    res = build_layout(doc.root, kind, fm)
    return render_to_png(res, get_theme(""), fm, tmp_path / "out.png", **kwargs)


def _count_red(img: Image.Image) -> int:
    px = img.convert("RGB").load()
    w, h = img.size
    hits = 0
    for y in range(0, h, 5):
        for x in range(0, w, 5):
            r, g, b = px[x, y]
            if r > 140 and g < 90 and b < 90:
                hits += 1
    return hits


def test_tree_png(tmp_path):
    rr = _render(TREE_MD, "tree", tmp_path)
    assert rr.png_path.is_file()
    assert rr.layout == "tree"
    assert rr.nodes == 6  # 根 + 2 分支 + 2 叶子 + 1 细节
    assert 400 <= rr.width <= 4000
    assert rr.height >= 150  # 紧凑布局，宽扁属正常
    with Image.open(rr.png_path) as im:
        im.load()
        assert _count_red(im) > 30  # 朱砂主题节点与连线存在
        # 白底：四角应为近白
        px = im.convert("RGB").load()
        w, h = im.size
        for corner in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]:
            r, g, b = px[corner]
            assert r > 235 and g > 235 and b > 235


def test_timeline_png(tmp_path):
    rr = _render("# T\n- 1789: 甲\n- 1790: 乙", "timeline", tmp_path)
    assert rr.layout == "timeline"
    assert rr.nodes == 3
    with Image.open(rr.png_path) as im:
        im.load()
        assert _count_red(im) > 10


def test_wide_image_scaled(tmp_path):
    md = (
        "# T"
        + "\n"
        + "\n".join(f"## 很长的分支名称{i} " + "描述" * 30 for i in range(6))
    )
    rr = _render(md, "tree", tmp_path, max_img_width=600)
    assert rr.width <= 600
