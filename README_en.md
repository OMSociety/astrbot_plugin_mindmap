<p align="center"><a href="README.md">中文</a> · <strong>English</strong></p>

<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_mindmap/main/logo.png" width="120" alt="Mindmap Logo" />

# Mindmap Mind-map Toolkit

**Turn a Markdown outline into a mind map or timeline and send it straight to the chat** — Local rendering · Six palettes · CJK line wrapping · HiDPI output

[![Version](https://img.shields.io/github/v/tag/OMSociety/astrbot_plugin_mindmap?label=version&color=blue)](https://github.com/OMSociety/astrbot_plugin_mindmap/releases)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4.13-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_mindmap)](https://github.com/OMSociety/astrbot_plugin_mindmap/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_mindmap)](https://github.com/OMSociety/astrbot_plugin_mindmap/issues)

[Core features](#core-features) • [Overview](#overview) • [Getting started](#getting-started) • [Configuration](#configuration) • [LLM tool](#llm-tool) • [FAQ](#faq) • [Changelog](CHANGELOG.md)

</div>

---

## Core features

| Feature | Notes |
|---------|-------|
| **Tree mind map** | Root on the left, horizontal branches, tier colors derived automatically, long labels wrap |
| **Vertical timeline** | Central spine with alternating nodes; date-heavy outlines are detected automatically |
| **Six palettes** | Vermilion / Indigo / Pine / Amber / Slate / Violet, or any `#RRGGBB` primary color |
| **Agent-driven** | Built-in LLM tool and skill spec; the model reads the material, draws and posts on its own |
| **Fully local** | Custom Pillow layout and renderer, no browser, no remote rendering service |
| **CJK typesetting** | Ships Source Han Sans CN and wraps by glyph width — no tofu boxes, no clipping |
| **HiDPI and retention** | 1x base already equals the old 2x pixels, decimals allowed; PNGs archived by day and auto-cleaned |

---

## Overview

### Tree mind map

Feed a Markdown heading hierarchy or indented list and get a tree that grows left to right. Label width is measured from the actual text, so long sentences wrap into multiple lines.

### Vertical timeline

When most leaf nodes look like dates (`1789:`, `1949`), the outline is treated as a timeline: nodes alternate left and right along a central spine, suited to historical narratives and event sequences.

### Six palettes

Vermilion (default), Indigo, Pine, Amber, Slate and Violet ship built in; the other five tiers are derived from the primary color as a lightness ladder. Pass `#RRGGBB` for any custom primary color — extremes are clamped into a derivable range so levels stay readable.

### Agent-driven drawing

A bundled skill `mindmap` teaches the bot the outline format, size guidance, palette choice and sending rules. The bot calls `draw_mindmap` on its own during a walkthrough, so users never need to learn the command syntax.

### File retention and reuse

PNGs land in `data/plugin_data/astrbot_plugin_mindmap/mindmap/YYYYmmdd/` and are kept for 7 days by default. Passing `send=False` renders only and returns the path, handy for embedding into docx, PDF or other post-processing.

---

## Getting started

### Step 1: Install

AstrBot WebUI → Plugin marketplace → search for "思维导图工具箱"

> **Note:** the plugin reads `requirements.txt` and installs Pillow on install; no manual dependency setup.

### Step 2: Just ask

No configuration needed. Describe what you want and the bot decides whether to draw, and which layout:

```
User: Walk me through Kant's three critiques and draw a mind map
Bot: [mind map PNG] Done!

User: Draw the key turning points from the French Revolution to the Paris Commune as a timeline
Bot: [timeline PNG] Done — five nodes from 1789 to 1871.
```

### Step 3: Or use the command

```
/mindmap <outline>                   # default palette
/mindmap timeline <events>           # timeline
/mindmap --theme 靛蓝 <outline>      # built-in palette
/mindmap --theme #2E8B8B <outline>   # custom primary color
```

The `--theme` and `timeline` prefixes may appear in any order; an empty outline replies with usage help.

---

## Configuration

| Field | Type | Default | Notes |
|:------|:-----|:--------|:------|
| `auto_send` | bool | `true` | Auto-send the image when a tool call leaves `send` unset |
| `echo_outline` | bool | `false` | Echo the original outline after a command-generated image |
| `retain_days` | int | `7` | Days PNGs are kept before automatic cleanup |
| `max_image_width` | int | `4000` | Maximum output width in pixels, downscaled proportionally beyond |
| `max_nodes` | int | `200` | Hard node limit; the call is rejected beyond it |
| `max_node_chars` | int | `200` | Hard per-node character limit; rejected, never silently truncated |
| `output_scale` | float | `1` | Resolution multiplier, decimals allowed; bounded by `max_image_width` |
| `enable_command` | bool | `true` | Enable the `/mindmap` command |

### Quick config template

Fill it in the WebUI panel, or follow this structure (`data/config/astrbot_plugin_mindmap_config.json`):

```json
{
  "auto_send": true,
  "echo_outline": false,
  "retain_days": 7,
  "max_image_width": 4000,
  "max_nodes": 200,
  "max_node_chars": 200,
  "output_scale": 1,
  "enable_command": true
}
```

---

## LLM tool

The plugin registers one LLM tool; the model decides when to call it, so natural language is enough:

```
User: Draw the structure of this material
    # Weber's typology of authority
    ## Traditional authority
    - Gerontocracy and patrimonialism
    ## Charismatic authority
    - Prophets and the extraordinary qualities of leaders
    ## Legal-rational authority
    - Bureaucracy and formal rational law
Bot: [mind map PNG] Done!
```

### draw_mindmap

Render a Chinese mind map or timeline from an outline (PNG).

| Parameter | Type | Required | Notes |
|:----------|:-----|:--------:|:------|
| `outline` | string | yes | Markdown outline; `#` headings or `-` list indentation for levels |
| `layout` | string | no | `tree` mind map / `timeline` / `auto` detection (default) |
| `theme` | string | no | Built-in palette name or `#RRGGBB`; empty uses the default vermilion, invalid values fall back silently |
| `send` | bool | no | Post the image directly, default `true`; `false` renders only and returns the path |

> **Note:** with `send=False` the tool returns a file path for a file tool to read and embed into docx and similar documents — never read that path out loud to the user.

Size guidance: at most 4 levels, 6 children per branch, 60 nodes in total, 40 characters per node. Exceeding a hard limit returns a fixed phrase asking for trimming; content is never silently dropped.

---

## FAQ

### Q1: Is any configuration required?

No. Install and it works; every field has a sensible default.

### Q2: Which platforms are supported?

Any platform that accepts image messages (QQ, Telegram, Discord and others). If sending fails, the tool returns the generated file path so the host or the user can pick it up.

### Q3: Where are the images stored, and do they pile up?

Under `data/plugin_data/astrbot_plugin_mindmap/mindmap/YYYYmmdd/`, one directory per day; anything older than `retain_days` (7 by default) is removed, with a cleanup every six hours.

### Q4: What if the outline is too large?

Trim per the returned phrase: merge sibling nodes, reduce depth, or split into several images. Hard limits are 200 nodes, 200 characters per node and 8 levels.

### Q5: Why not mermaid or markmap?

Those rely on browser rendering or do not wrap Chinese text. This plugin uses a custom Pillow layout and line breaker: fully local, no browser, still sharp in chat thumbnails.

### Q6: Can the result go into a docx?

Yes. Call with `send=False`, then read the returned path with a file tool and embed it.

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
