<p align="center"><strong>中文</strong> | <a href="README_en.md">English</a></p>

<div align="center">
  <img src="https://raw.githubusercontent.com/OMSociety/astrbot_plugin_mindmap/main/logo.png" width="128" alt="思维导图工具箱 Logo" />
  <h1>思维导图工具箱</h1>
  <p>AstrBot 插件 · 把大纲渲染成思维导图 / 时间线发到群里，全程本地、零浏览器</p>
  <p>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/releases"><img src="https://img.shields.io/badge/version-v1.0.0-B41818" alt="Version" /></a>
    <a href="https://github.com/AstrBotDevs/AstrBot"><img src="https://img.shields.io/badge/AstrBot-plugin-5865F2" alt="AstrBot" /></a>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-green" alt="License" /></a>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/stargazers"><img src="https://img.shields.io/github/stars/OMSociety/astrbot_plugin_mindmap" alt="Stars" /></a>
    <a href="https://github.com/OMSociety/astrbot_plugin_mindmap/issues"><img src="https://img.shields.io/github/issues/OMSociety/astrbot_plugin_mindmap" alt="Issues" /></a>
  </p>
</div>

[核心特性](#核心特性) • [功能概览](#功能概览) • [快速开始](#快速开始) • [大纲格式](#大纲格式) • [配置说明](#配置说明) • [LLM 工具](#llm-工具) • [故障排查](#故障排查)

## 核心特性

| 特性 | 说明 |
|------|------|
| **树状思维导图** | 根在左、水平展开，社科红分支配色 |
| **竖轴时间线** | 中央竖轴、节点左右交替，适合历史脉络 |
| **Agent 自主出图** | 内置 LLM 工具，读完材料自己决定画图发送 |
| **全程本地** | Pillow 自研渲染，无浏览器依赖，内容不出本机 |
| **图文件留存** | PNG 按日归档、到期自动清理，可嵌入 docx 复用 |
| **高清输出** | 2x 超采样，QQ 缩略图与原图都清晰 |

## 功能概览

### 树状思维导图

输入 Markdown 大纲，输出一张分支配色的树状图。层级、折行、配色全自动。

### 竖轴时间线

带日期的大纲自动识别为时间线，节点沿中央竖轴左右交替排布。

### Agent 自主调用

插件内置技能 `mindmap` 教 agent 大纲语法与发送纪律；agent 在科普回答中自行调用 `draw_mindmap` 出图并发送到群。

### 图文件留存

生成的 PNG 保留在 `data/mindmap/YYYYmmdd/` 下（默认 7 天自动清理），可嵌入 docx 等文档复用。

## 快速开始

在 AstrBot 插件市场搜索「思维导图工具箱」安装即可，无需任何配置。

## 大纲格式

支持 Markdown 标题层级与列表缩进混用；树状与时间线两种形态：

```markdown
# 主题
## 一级分支
- 节点
  - 子节点
- 另一节点：可写长描述，自动折行

# 时间线
- 1789: 三级会议召开
- 1793–1794: 雅各宾专政
```

> **提示：**节点数 ≤ 200、单节点文本 ≤ 200 字符；超出会拒绝并提示精简。完整规范见插件内置技能 `skills/mindmap/SKILL.md`。

## 配置说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| theme | string | socred | 配色主题（目前内置 socred 社科红） |
| auto_send | bool | true | 工具调用后是否自动发图 |
| retention_days | int | 7 | PNG 留存天数，0 为永久 |
| output_scale | int | 2 | 分辨率倍数（1 / 2 / 3） |

快速配置模板：

```json
{
  "theme": "socred",
  "auto_send": true,
  "retention_days": 7,
  "output_scale": 2
}
```

## LLM 工具

`draw_mindmap(outline, layout, send)`：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| outline | string | 是 | Markdown 大纲 |
| layout | string | 否 | `tree` / `timeline` / `auto`（默认 auto） |
| send | bool | 否 | 默认取配置 `auto_send`；`false` 只渲染不发，返回短语含绝对路径 |

对话示例：

```
你：帮我梳理一下康德的三大批判，画个思维导图
机器人：[思维导图 PNG] 已发送思维导图（10 个节点）。
```

不支持富媒体的平台上 `auto_send` 会自动禁用，改为返回文件路径供宿主自取。

## 故障排查

> **中文变方框：**插件自带思源黑体（res/fonts/），正常不会缺字；若仍方框，检查两个 otf 文件是否完整（共约 33 MB）。

> **插件没出现在插件页：**确认目录含 metadata.yaml、main.py、logo.png、_conf_schema.json；Launcher 管理的实例需整实例重启，源码实例可设 ASTRBOT_RELOAD=1 开启热重载。

> **不出图只回短语：**大纲超限（超过 200 节点或单节点超过 200 字），按返回短语精简后重试。

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)。

## 支持与致谢

字体：思源黑体（Source Han Sans CN），SIL Open Font License 1.1，见 res/fonts/OFL.txt。

## 许可证与作者

AGPL-3.0 · OMSociety。第三方组件（思源黑体）按 OFL 1.1 单独授权。
