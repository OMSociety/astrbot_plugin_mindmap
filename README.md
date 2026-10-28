<p align="center"><strong>中文</strong> · <a href="README_en.md">English</a></p>

<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_mindmap/main/logo.png" width="120" alt="Mindmap Logo" />

# Mindmap 思维导图工具箱

**把 Markdown 大纲渲染成思维导图 / 时间线，直接发到群里** —— 本地渲染 · 六套配色 · 中文自动折行 · 高清输出

[![Version](https://img.shields.io/github/v/tag/OMSociety/astrbot_plugin_mindmap?label=version&color=blue)](https://github.com/OMSociety/astrbot_plugin_mindmap/releases)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A5v4.13-green.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OMSociety/astrbot_plugin_mindmap)](https://github.com/OMSociety/astrbot_plugin_mindmap/stargazers)
[![Issues](https://img.shields.io/github/issues/OMSociety/astrbot_plugin_mindmap)](https://github.com/OMSociety/astrbot_plugin_mindmap/issues)

[核心特性](#核心特性) • [功能概览](#功能概览) • [快速开始](#快速开始) • [配置项说明](#配置项说明) • [LLM 可调用工具](#llm-可调用工具) • [常见问题](#常见问题) • [更新日志](CHANGELOG.md)

</div>

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **树状思维导图** | 根节点在左、水平展开，层级配色自动派生，长文本自动折行 |
| **竖轴时间线** | 中央竖轴、节点左右交替，带日期的大纲自动识别为时间线 |
| **六套配色** | 朱砂 / 靛蓝 / 松绿 / 琥珀 / 墨灰 / 黛紫，也可传 `#RRGGBB` 自定义主色 |
| **Agent 自主出图** | 内置 LLM 工具与技能规范，bot 读完材料自己决定画图并发到群里 |
| **全程本地** | Pillow 自研布局渲染，不调浏览器、不调远程渲染服务，内容不出本机 |
| **中文排版** | 自带思源黑体，节点按字符宽度折行，不出现方框与截断 |
| **高清与留存** | 默认 1x 基准即旧版 2x 像素、可调小数倍数；PNG 按日归档、到期自动清理 |

---

## 功能概览

### 树状思维导图

输入 Markdown 标题层级或列表缩进，输出一张根在左、层级向右展开的树状图。节点宽度按文字实际长度计算，长句自动折行成多行。

### 竖轴时间线

大纲叶子节点多为日期（`1789:`、`1949 年` 等）时自动判定为时间线，节点沿中央竖轴左右交替排布，适合历史脉络与事件先后。

### 六套配色

内置朱砂（默认）、靛蓝、松绿、琥珀、墨灰、黛紫六种主色，其余五阶由主色按明度阶梯派生。传 `#RRGGBB` 可自定义任意主色，极浅或极深的主色会被钳到可派生区间，保证层级依然可读。

### Agent 自主调用

插件内置技能 `mindmap`，教 bot 大纲格式、规模建议、配色选择与发送纪律。bot 在科普回答中自行调用 `draw_mindmap` 出图，用户无需关心指令语法。

### 图文件留存与二次加工

生成的 PNG 落在 `data/plugin_data/astrbot_plugin_mindmap/mindmap/YYYYmmdd/` 下，默认保留 7 天。调用时传 `send=False` 只渲染不发图，返回文件路径，可用于嵌入 docx、PDF 或做二次加工。

---

## 快速开始

### 第一步：安装

AstrBot WebUI → 插件市场 → 搜索「思维导图工具箱」

> **提示：**插件安装时会自动读取 `requirements.txt` 安装 Pillow，无需手动装依赖。

### 第二步：直接说需求

安装后无需任何配置。在对话里自然描述，bot 会自己判断是否画图、画哪种：

```
用户：帮我梳理一下康德的三大批判，画个思维导图
bot：[思维导图 PNG] 画好啦！

用户：把法国大革命到巴黎公社的关键节点画成时间线
bot：[时间线 PNG] 已画好，从 1789 到 1871 共 5 个节点。
```

### 第三步：或使用指令

```
/mindmap <大纲>                      # 默认主题
/mindmap timeline <事件>             # 时间线
/mindmap --theme 靛蓝 <大纲>         # 指定内置主题
/mindmap --theme #2E8B8B <大纲>      # 自定义主色
```

`--theme` 与 `timeline` 前缀顺序任意；大纲为空时回复用法说明。

---

## 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|:------|:-----|:-------|:-----|
| `auto_send` | bool | `true` | 工具调用未显式指定 `send` 时是否自动发图 |
| `echo_outline` | bool | `false` | 指令生成图片后是否在回复里回显原始大纲 |
| `retain_days` | int | `7` | PNG 保留天数，超过后自动清理 |
| `max_image_width` | int | `4000` | 输出图片最大宽度（像素），超出等比缩放 |
| `max_nodes` | int | `200` | 大纲节点数硬上限，超出拒绝生成 |
| `max_node_chars` | int | `200` | 单节点字数硬上限，超出拒绝生成（不静默裁剪） |
| `output_scale` | float | `1` | 输出分辨率倍数，支持小数；受 `max_image_width` 约束 |
| `enable_command` | bool | `true` | 是否启用 `/mindmap` 指令 |

### 快速配置模板

在 WebUI 配置面板填写，或参考以下结构（`data/config/astrbot_plugin_mindmap_config.json`）：

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

## LLM 可调用工具

插件注册 1 个 LLM 工具，模型会自动判断何时调用，你只需用自然语言说需求：

```
用户：把这段材料的结构画出来
    # 韦伯的支配类型学
    ## 传统型支配
    - 长老制与世袭制
    ## 卡里斯玛型支配
    - 先知与领袖的非凡品质
    ## 法理型支配
    - 科层制与形式理性法
bot：[思维导图 PNG] 画好啦！
```

### draw_mindmap

根据大纲生成中文思维导图或时间线图（PNG）。

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:----:|:-----|
| `outline` | string | 是 | Markdown 大纲，用 `#` 标题或 `-` 列表缩进表示层级 |
| `layout` | string | 否 | `tree` 思维导图 / `timeline` 时间线 / `auto` 自动检测（默认） |
| `theme` | string | 否 | 内置主题名或 `#RRGGBB` 主色；留空用默认朱砂，无法识别时静默回退默认 |
| `send` | bool | 否 | 是否直接发图，默认 `true`；`false` 时只渲染并返回文件路径 |

> **注意：**`send=False` 返回的是文件路径，供文件工具读取后嵌入 docx 等文档，不要把这个路径念给用户。

大纲规模建议：层级 ≤ 4 层、每个分支 ≤ 6 个子节点、总节点 ≤ 60、单节点 ≤ 40 字。超出硬上限时返回固定短语提示精简，不会静默裁剪内容。

---

## 常见问题

### Q1：需要配置什么吗？

不需要。装好即用，所有配置项都有合理默认值。

### Q2：支持哪些平台？

任何支持图片消息的平台（QQ、Telegram、Discord 等）。发送失败时工具会返回生成好的文件路径，便于宿主或用户自取。

### Q3：图片存在哪里，会占空间吗？

`data/plugin_data/astrbot_plugin_mindmap/mindmap/YYYYmmdd/`，按日期分目录；超过 `retain_days`（默认 7 天）自动删除，后台每 6 小时清理一次。

### Q4：大纲太大画不出来怎么办？

按返回短语精简：合并同类节点、减少层级，或拆成多张图分别绘制。硬上限是 200 节点、单节点 200 字、层级 8 层。

### Q5：为什么不用 mermaid、markmap 这类现成方案？

它们要么依赖浏览器渲染、要么中文不折行。本插件用 Pillow 自研布局与折行，纯本地、无浏览器依赖，聊天缩略图下也清晰。

### Q6：能把图放进 docx 吗？

可以。调用时传 `send=False`，拿到返回的文件路径后用文件工具读取，再嵌入文档。

---

## 更新日志

> **[查看更新日志 →](CHANGELOG.md)**

## 支持与致谢

如果这个插件对你有帮助，欢迎点亮 Star，有问题和建议请提交 [Issue](https://github.com/OMSociety/astrbot_plugin_mindmap/issues) 或 [Pull Request](https://github.com/OMSociety/astrbot_plugin_mindmap/pulls)。

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) 开源聊天机器人框架
- [Source Han Sans](https://github.com/adobe-fonts/source-han-sans) 思源黑体（SIL Open Font License 1.1，见 `res/fonts/OFL.txt`）

## 许可证与作者

本项目采用 **AGPL-3.0** 开源协议。

[@OMSociety](https://github.com/OMSociety)
