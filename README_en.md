<p align="center"><a href="README.md">中文</a> | <strong>English</strong></p>

<div align="center">
  <img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_mindmap/main/logo.png" width="128" alt="Mindmap Toolbox Logo" />
  <h1>Mindmap Toolbox</h1>
  <p>An AstrBot plugin · render an outline into a mindmap / timeline and send it to the chat, fully local with zero browser dependency</p>
  <p>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/releases"><img src="https://img.shields.io/badge/version-v1.0.0-B41818" alt="Version" /></a>
    <a href="https://github.com/AstrBotDevs/AstrBot"><img src="https://img.shields.io/badge/AstrBot-plugin-5865F2" alt="AstrBot" /></a>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-green" alt="License" /></a>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/stargazers"><img src="https://img.shields.io/github/stars/OMSociety/astrbot_plugin_mindmap" alt="Stars" /></a>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/issues"><img src="https://img.shields.io/github/issues/OMSociety/astrbot_plugin_mindmap" alt="Issues" /></a>
  </p>
</div>

## Features

| Feature | Notes |
|---------|-------|
| **Tree mindmap** | Root on the left, horizontal branches, auto-derived tier colors |
| **Vertical timeline** | Central spine with alternating nodes, for historical narratives |
| **Six palettes** | Vermilion / Indigo / Pine / Amber / Slate / Violet, or any `#RRGGBB` |
| **Agent-driven** | Built-in LLM tool; the model reads the material and draws on its own |
| **Fully local** | Custom Pillow renderer, no browser, content never leaves the host |
| **File retention** | PNGs archived by day and auto-cleaned, reusable in docx |
| **HiDPI output** | 2x supersampling, sharp in QQ thumbnails and full view |

Six primary colors ship built in: vermilion (default, 朱砂), indigo, pine, amber, slate and violet. Pass any `#RRGGBB` primary color and the other five tiers are derived from it, with lightness steps that keep levels readable.

## Getting started

Install "思维导图工具箱" from the AstrBot plugin marketplace. No configuration needed.

Command usage:

```
/mindmap <outline>                   # default palette
/mindmap timeline <events>           # timeline
/mindmap --theme 靛蓝 <outline>      # built-in palette
/mindmap --theme #2E8B8B <outline>   # custom primary color
```

The `--theme` and `timeline` prefixes may appear in any order.

## Outline format

Markdown headings and list indentation can mix; two layouts are supported:

```markdown
# Topic
## First branch
- Node
  - Child
- Another node: a long description wraps automatically

# Timeline
- 1789: The Estates-General convenes
- 1793–1794: Jacobin dictatorship
```

> **Note:** at most 200 nodes and 200 characters per node; beyond that the call is rejected with a hint to trim. The full spec lives in the bundled skill `skills/mindmap/SKILL.md`.

## Configuration

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| auto_send | bool | true | Auto-send the PNG after a tool call |
| retention_days | int | 7 | Days PNGs are kept, 0 means forever |
| output_scale | float | 1 | Resolution multiplier, decimals allowed |

Quick config template:

```json
{
  "auto_send": true,
  "retention_days": 7,
  "output_scale": 1.5
}
```

## LLM tool

`draw_mindmap(outline, layout, theme, send)`:

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| outline | string | yes | Markdown outline |
| layout | string | no | `tree` / `timeline` / `auto` (default `auto`) |
| theme | string | no | Built-in palette name or `#RRGGBB`, default vermilion; invalid values fall back silently |
| send | bool | no | defaults to `auto_send`; `false` renders only and returns the absolute path |

Example conversation:

```
You: 帮我梳理一下康德的三大批判，画个思维导图
Bot: [mindmap PNG] 画好啦！
```

On platforms without rich-media support, `auto_send` is disabled automatically and the file path is returned for the host to pick up.

## Troubleshooting

> **Boxes instead of CJK:** the plugin ships Source Han Sans CN (res/fonts/), so this should not happen; if it does, verify the two otf files (about 33 MB total) are intact.

> **Not listed on the plugin page:** check the directory contains metadata.yaml, main.py, logo.png and _conf_schema.json; Launcher-managed instances need a full restart, source instances can set ASTRBOT_RELOAD=1 for hot reload.

> **Only a phrase, no image:** the outline exceeded the hard limits; trim it per the returned phrase and retry.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Credits

Font: Source Han Sans CN, SIL Open Font License 1.1 (see res/fonts/OFL.txt).

## License and author

AGPL-3.0 · OMSociety. The bundled font (Source Han Sans CN) stays under OFL 1.1.
