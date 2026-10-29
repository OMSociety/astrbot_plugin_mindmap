<p align="center"><strong>中文</strong> · <a href="README_en.md">English</a></p>

<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_mindmap/main/logo.png" width="120" alt="Mindmap Logo" />

# Mindmap 图表工具箱

**把材料渲染成思维导图 / 时间线 / 表格 / 基础流程图，直接发到群里** —— 本地渲染 · 六套配色 · 中文自动折行 · 高清输出

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
| **思维导图与时间线** | 树状图根在左、层级向右展开；时间线沿中央竖轴交替排布，长文本自动折行 |
| **Markdown 表格** | 标准 Markdown 输入，标题独立传参，适合整理对比项与结构化数据 |
| **基础流程图** | 纵向或横向绘制开始、处理、判断与结束节点，支持顺序、分支与汇合 |
| **六套配色** | 朱砂 / 靛蓝 / 松绿 / 琥珀 / 墨灰 / 黛紫，也可传 `#RRGGBB` 自定义主色 |
| **Agent 自主出图** | 三个 LLM 工具与配套技能规范，bot 读完材料自行选图并发送 |
| **全程本地** | Pillow 自研布局渲染，不依赖浏览器、Graphviz 或远程渲染服务 |
| **中文排版** | 自带思源黑体，节点按字符宽度折行，不出现方框与截断 |
| **高清与留存** | 默认 1x 基准即旧版 2x 像素、可调小数倍数；PNG 按日归档、到期自动清理 |

---

## 功能概览

### 思维导图与时间线

输入 Markdown 标题层级或列表缩进，输出根在左、层级向右展开的树状图。大纲叶子节点多为日期（`1789:`、`1949 年` 等）时可自动判定为时间线，适合历史脉络与事件先后。

### 表格

`draw_table` 接收标准 Markdown 表格，标题通过单独的 `title` 参数设置。最多 8 列、50 个数据行，每个单元格最多 200 字；不支持合并单元格或富文本。

### 基础流程图

`draw_flowchart` 将节点声明与有向连线渲染为流程图。默认纵向排列，也可选择横向；支持 `start`、`process`、`decision`、`end` 四种节点及顺序、分支、汇合关系，最多 30 个节点。

流程图只接受结构明确的单向流程。回环、跨层连线、不可达节点和歧义输入会被拒绝，不猜测或补全流程关系。

### 六套配色

内置朱砂（默认）、靛蓝、松绿、琥珀、墨灰、黛紫六种主色，其余五阶由主色按明度阶梯派生。传 `#RRGGBB` 可自定义任意主色，极浅或极深的主色会被钳到可派生区间，保证层级依然可读。

### Agent 自主调用

插件内置技能 `mindmap`，教 bot 选择图表类型、组织输入、控制规模、选择配色并遵守发送纪律。bot 在科普回答中自行调用相应工具出图，用户只需自然描述需求。

### 图文件留存与二次加工

生成的 PNG 落在 `data/plugin_data/mindmap/mindmap/YYYYmmdd/` 下，默认保留 7 天。调用时传 `send=False` 只渲染不发图，返回文件路径，可用于嵌入 docx、PDF 或做二次加工。

---

## 快速开始

### 第一步：安装

AstrBot WebUI → 插件市场 → 搜索「思维导图工具箱」

> **提示：**插件安装时会自动读取 `requirements.txt` 安装 Pillow，无需手动装依赖。

### 第二步：直接说需求

安装后无需任何配置。在对话里自然描述，bot 会自己判断是否画图、画哪种：

```text
用户：康德的三大批判分别在处理什么问题？
bot：三大批判考察的是认识、实践与判断三种能力。
[三大批判对比表格 PNG]
可见，三者并非彼此割裂，而是共同构成批判哲学的整体。

用户：把这份材料处理过程画成流程图
bot：材料处理可以分成完整性检查、概念提取与体系形成几个环节。
[材料处理流程图 PNG]
其中，补充材料与直接提取概念两条路线最终汇入同一终点。
```

---

## 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|:------|:-----|:-------|:-----|
| `auto_send` | bool | `true` | 工具调用未显式指定 `send` 时是否自动发图 |
| `retain_days` | int | `7` | PNG 保留天数，超过后自动清理 |
| `max_image_width` | int | `4000` | 输出图片最大宽度（像素），超出等比缩放 |
| `max_nodes` | int | `200` | 大纲节点数硬上限，超出拒绝生成 |
| `max_node_chars` | int | `200` | 单节点字数硬上限，超出拒绝生成（不静默裁剪） |
| `output_scale` | float | `1` | 输出分辨率倍数，支持小数；受 `max_image_width` 约束 |

### 快速配置模板

在 WebUI 配置面板填写，或参考以下结构（`data/config/mindmap_config.json`）：

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

## LLM 可调用工具

插件注册 `draw_mindmap`、`draw_table`、`draw_flowchart` 三个工具，模型会自动判断何时调用，你只需用自然语言说需求。

### draw_mindmap

根据大纲生成中文思维导图或时间线图（PNG）。

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:----:|:-----|
| `outline` | string | 是 | Markdown 大纲，用 `#` 标题或 `-` 列表缩进表示层级 |
| `layout` | string | 否 | `tree` 思维导图 / `timeline` 时间线 / `auto` 自动检测（默认） |
| `theme` | string | 否 | 内置主题名或 `#RRGGBB` 主色；留空用默认朱砂，无法识别时静默回退默认 |
| `send` | bool | 否 | 是否直接发图，默认 `true`；`false` 时只渲染并返回文件路径 |

大纲规模建议：层级 ≤ 4 层、每个分支 ≤ 6 个子节点、总节点 ≤ 60、单节点 ≤ 40 字。硬上限为 200 节点、单节点 200 字、层级 8 层；超限拒绝生成，不静默裁剪内容。

### draw_table

将标准 Markdown 表格渲染为 PNG。表格标题通过 `title` 传入，不写进 `markdown`。

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:----:|:-----|
| `markdown` | string | 是 | 标准 Markdown 表格，包含表头、分隔行与数据行 |
| `title` | string | 否 | 表格标题，最多 80 字，超宽自动折行 |
| `theme` | string | 否 | 内置主题名或 `#RRGGBB` 主色；留空用默认主题 |
| `send` | bool | 否 | 是否直接发图，默认 `true`；`false` 时只渲染并返回文件路径 |

最多 8 列、50 个数据行，每个单元格最多 200 字。支持纯文本单元格，不支持合并单元格或富文本。

```text
draw_table(markdown="| 批判 | 核心问题 |\n| --- | --- |\n| 纯粹理性批判 | 我能够知道什么？ |\n| 实践理性批判 | 我应当做什么？ |", title="康德的批判哲学", theme="朱砂", send=True)
```

### draw_flowchart

将节点声明与有向连线渲染为基础流程图（PNG）。

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:----:|:-----|
| `spec` | string | 是 | 流程定义，含可选的 `#` 标题（最多 80 字）、节点声明与有向边 |
| `direction` | string | 否 | `vertical` 纵向（默认）/ `horizontal` 横向 |
| `theme` | string | 否 | 内置主题名或 `#RRGGBB` 主色；留空用默认主题 |
| `send` | bool | 否 | 是否直接发图，默认 `true`；`false` 时只渲染并返回文件路径 |

节点声明格式为 `节点ID [类型] 节点文字`。节点 ID 必须以 ASCII 字母开头，之后可含 ASCII 字母、数字、下划线或连字符；类型可省略，缺省为 `process`。首行 `# 标题` 可选，流程图标题只在这里设置。边写成 `起点 -> 终点`，需要分支标签时用中文或英文冒号追加，如 `check -> process: 是`。

支持 `start`、`process`、`decision`、`end` 四种节点，以及顺序、分支与汇合。唯一入口使用 `start`，各末端使用 `end`，中间节点不能悬空在末端。最多 30 个节点；回环、跨层连线、不可达节点和歧义输入会被拒绝。

```text
draw_flowchart(spec="# 材料处理\nstart [start] 收到材料\ncheck [decision] 材料完整？\nprocess [process] 提取概念\nsupplement [process] 补充材料\ndone [end] 形成体系\nstart -> check\ncheck -> process: 是\ncheck -> supplement: 否\nprocess -> done\nsupplement -> done", direction="vertical", theme="朱砂", send=True)
```

> **注意：**三个工具的 `send` 行为一致。`send=False` 返回的文件路径供文件工具读取后嵌入 docx 等文档，不要把这个路径念给用户。

---

## 常见问题

### Q1：需要配置什么吗？

不需要。装好即用，所有配置项都有合理默认值。

### Q2：支持哪些平台？

任何支持图片消息的平台（QQ、Telegram、Discord 等）。发送失败时工具会返回生成好的文件路径，便于宿主或用户自取。

### Q3：图片存在哪里，会占空间吗？

`data/plugin_data/mindmap/mindmap/YYYYmmdd/`，按日期分目录；超过 `retain_days`（默认 7 天）自动删除，后台每 6 小时清理一次。

### Q4：输入太大画不出来怎么办？

思维导图可合并同类节点、减少层级或拆成多张图；表格可拆列或分批绘制；流程图应拆成多个边界清楚的子流程。超限内容不会被静默裁剪。

### Q5：为什么不用 Mermaid、Markmap 或 Graphviz？

插件使用 Pillow 自研布局与折行，纯本地渲染，无浏览器或 Graphviz 依赖，聊天缩略图下也清晰。

### Q6：能把图放进 docx 吗？

可以。调用任一工具时传 `send=False`，拿到返回的文件路径后用文件工具读取，再嵌入文档。

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
