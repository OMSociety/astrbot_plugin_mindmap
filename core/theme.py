"""主题：社科红全红系单色六阶（源自中国社会科学院大学校徽实测主色 #B41818）。"""

from __future__ import annotations

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


THEME_SOCRED = Theme(
    root_fill="#B41818",
    branch_1="#C63E3E",
    branch_2="#D46B6B",
    branch_3="#E2A0A0",
    deep_fill="#F7E8E8",
    bg="#FFFFFF",
    text_on_dark="#FFFFFF",
    text_on_light="#7A1010",
)


def get_theme(name: str = "socred") -> Theme:
    """返回主题；当前仅内置 socred，未知名静默回退到它。"""
    del name
    return THEME_SOCRED
