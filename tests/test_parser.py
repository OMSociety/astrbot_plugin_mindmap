"""大纲解析器测试：标题吸收、自由文本主题、缩进、续行、超限、布局检测。"""

import pytest

from astrbot_plugin_mindmap.core.parser import (
    OutlineError,
    OutlineTooLargeError,
    detect_layout,
    parse_outline,
    split_label,
)


def test_heading_absorbed_as_root():
    doc = parse_outline("# 主题\n## 分支\n- 要点\n  - 细节\n## 分支二\n- 要点")
    top = doc.root
    assert top.depth == 0 and top.text == "主题"
    assert [c.text for c in top.children] == ["分支", "分支二"]
    assert top.children[0].depth == 1
    leaf = top.children[0].children[0]
    assert leaf.text == "要点" and leaf.depth == 2
    assert leaf.children[0].depth == 3


def test_free_text_title():
    doc = parse_outline("主题\n- 分支\n  - 要点\n- 分支二")
    assert doc.root.depth == 0 and doc.root.text == "主题"
    assert [c.text for c in doc.root.children] == ["分支", "分支二"]
    assert doc.root.children[0].children[0].text == "要点"


def test_continuation_line():
    doc = parse_outline("# 主题\n- 节点\n  续行文字")
    node = doc.root.children[0]
    assert "续行文字" in node.text


def test_empty_raises():
    with pytest.raises(OutlineError):
        parse_outline("   \n\n")


def test_bad_indent_reports_line():
    with pytest.raises(OutlineError) as ei:
        parse_outline("- A\n   - B")
    assert "第 2 行" in str(ei.value)


def test_too_many_nodes():
    md = "\n".join(f"- 节点{i}" for i in range(300))
    with pytest.raises(OutlineTooLargeError) as ei:
        parse_outline(md, max_nodes=200)
    assert ei.value.nodes > 200


def test_too_long_node():
    md = "# T\n- " + "长" * 500
    with pytest.raises(OutlineTooLargeError) as ei:
        parse_outline(md, max_node_chars=200)
    assert ei.value.max_node_chars > 200


def test_detect_layout_timeline():
    md = "# T\n- 1789: 甲\n- 1790: 乙\n- 无标签的丙"
    assert detect_layout(parse_outline(md)) == "timeline"


def test_detect_layout_tree():
    md = "# T\n## 甲\n- 1\n## 乙\n- 2"
    assert detect_layout(parse_outline(md)) == "tree"


def test_split_label():
    assert split_label("1789: 事件") == ("1789", "事件")
    assert split_label("1789：事件") == ("1789", "事件")
    assert split_label("无标签描述") == ("", "无标签描述")
