"""布局几何断言：树状不重叠且右展，时间线交替有序。"""

from astrbot_plugin_mindmap.core.fonts import FontManager
from astrbot_plugin_mindmap.core.layout import Box, build_layout
from astrbot_plugin_mindmap.core.parser import parse_outline


def _boxes(b: Box):
    yield b
    for c in b.children:
        yield from _boxes(c)


def _tree_doc():
    return parse_outline("# 根\n## 甲\n- 甲一\n  - 细节\n- 甲二\n## 乙\n- 乙一\n- 乙二")


def test_tree_layout_geometry():
    fm = FontManager()
    doc = _tree_doc()
    res = build_layout(doc.root, "tree", fm)
    boxes = list(_boxes(res.root))
    assert res.width > 400 and res.height > 300
    # 同层兄弟垂直不重叠，且子节点在父右侧
    stack = [res.root]
    while stack:
        b = stack.pop()
        for c in b.children:
            assert c.x > b.x + b.w - 1
        stack.extend(b.children)
    # 叶子 yc 自上而下递增
    leaves = [b for b in boxes if not b.children]
    ycs = [b.yc for b in leaves]
    assert ycs == sorted(ycs)
    # 同层相邻不重叠
    seen: dict[int, list[Box]] = {}
    for b in boxes:
        seen.setdefault(b.depth, []).append(b)
    for depth, group in seen.items():
        group = sorted(group, key=lambda b: b.top)
        for a, c in zip(group, group[1:]):
            assert a.bottom <= c.top + 0.5, f"depth {depth} boxes overlap"


def test_timeline_layout_alternates():
    fm = FontManager()
    doc = parse_outline("# T\n- 1: 甲\n- 2: 乙\n- 3: 丙\n- 4: 丁")
    res = build_layout(doc.root, "timeline", fm)
    kids = res.root.children
    assert len(kids) == 4
    sides = [k.x < res.axis_x for k in kids]
    assert sides == [True, False, True, False]
    ycs = [k.yc for k in kids]
    assert ycs == sorted(ycs)
    for k in kids:
        assert k.label in {"1", "2", "3", "4"}
    # 画布宽度足够容纳最右节点
    assert res.width >= max(k.x + k.w for k in kids) + 39


def test_timeline_rejects_deep_nodes():
    """时间线只承载一层事件；深层节点显式拒绝而非静默丢弃。"""
    import pytest

    from astrbot_plugin_mindmap.core.parser import OutlineError

    fm = FontManager()
    doc = parse_outline("# T\n- 1789: 甲\n  - 深层细节")
    with pytest.raises(OutlineError, match="仅支持一层"):
        build_layout(doc.root, "timeline", fm)
