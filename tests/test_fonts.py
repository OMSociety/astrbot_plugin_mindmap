"""字体管理的告警回调与宿主日志接线。"""

from astrbot_plugin_mindmap.core import fonts
from astrbot_plugin_mindmap.core.fonts import FontManager


def test_font_manager_reports_fallback_through_callback(monkeypatch):
    messages = []
    monkeypatch.setattr(fonts, "_SYSTEM_CANDIDATES", [])
    monkeypatch.setattr(fonts, "_BUNDLED_REGULAR", fonts.Path("missing-regular.otf"))

    FontManager(on_warning=messages.append)

    assert len(messages) == 1
    assert "字体缺失" in messages[0]


def test_font_manager_does_not_require_host_logging(monkeypatch):
    monkeypatch.setattr(fonts, "_SYSTEM_CANDIDATES", [])

    manager = FontManager()

    assert manager.get(32) is not None


def test_plugin_uses_astrbot_logger_for_font_warning(monkeypatch):
    import astrbot_plugin_mindmap.main as main

    captured = {}
    monkeypatch.setattr(
        main.FontManager,
        "__init__",
        lambda self, **kwargs: captured.update(kwargs),
    )
    main.MindmapPlugin(context=None, config={})

    assert captured["on_warning"].__name__ == "warning"
