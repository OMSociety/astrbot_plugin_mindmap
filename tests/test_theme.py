"""主题测试：内置名解析、自定义 hex 派生、静默回退、极端色梯度。"""

from astrbot_plugin_mindmap.core.theme import (
    DEFAULT_THEME,
    THEMES,
    derive_theme,
    get_theme,
)

EXPECTED_NAMES = {"朱砂", "靛蓝", "松绿", "琥珀", "墨灰", "黛紫"}


def test_builtin_theme_registry():
    assert set(THEMES) == EXPECTED_NAMES
    assert DEFAULT_THEME == "朱砂"


def test_derive_keeps_root_color_and_white_background():
    t = derive_theme("#B41818")
    assert t.root_fill == "#B41818"
    assert t.bg == "#FFFFFF"
    assert t.text_on_dark == "#FFFFFF"


def test_derive_gradient_gets_lighter_down_the_levels():
    t = derive_theme("#B41818")

    def lightness(hex_color: str) -> int:
        return sum(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))

    assert lightness(t.branch_1) > lightness(t.root_fill)
    assert lightness(t.branch_2) > lightness(t.branch_1)
    assert lightness(t.branch_3) > lightness(t.branch_2)
    assert lightness(t.branch_3) < lightness(t.deep_fill)


def test_each_builtin_theme_resolves():
    for name in EXPECTED_NAMES:
        theme = get_theme(name)
        assert theme.root_fill == THEMES[name].upper()


def test_custom_hex_accepted():
    assert get_theme("#2E8B8B").root_fill == "#2E8B8B"


def test_unknown_name_falls_back_to_default():
    assert get_theme("不存在的主题") == get_theme(DEFAULT_THEME)


def test_invalid_hex_falls_back_to_default():
    assert get_theme("#GGGGGG") == get_theme(DEFAULT_THEME)
    assert get_theme("#12345") == get_theme(DEFAULT_THEME)


def test_empty_name_uses_default():
    assert get_theme("") == get_theme(DEFAULT_THEME)
    assert get_theme() == get_theme(DEFAULT_THEME)


def test_extreme_colors_still_produce_visible_gradient():
    for color in ("#F0F0F0", "#101010"):
        theme = derive_theme(color)
        assert theme.root_fill == color
        assert theme.branch_1 != theme.root_fill


def test_theme_is_immutable():
    theme = get_theme("朱砂")
    try:
        theme.root_fill = "#000000"  # type: ignore[misc]
    except AttributeError:
        return
    raise AssertionError("Theme 应为 frozen dataclass")
