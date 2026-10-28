"""指令层测试：指令名不污染大纲主题；send 行为。"""

import re
from pathlib import Path

import pytest


def test_command_prefix_regex():
    pat = r"^/?mindmap(@\S+)?\s*"
    assert re.sub(pat, "", "mindmap # 物权法", flags=re.IGNORECASE) == "# 物权法"
    assert re.sub(pat, "", "/mindmap # 物权法", flags=re.IGNORECASE) == "# 物权法"
    assert re.sub(pat, "", "/mindmap@bot # 物权法", flags=re.IGNORECASE) == "# 物权法"


class _FakeEvent:
    def __init__(self, message_str: str) -> None:
        self.message_str = message_str

    def chain_result(self, chain):
        return type("Result", (), {"chain": chain})()


@pytest.mark.asyncio
async def test_command_renders_clean_title(tmp_path, monkeypatch):
    from astrbot_plugin_mindmap.main import MindmapPlugin

    star = MindmapPlugin(context=None, config={})
    monkeypatch.setattr(star, "_data_root", lambda: tmp_path / "mindmap")
    ev = _FakeEvent("/mindmap # 物权法\n## 章节\n- 要点")
    results = [r async for r in star.mindmap_command(ev)]
    assert results, "指令没有产出"
    img = results[-1].chain[0]
    assert Path(img.file).is_file(), f"图片不存在: {img.file}"


@pytest.mark.asyncio
async def test_command_theme_prefix_and_order(tmp_path, monkeypatch):
    import astrbot_plugin_mindmap.main as m

    calls = []
    real_get_theme = m.get_theme

    def spy(name=""):
        calls.append(name)
        return real_get_theme(name)

    monkeypatch.setattr(m, "get_theme", spy)
    star = m.MindmapPlugin(context=None, config={})
    monkeypatch.setattr(star, "_data_root", lambda: tmp_path / "mindmap")

    for text in (
        "/mindmap --theme 靛蓝 # 主题\n- 要点",
        "/mindmap --theme #2E8B8B timeline 1789: 事件",
        "/mindmap timeline --theme 松绿 1789: 事件",
    ):
        ev = _FakeEvent(text)
        results = [r async for r in star.mindmap_command(ev)]
        assert results, f"指令没有产出: {text}"
        assert Path(results[-1].chain[0].file).is_file()

    assert calls == ["靛蓝", "#2E8B8B", "松绿"]
