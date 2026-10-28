"""思维导图工具箱：llm_tool 自主出图 + 指令出图 + 文件留存与清理。"""

from __future__ import annotations

import asyncio
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Image, Plain
from astrbot.api.star import Context, Star, StarTools

from .core.fonts import FontManager
from .core.layout import build_layout
from .core.parser import (
    OutlineError,
    OutlineTooLargeError,
    detect_layout,
    parse_outline,
)
from .core.render import RenderResult, render_to_png
from .core.theme import get_theme

PLUGIN_NAME = "astrbot_plugin_mindmap"

DEFAULTS: dict = {
    "auto_send": True,
    "echo_outline": False,
    "retain_days": 7,
    "max_image_width": 4000,
    "max_nodes": 200,
    "max_node_chars": 200,
    "output_scale": 1,
    "enable_command": True,
}

_DATE_DIR_RE = re.compile(r"^\d{8}$")


class MindmapPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else (config or {})
        self.fm = FontManager()
        self._cleanup_task: asyncio.Task | None = None

    # ---------------- 配置 ----------------

    def _cfg(self, key: str):
        val = None
        try:
            val = self.config.get(key)  # type: ignore[union-attr]
        except AttributeError:
            val = None
        return DEFAULTS[key] if val is None else val

    def _data_root(self) -> Path:
        return StarTools.get_data_dir(PLUGIN_NAME) / "mindmap"

    # ---------------- 生命周期 ----------------

    async def initialize(self):
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def terminate(self):
        task = self._cleanup_task
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._cleanup_task = None

    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.to_thread(self.cleanup_old_images)
            except Exception:
                logger.exception("mindmap: 清理过期图片失败")
            await asyncio.sleep(6 * 3600)

    def cleanup_old_images(self) -> int:
        """删除超过 retain_days 的日期目录，返回删除数。"""
        root = self._data_root()
        if not root.is_dir():
            return 0
        deadline = datetime.now() - timedelta(days=int(self._cfg("retain_days")))
        removed = 0
        for entry in root.iterdir():
            if not entry.is_dir() or not _DATE_DIR_RE.match(entry.name):
                continue
            try:
                day = datetime.strptime(entry.name, "%Y%m%d")
            except ValueError:
                continue
            if day < deadline:
                shutil.rmtree(entry, ignore_errors=True)
                removed += 1
        return removed

    # ---------------- 渲染管线 ----------------

    def _render(self, outline: str, layout: str, theme_name: str = "") -> RenderResult:
        doc = parse_outline(
            outline,
            max_nodes=int(self._cfg("max_nodes")),
            max_node_chars=int(self._cfg("max_node_chars")),
        )
        kind = layout if layout in ("tree", "timeline") else detect_layout(doc)
        res = build_layout(doc.root, kind, self.fm)
        theme = get_theme(str(theme_name))
        day_dir = self._data_root() / datetime.now().strftime("%Y%m%d")
        out_path = day_dir / f"mindmap_{datetime.now().strftime('%H%M%S%f')}.png"
        return render_to_png(
            res,
            theme,
            self.fm,
            out_path,
            max_img_width=int(self._cfg("max_image_width")),
            output_scale=float(self._cfg("output_scale")),
        )

    # ---------------- LLM 工具 ----------------

    @filter.llm_tool(name="draw_mindmap")
    async def draw_mindmap(
        self,
        event: AstrMessageEvent,
        outline: str,
        layout: str = "auto",
        theme: str = "",
        send: bool = True,
    ) -> str:
        """根据大纲生成中文思维导图或时间线图（PNG）。

        大纲用 Markdown 标题（# ## ###）或 '-' 列表缩进表示层级。时间线布局节点写成「时间标签: 描述」，
        时间标签可省略。默认直接把图片发给用户；要嵌入 docx 等二次加工时传 send=False，
        此时返回文件路径，用文件工具读取该路径即可，无需向用户展示路径。

        Args:
            outline (str): 大纲文本。
            layout (str): 布局：'tree' 思维导图（默认）、'timeline' 时间线、'auto' 自动检测。
            theme (str): 配色主题，可选内置名（朱砂、靛蓝、松绿、琥珀、墨灰、黛紫）或 #RRGGBB 自定义主色；留空用默认主题。
            send (bool): 是否直接把图片发给用户（默认 true）。

        Returns:
            str: send=True 时返回发送状态标记；send=False 时为文件路径。
        """
        try:
            result = await asyncio.to_thread(self._render, outline, layout, theme)
        except OutlineTooLargeError as e:
            if e.nodes:
                return (
                    f"大纲共 {e.nodes} 个节点，超过 {self._cfg('max_nodes')} 的上限，未生成图片。"
                    "请精简：合并同类节点、减少层级，或拆成多张图分别绘制。"
                )
            return (
                f"大纲存在 {e.max_node_chars} 字的超长节点，超过单节点 {self._cfg('max_node_chars')} 字上限，未生成图片。"
                "请把长段拆成若干短节点。"
            )
        except OutlineError as e:
            return f"大纲解析失败：{e} 请修正后重试。"
        except Exception:
            logger.exception("mindmap: 渲染失败")
            return "思维导图生成失败：内部错误，请稍后重试。"

        if send:
            try:
                await event.send(MessageChain([Image(file=str(result.png_path))]))
            except Exception:
                logger.exception("mindmap: 发送图片失败")
                return f"图已生成但发送失败，文件 {result.png_path}"
            return "[图片已发送]"
        return str(result.png_path)

    # ---------------- 指令 ----------------

    @filter.command("mindmap")
    async def mindmap_command(self, event: AstrMessageEvent):
        """根据大纲生成思维导图。用法：/mindmap [--theme 主题] [timeline] <大纲文本>。"""
        if not self._cfg("enable_command"):
            return
        text = event.message_str or ""
        text = re.sub(r"^/?mindmap(@\S+)?\s*", "", text, flags=re.IGNORECASE).strip()
        layout = "auto"
        theme = ""
        while True:
            m = re.match(r"^--theme\s+(\S+)\s*", text, flags=re.IGNORECASE)
            if m:
                theme = theme or m.group(1)
                text = text[m.end() :]
                continue
            m = re.match(r"^timeline\s*", text, flags=re.IGNORECASE)
            if m and layout == "auto":
                layout = "timeline"
                text = text[m.end() :].strip()
                continue
            break
        if not text:
            yield event.chain_result(
                [
                    Plain(
                        "用法：/mindmap [--theme 主题] [timeline] <大纲>\n"
                        "主题：朱砂（默认）、靛蓝、松绿、琥珀、墨灰、黛紫，或 #RRGGBB 自定义\n"
                        "大纲示例（Markdown 标题）：\n"
                        "# 主题\n## 分支一\n- 要点\n## 分支二\n"
                        "或列表缩进：\n- 主题\n  - 分支\n    - 要点\n"
                        "时间线节点格式：1789: 三级会议召开……（时间标签可省略）"
                    )
                ]
            )
            return
        try:
            result = await asyncio.to_thread(self._render, text, layout, theme)
        except OutlineError as e:
            yield event.chain_result([Plain(f"生成失败：{e}")])
            return
        except Exception:
            logger.exception("mindmap: 渲染失败")
            yield event.chain_result([Plain("生成失败：内部错误。")])
            return
        chain: list = [Image(file=str(result.png_path))]
        if self._cfg("echo_outline"):
            chain.append(Plain(f"\n大纲：\n{text}"))
        yield event.chain_result(chain)
