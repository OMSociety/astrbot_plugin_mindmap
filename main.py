"""思维导图工具箱：大纲、表格与基础流程图的 LLM 工具及图片留存。"""

from __future__ import annotations

import asyncio
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, StarTools

from .core.flowchart import FlowchartError, parse_flowchart, render_flowchart_png
from .core.fonts import FontManager
from .core.layout import build_layout
from .core.parser import (
    OutlineError,
    OutlineTooLargeError,
    detect_layout,
    parse_outline,
)
from .core.render import RenderResult, render_to_png
from .core.table import (
    TableError,
    parse_table,
    render_table_png,
    validate_table_title,
)
from .core.theme import get_theme

PLUGIN_NAME = "mindmap"

DEFAULTS: dict = {
    "auto_send": True,
    "retain_days": 7,
    "max_image_width": 4000,
    "max_nodes": 200,
    "max_node_chars": 200,
    "output_scale": 1,
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

    # ---------------- 渲染与发送 ----------------

    def _render_mindmap(
        self, outline: str, layout: str, theme_name: str
    ) -> RenderResult:
        doc = parse_outline(
            outline,
            max_nodes=int(self._cfg("max_nodes")),
            max_node_chars=int(self._cfg("max_node_chars")),
        )
        kind = layout if layout in ("tree", "timeline") else detect_layout(doc)
        res = build_layout(doc.root, kind, self.fm)
        return self._save_render(res, "mindmap", theme_name, render_to_png)

    def _render_table(self, markdown: str, title: str, theme_name: str) -> RenderResult:
        doc = parse_table(markdown)
        doc.title = validate_table_title(title)
        return self._save_render(doc, "table", theme_name, render_table_png)

    def _render_flowchart(
        self, spec: str, direction: str, theme_name: str
    ) -> RenderResult:
        doc = parse_flowchart(spec)
        return self._save_render(
            doc, "flowchart", theme_name, render_flowchart_png, direction
        )

    def _save_render(
        self,
        document,
        prefix: str,
        theme_name: str,
        renderer: Callable,
        *args,
    ) -> RenderResult:
        day_dir = self._data_root() / datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%H%M%S%f")
        out_path = day_dir / f"{prefix}_{timestamp}.png"
        return renderer(
            document,
            *args,
            get_theme(str(theme_name)),
            self.fm,
            out_path,
            max_img_width=int(self._cfg("max_image_width")),
            output_scale=float(self._cfg("output_scale")),
        )

    async def _deliver(
        self, event: AstrMessageEvent, result: RenderResult, send: bool | None
    ) -> str:
        should_send = bool(self._cfg("auto_send")) if send is None else send
        if not should_send:
            return str(result.png_path)
        try:
            await event.send(MessageChain([Image(file=str(result.png_path))]))
        except Exception:
            logger.exception("mindmap: 发送图片失败")
            return f"图已生成但发送失败，文件 {result.png_path}"
        return "[图片已发送]"

    # ---------------- LLM 工具 ----------------

    @filter.llm_tool(name="draw_mindmap")
    async def draw_mindmap(
        self,
        event: AstrMessageEvent,
        outline: str,
        layout: str = "auto",
        theme: str = "",
        send: bool | None = None,
    ) -> str:
        """根据大纲生成中文思维导图或时间线图（PNG）。

        大纲用 Markdown 标题（# ## ###）或 '-' 列表缩进表示层级。时间线布局节点写成「时间标签: 描述」。
        要嵌入 docx 等二次加工时传 send=False，返回文件路径供文件工具读取。

        Args:
            outline (str): 大纲文本。
            layout (str): 布局：'tree' 思维导图、'timeline' 时间线、'auto' 自动检测。
            theme (str): 内置主题名或 #RRGGBB 自定义主色；留空使用默认主题。
            send (bool): 是否直接把图片发给用户。

        Returns:
            str: 发图状态标记，或供二次加工读取的文件路径。
        """
        try:
            result = await asyncio.to_thread(
                self._render_mindmap, outline, layout, theme
            )
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
            logger.exception("mindmap: 思维导图渲染失败")
            return "思维导图生成失败：内部错误，请稍后重试。"
        return await self._deliver(event, result, send)

    @filter.llm_tool(name="draw_table")
    async def draw_table(
        self,
        event: AstrMessageEvent,
        markdown: str,
        title: str = "",
        theme: str = "",
        send: bool | None = None,
    ) -> str:
        """把标准 Markdown 表格绘制成中文表格图片（PNG）。

        表格需含表头与分隔行；标题通过 title 单独传入。要嵌入文档时传 send=False。

        Args:
            markdown (str): 标准 Markdown 表格，最多 8 列、50 行数据。
            title (str): 显示在表格上方的标题，最多 80 字，超宽自动折行。
            theme (str): 内置主题名或 #RRGGBB 自定义主色。
            send (bool): 是否直接把图片发给用户。

        Returns:
            str: 发图状态标记，或供二次加工读取的文件路径。
        """
        try:
            result = await asyncio.to_thread(self._render_table, markdown, title, theme)
        except TableError as e:
            return f"表格生成失败：{e}"
        except Exception:
            logger.exception("mindmap: 表格渲染失败")
            return "表格生成失败：内部错误，请稍后重试。"
        return await self._deliver(event, result, send)

    @filter.llm_tool(name="draw_flowchart")
    async def draw_flowchart(
        self,
        event: AstrMessageEvent,
        spec: str,
        direction: str = "vertical",
        theme: str = "",
        send: bool | None = None,
    ) -> str:
        """把节点与箭头声明绘制成基础流程图（PNG），支持顺序、判断分支与汇合。

        首行可用 '# 标题'；节点写成 'id [process] 内容'，类型可选 start、process、decision、end；
        连线写成 '起点 -> 终点: 条件'。以 start 节点为唯一入口、end 节点收尾，
        所有节点连成一个无回环、逐层推进的流程。
        要嵌入文档时传 send=False。

        Args:
            spec (str): 流程声明，最多 30 个节点。
            direction (str): 布局方向：'vertical' 纵向或 'horizontal' 横向。
            theme (str): 内置主题名或 #RRGGBB 自定义主色。
            send (bool): 是否直接把图片发给用户。

        Returns:
            str: 发图状态标记，或供二次加工读取的文件路径。
        """
        try:
            result = await asyncio.to_thread(
                self._render_flowchart, spec, direction, theme
            )
        except FlowchartError as e:
            return f"流程图生成失败：{e}"
        except Exception:
            logger.exception("mindmap: 流程图渲染失败")
            return "流程图生成失败：内部错误，请稍后重试。"
        return await self._deliver(event, result, send)
