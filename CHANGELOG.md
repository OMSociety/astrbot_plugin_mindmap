# Changelog

本项目的更改记录在此文件。

All notable changes to this project are documented in this file.

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-30

### 新增

- 新增 `draw_table` 工具，将标准 Markdown 表格渲染为带主题配色的 PNG，支持自动列宽与中文折行。
- 新增 `draw_flowchart` 工具，支持纵向或横向绘制顺序、判断分支与汇合关系，并校验回环、跨层连线与不可达节点。
- 思维导图、时间线、表格与流程图共用主题、高清输出与文件留存机制；`auto_send` 可控制未指定 `send` 时的默认发送行为。

### 移除

- 移除 `/mindmap` 手工指令，图表统一通过 LLM 工具生成。
- 移除指令专用的 `echo_outline` 与 `enable_command` 配置项，宿主重载时会清理这两个旧配置键。

### Added

- Added `draw_table` to render standard Markdown tables as themed PNGs with automatic column widths and CJK line wrapping.
- Added `draw_flowchart` for vertical or horizontal sequences, decision branches and merges, with validation for cycles, cross-level edges and unreachable nodes.
- Mind maps, timelines, tables and flowcharts now share palettes, high-resolution output and file retention; `auto_send` controls delivery when `send` is unset.

### Removed

- Removed the `/mindmap` manual command; diagrams are generated through LLM tools.
- Removed the command-specific `echo_outline` and `enable_command` fields; the host deletes these legacy keys when reloading the configuration.
