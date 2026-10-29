"""LLM 工具层：三类图表的真实出图、发送状态与输入错误反馈。"""

from pathlib import Path

import pytest


class _FakeEvent:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, chain) -> None:
        self.sent.append(chain)


@pytest.fixture
def star(tmp_path, monkeypatch):
    from astrbot_plugin_mindmap.main import MindmapPlugin

    plugin = MindmapPlugin(context=None, config={})
    monkeypatch.setattr(plugin, "_data_root", lambda: tmp_path / "charts")
    return plugin


@pytest.mark.asyncio
async def test_mindmap_tool_sends_image(star):
    event = _FakeEvent()
    result = await star.draw_mindmap(event, "# 主题\n- 分支")

    assert result == "[图片已发送]"
    assert len(event.sent) == 1
    assert Path(event.sent[0].chain[0].file).is_file()


@pytest.mark.asyncio
async def test_table_tool_sends_image_and_returns_path_when_disabled(star):
    markdown = "| 批判 | 问题 |\n| --- | --- |\n| 纯粹理性批判 | 我能知道什么 |"
    sent_event = _FakeEvent()
    sent_result = await star.draw_table(sent_event, markdown, title="三大批判")

    assert sent_result == "[图片已发送]"
    assert Path(sent_event.sent[0].chain[0].file).name.startswith("table_")

    path = await star.draw_table(_FakeEvent(), markdown, send=False)
    assert Path(path).is_file()


@pytest.mark.asyncio
async def test_flowchart_tool_supports_both_delivery_modes(star):
    spec = "start [start] 开始\nfinish [end] 完成\nstart -> finish"
    event = _FakeEvent()
    result = await star.draw_flowchart(event, spec, direction="horizontal")

    assert result == "[图片已发送]"
    assert Path(event.sent[0].chain[0].file).name.startswith("flowchart_")

    path = await star.draw_flowchart(_FakeEvent(), spec, send=False)
    assert Path(path).is_file()


@pytest.mark.asyncio
async def test_auto_send_controls_only_unset_send(star):
    star.config["auto_send"] = False
    path = await star.draw_table(_FakeEvent(), "| A |\n| --- |\n| 甲 |", title="测试")
    assert Path(path).is_file()

    event = _FakeEvent()
    result = await star.draw_table(
        event, "| A |\n| --- |\n| 甲 |", title="测试", send=True
    )
    assert result == "[图片已发送]"
    assert len(event.sent) == 1


@pytest.mark.asyncio
async def test_tools_return_specific_input_errors(star):
    table_error = await star.draw_table(_FakeEvent(), "不是表格")
    flow_error = await star.draw_flowchart(
        _FakeEvent(), "a [start] 开始\nb [end] 结束\na -> b\nb -> a"
    )

    assert table_error.startswith("表格生成失败：")
    assert flow_error.startswith("流程图生成失败：")
    assert "回环" in flow_error


def test_plugin_registers_no_command_handlers():
    from astrbot_plugin_mindmap.main import MindmapPlugin

    assert not hasattr(MindmapPlugin, "mindmap_command")
    assert hasattr(MindmapPlugin, "draw_table")
    assert hasattr(MindmapPlugin, "draw_flowchart")
