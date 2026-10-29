<p align="center"><a href="README.md">中文</a> · <strong>English</strong></p>

<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_mindmap/main/logo.png" width="120" alt="Mindmap Logo" />

# Mindmap Diagram Toolkit

**Render material as mind maps, timelines, tables, or basic flowcharts and send it straight to the chat** — Local rendering · Six palettes · CJK line wrapping · HiDPI output

[![Version](https://img.shields.io/github/v/tag/OMSociety/astrbot_plugin_mindmap?label=version&color=blue)](https://github.com/OMSociety/astrbot_plugin_mindmap/releases)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4.13-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_mindmap)](https://github.com/OMSociety/astrbot_plugin_mindmap/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_mindmap)](https://github.com/OMSociety/astrbot_plugin_mindmap/issues)

</div>

---

## Core features

| Feature | Notes |
|---------|-------|
| **Mind maps and timelines** | Trees grow from left to right; timelines alternate along a central spine; long labels wrap |
| **Markdown tables** | Standard Markdown input with a separate title parameter for comparisons and structured data |
| **Basic flowcharts** | Vertical or horizontal start, process, decision and end nodes, with sequences, branches and merges |
| **Six palettes** | Vermilion / Indigo / Pine / Amber / Slate / Violet, or any `#RRGGBB` primary color |
| **Agent-driven** | Three LLM tools and a bundled skill; the model reads the material, selects a diagram and posts it |
| **Fully local** | Custom Pillow layout and renderer; no browser, Graphviz or remote rendering service |
| **CJK typesetting** | Ships Source Han Sans CN and wraps by glyph width — no tofu boxes, no clipping |
| **HiDPI and retention** | 1x base already equals the old 2x pixels, decimals allowed; PNGs archived by day and auto-cleaned |

---

## Overview

### Mind maps and timelines

Feed a Markdown heading hierarchy or indented list and get a tree that grows left to right. When most leaf nodes look like dates (`1789:`, `1949`), the outline can be treated as a timeline for historical narratives and event sequences.

### Tables

`draw_table` accepts a standard Markdown table, with its title supplied separately through `title`. It supports up to 8 columns and 50 data rows, with at most 200 characters per cell. Merged cells and rich text are not supported.

### Basic flowcharts

`draw_flowchart` renders node declarations and directed edges as a flowchart. The default direction is vertical, with horizontal as an alternative. It supports `start`, `process`, `decision` and `end` nodes, plus sequences, branches and merges, for up to 30 nodes.

Flowcharts must describe an unambiguous one-way process. Cycles, cross-level edges, unreachable nodes and ambiguous input are rejected rather than completed by guesswork.

### Six palettes

Vermilion (default), Indigo, Pine, Amber, Slate and Violet ship built in; the other five tiers are derived from the primary color as a lightness ladder. Pass `#RRGGBB` for any custom primary color — extremes are clamped into a derivable range so levels stay readable.

### Agent-driven drawing

The bundled `mindmap` skill teaches the bot to select a diagram type, structure input, control size, choose palettes and follow sending rules. It calls the appropriate tool during a walkthrough, so natural-language requests are enough.

### File retention and reuse

PNGs land in `data/plugin_data/mindmap/mindmap/YYYYmmdd/` and are kept for 7 days by default. Passing `send=False` renders only and returns the path, handy for embedding into docx, PDF or other post-processing.

---

## Getting started

### Step 1: Install

AstrBot WebUI → Plugin marketplace → search for "思维导图工具箱"

> **Note:** the plugin reads `requirements.txt` and installs Pillow on install; no manual dependency setup.

### Step 2: Just ask

No configuration needed. Describe what you want and the bot decides whether to draw, and which diagram type to use:

```text
User: What questions do Kant's three critiques address?
Bot: The three critiques examine the faculties of knowledge, practice and judgment.
[comparison table of the three critiques PNG]
Together, they form the interconnected project of critical philosophy.

User: Turn this material-handling procedure into a flowchart
Bot: Material handling can be divided into completeness checks, concept extraction and system formation.
[material-handling flowchart PNG]
Both supplementary material and direct concept extraction ultimately lead to the same endpoint.
```

---

## Configuration

| Field | Type | Default | Notes |
|:------|:-----|:--------|:------|
| `auto_send` | bool | `true` | Auto-send the image when a tool call leaves `send` unset |
| `retain_days` | int | `7` | Days PNGs are kept before automatic cleanup |
| `max_image_width` | int | `4000` | Maximum output width in pixels, downscaled proportionally beyond |
| `max_nodes` | int | `200` | Hard outline node limit; the call is rejected beyond it |
| `max_node_chars` | int | `200` | Hard per-node character limit; rejected, never silently truncated |
| `output_scale` | float | `1` | Resolution multiplier, decimals allowed; bounded by `max_image_width` |

### Quick config template

Fill it in the WebUI panel, or follow this structure (`data/config/mindmap_config.json`):

```json
{
  "auto_send": true,
  "retain_days": 7,
  "max_image_width": 4000,
  "max_nodes": 200,
  "max_node_chars": 200,
  "output_scale": 1
}
```

---

## LLM tools

The plugin registers three tools: `draw_mindmap`, `draw_table` and `draw_flowchart`. The model decides when to call them, so natural language is enough.

### draw_mindmap

Render a Chinese mind map or timeline from an outline (PNG).

| Parameter | Type | Required | Notes |
|:----------|:-----|:--------:|:------|
| `outline` | string | yes | Markdown outline; `#` headings or `-` list indentation for levels |
| `layout` | string | no | `tree` mind map / `timeline` / `auto` detection (default) |
| `theme` | string | no | Built-in palette name or `#RRGGBB`; empty uses the default vermilion, invalid values fall back silently |
| `send` | bool | no | Post the image directly, default `true`; `false` renders only and returns the path |

Size guidance: at most 4 levels, 6 children per branch, 60 nodes in total, 40 characters per node. Hard limits are 200 nodes, 200 characters per node and 8 levels. Oversized input is rejected rather than silently truncated.

### draw_table

Render a standard Markdown table as PNG. Supply the table title through `title`, not inside `markdown`.

| Parameter | Type | Required | Notes |
|:----------|:-----|:--------:|:------|
| `markdown` | string | yes | Standard Markdown table with a header, separator and data rows |
| `title` | string | no | Table title, up to 80 characters; long titles wrap |
| `theme` | string | no | Built-in palette name or `#RRGGBB`; empty uses the default palette |
| `send` | bool | no | Post the image directly, default `true`; `false` renders only and returns the path |

Supports up to 8 columns and 50 data rows, with at most 200 characters per cell. Cells contain plain text; merged cells and rich text are not supported.

```text
draw_table(markdown="| Critique | Central question |\n| --- | --- |\n| Critique of Pure Reason | What can I know? |\n| Critique of Practical Reason | What ought I to do? |", title="Kant's critical philosophy", theme="朱砂", send=True)
```

### draw_flowchart

Render node declarations and directed edges as a basic flowchart (PNG).

| Parameter | Type | Required | Notes |
|:----------|:-----|:--------:|:------|
| `spec` | string | yes | Flow definition with an optional `#` title (up to 80 characters), node declarations and directed edges |
| `direction` | string | no | `vertical` (default) / `horizontal` |
| `theme` | string | no | Built-in palette name or `#RRGGBB`; empty uses the default palette |
| `send` | bool | no | Post the image directly, default `true`; `false` renders only and returns the path |

Declare nodes as `nodeID [type] node text`. A node ID must begin with an ASCII letter, followed only by ASCII letters, digits, underscores or hyphens. The type is optional and defaults to `process`. An optional `# Title` may appear on the first line; this is where the flowchart title is set. Write edges as `source -> target`, adding a branch label after an English or Chinese colon, such as `check -> process: yes`.

Supported node types are `start`, `process`, `decision` and `end`, with sequences, branches and merges. The single entry uses `start`, every terminal uses `end`, and intermediate nodes cannot be left at a dead end. The limit is 30 nodes. Cycles, cross-level edges, unreachable nodes and ambiguous input are rejected.

```text
draw_flowchart(spec="# Material handling\nstart [start] Receive material\ncheck [decision] Complete?\nprocess [process] Extract concepts\nsupplement [process] Supplement material\ndone [end] Form a system\nstart -> check\ncheck -> process: yes\ncheck -> supplement: no\nprocess -> done\nsupplement -> done", direction="vertical", theme="朱砂", send=True)
```

> **Note:** all three tools handle `send` the same way. With `send=False`, the returned file path is for a file tool to read and embed into docx and similar documents — never read that path out loud to the user.

---

## FAQ

### Q1: Is any configuration required?

No. Install and it works; every field has a sensible default.

### Q2: Which platforms are supported?

Any platform that accepts image messages (QQ, Telegram, Discord and others). If sending fails, the tool returns the generated file path so the host or the user can pick it up.

### Q3: Where are the images stored, and do they pile up?

Under `data/plugin_data/mindmap/mindmap/YYYYmmdd/`, one directory per day; anything older than `retain_days` (7 by default) is removed, with a cleanup every six hours.

### Q4: What if the input is too large to draw?

For mind maps, merge sibling nodes, reduce depth or split the outline into several images. For tables, split columns or draw batches. For flowcharts, use several subprocesses with clear boundaries. Oversized content is never silently truncated.

### Q5: Why not Mermaid, Markmap or Graphviz?

The plugin uses a custom Pillow layout and line breaker: fully local, with no browser or Graphviz dependency, and still sharp in chat thumbnails.

### Q6: Can the result go into a docx?

Yes. Call any tool with `send=False`, then read the returned path with a file tool and embed it.

---

## Changelog

> **[View the changelog →](CHANGELOG.md)**

## Credits

If this plugin helps you, a star is welcome; issues and pull requests are more than welcome at [Issues](https://github.com/OMSociety/astrbot_plugin_mindmap/issues) and [Pull requests](https://github.com/OMSociety/astrbot_plugin_mindmap/pulls).

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — open-source chatbot framework
- [Source Han Sans](https://github.com/adobe-fonts/source-han-sans) — SIL Open Font License 1.1, see `res/fonts/OFL.txt`

## License and author

Released under **AGPL-3.0**.

[@OMSociety](https://github.com/OMSociety)
