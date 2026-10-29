"""字体管理：插件内置思源黑体优先，系统候选链降级，PIL 默认兜底并告警。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import ImageFont

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_BUNDLED_REGULAR = PLUGIN_ROOT / "res" / "fonts" / "SourceHanSansCN-Regular.otf"
_BUNDLED_BOLD = PLUGIN_ROOT / "res" / "fonts" / "SourceHanSansCN-Bold.otf"
_SYSTEM_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",  # 黑体
    "C:/Windows/Fonts/simsun.ttc",  # 宋体（兜底有字形）
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


class FontManager:
    """按字号缓存 ImageFont；优先插件内置思源黑体，缺失时降级系统字体。"""

    def __init__(self, on_warning: Callable[[str], None] | None = None) -> None:
        self._regular = self._pick(_BUNDLED_REGULAR)
        self._bold = self._pick(_BUNDLED_BOLD)
        self._cache: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}
        if on_warning is not None and (
            self._regular[1] != "bundled" or self._bold[1] != "bundled"
        ):
            on_warning(
                "mindmap: 插件内置字体缺失，已降级到 "
                f"{self._regular[0]}；中文可能显示为方框，"
                "建议补全 res/fonts/ 下的思源黑体文件。"
            )

    def _pick(self, bundled: Path) -> tuple[str, str]:
        if bundled.is_file():
            return (str(bundled), "bundled")
        for cand in _SYSTEM_CANDIDATES:
            if Path(cand).is_file():
                return (cand, "system")
        return ("", "default")

    def get(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = (size, bold)
        if key not in self._cache:
            path, kind = self._bold if bold else self._regular
            if kind == "default":
                self._cache[key] = ImageFont.load_default(size)
            else:
                self._cache[key] = ImageFont.truetype(path, size)
        return self._cache[key]
