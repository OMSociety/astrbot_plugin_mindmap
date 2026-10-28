"""主题：主色派生六阶色板。内置主题用传统色名，也接受任意 #RRGGBB。

派生阶梯按朱砂手工精调板反推校准：分支层饱和度先降再提明度，
浅底压到接近白，文字色同色相压到深色端。
"""

from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    root_fill: str  # 根节点、标题条、连线主色
    branch_1: str  # 一级分支
    branch_2: str  # 二级分支
    branch_3: str  # 深层描边
    deep_fill: str  # 深层/时间线节点浅底
    bg: str
    text_on_dark: str  # 深底上的文字色
    text_on_light: str  # 浅底上的文字色


# 主题名 -> 主色
THEMES: dict[str, str] = {
    "朱砂": "#B41818",
    "靛蓝": "#1B4F8A",
    "松绿": "#1E6B52",
    "琥珀": "#B47A18",
    "墨灰": "#3A3F44",
    "黛紫": "#5B3A8E",
}

DEFAULT_THEME = "朱砂"

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def derive_theme(hex_color: str) -> Theme:
    """从主色派生六阶色板。"""
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    base_l = _clamp(lightness, 0.25, 0.55)  # 极浅/极深主色钳到可派生区间

    def shade(lightness: float, saturation: float) -> str:
        rr, gg, bb = colorsys.hls_to_rgb(hue, _clamp(lightness), _clamp(saturation))
        return "#{:02X}{:02X}{:02X}".format(int(rr * 255), int(gg * 255), int(bb * 255))

    return Theme(
        root_fill=hex_color.upper(),
        branch_1=shade(base_l + 0.11, saturation * 0.70),
        branch_2=shade(base_l + 0.23, saturation * 0.72),
        branch_3=shade(base_l + 0.36, saturation * 0.70),
        deep_fill=shade(0.94, saturation * 0.38),
        bg="#FFFFFF",
        text_on_dark="#FFFFFF",
        text_on_light=shade(0.27, saturation),
    )


def get_theme(name: str = "", default: str = DEFAULT_THEME) -> Theme:
    """解析主题：内置名或 #RRGGBB；无法识别时静默回退到 default。"""
    key = (name or "").strip()
    if key in THEMES:
        return derive_theme(THEMES[key])
    if _HEX_RE.match(key):
        return derive_theme(key)
    fallback = default if default in THEMES else DEFAULT_THEME
    return derive_theme(THEMES[fallback])
