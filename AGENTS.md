# AGENTS.md — astrbot_plugin_mindmap Agent 宪法

适用范围：本仓库全部目录。
最后更新：2026-10-29

## 项目概览

- 一句话定位：AstrBot 插件，把 Markdown 大纲渲染为思维导图/时间线 PNG，服务学术科普 bot。
- 技术栈：Python 3.13 / AstrBot 4.x 插件框架 / Pillow 自研布局渲染（无浏览器、无外部渲染服务）。
- 宿主机制细节：以 AstrBot 宿主源码为准；开发口径见本地技能 astrbot-plugin-creator 的 references/。

## 常用命令

| 目的 | 命令 |
|---|---|
| 安装依赖 | `pip install -r requirements.txt`（装进 AstrBot 宿主 venv；插件加载时宿主也会自动装） |
| 跑全部测试 | `python -m pytest tests -q` |
| 跑单个测试文件 | `python -m pytest tests/test_parser.py -q` |
| Lint | `ruff check .` |
| 格式化 | `ruff format .` |
| 插件离线自检 | astrbot-plugin-creator 技能的 `scripts/check_plugin.py <本仓库>` |

Lint 用 AstrBot 宿主 venv 的 ruff（版本跟随宿主 pyproject 的 pin），不另装。

```bash
python -m pytest tests -q
ruff check .
ruff format --check .
```

## 架构边界

```text
main.py（Star 入口） -> core/parser -> core/layout -> core/render -> core/theme, core/fonts
```

- 允许：main.py 只调 core 的公开函数；core 内部按上箭头单向依赖。
- 禁止 core/ 内 import 任何 astrbot.*。原因：core 必须能在无宿主环境下被 pytest 直接测；宿主耦合会让单测依赖运行时。
- main.py 只做「接事件 → 调 core → 发图」，不藏布局/渲染逻辑。

## 关键目录

| 我要… | 改这里 |
|---|---|
| 加大纲语法/解析规则 | `core/parser.py`（+ `tests/test_parser.py`） |
| 改布局（间距/树结构/时间线） | `core/layout.py`（+ `tests/test_layout.py`） |
| 改出图样式（圆角/描边/时间轴） | `core/render.py`（+ `tests/test_render.py`） |
| 加/改主题色 | `core/theme.py` 的 `THEMES` 注册表（+ `skills/mindmap/SKILL.md` 主题清单） |
| 换字体 | `res/fonts/`（OFL 合规见「已知风险区」） |
| 改工具参数/指令 | `main.py` + `_conf_schema.json` + `skills/mindmap/SKILL.md` 三处同步 |

## 数据流

聊天消息或 LLM 工具调用 → main.py 解析参数 → parser 出 Node 树 → layout 在基准坐标系算坐标 → render 按 output_scale 超采样出 PNG → event.send 被动回复发图。

## 修改契约

- 改 `_conf_schema.json`：宿主加载时会补默认、删旧键（用户旧值会丢），改前提醒备份配置；`default` 禁 `null`，`labels` 与 `options` 按索引等长。
- 改基准坐标系（`core/layout.py` 顶部常量区）：必须硬回归——同一输入新旧各渲一张，默认 output_scale=1 的像素尺寸与视觉样式应与基准一致（用 WorkBench 的 scale_regress 对比法）。
- 主题只经参数传入（工具 `theme` / 指令 `--theme`），不进 `_conf_schema.json`；默认主题固定在 `core/theme.py` 的 `DEFAULT_THEME`。原因：主题是单次调用属性，配置化会让用户以为全局改色而未生效。
- 改 `draw_mindmap` 的参数或返回值：同步 `skills/mindmap/SKILL.md` 与 README 双语。
- 改依赖：写进 `requirements.txt`；每个第三方顶层 import 都必须有对应条目；禁止 `requests`（用异步库）。
- 版本号保持一致：`metadata.yaml` / `CHANGELOG.md` / README 徽章；首版 CHANGELOG 只有标准头部，1.0.1 起才写版本条目。

## 禁止操作

- 禁止 core/ 内 import astrbot.*（原因见「架构边界」）。
- 禁止兄弟模块绝对导入，写 `from .utils import x`。原因：宿主加载时报 ModuleNotFoundError，而本地 pytest 因 PYTHONPATH 掩盖常常是绿的；改完必须做一次宿主内模拟加载。
- 禁止使用 `register`/`register_star` 装饰器。原因：宿主已标 DEPRECATED 且会 warnings.warn；Star 子类由宿主自动识别。
- 禁止把持久化写进插件目录。原因：插件更新/重装即丢；用 `StarTools.get_data_dir()` 下的 `data/plugin_data/<插件名>/`。
- 禁止在工具 description/返回值里写禁令清单、写死默认值或暴露异常原文。原因：模型会照抄复述、污染 bot 人格；成功给确认短语、失败给固定短语（astrbot-plugin-creator 硬约束 8）。

## 验收标准

改动完成 = 下列全部通过：

1. `python -m pytest tests -q`（Windows 本机若 Temp 目录 ACL 拒绝，加 `--basetemp=<可写目录>`）
2. `ruff check .` 与 `ruff format --check .`
3. 宿主内模拟加载：在宿主 venv 中 `import data.plugins.astrbot_plugin_mindmap.main` 无异常
4. astrbot-plugin-creator 技能 `scripts/check_plugin.py` 对「排除 tests/ 的副本」跑出 error 0（tests 用包名绝对导入是 pytest 必需写法，直接扫仓库会有 13 条 import.self 假阳性）

## 提交与协作

- 分支：main 单分支（仓库史尚短，惯例未成型）。
- Commit：`feat:`/`fix:`/`docs:` 前缀（首提交即此风格）。

## 已知风险区

| 路径 | 风险 | 改动前后置动作 |
|---|---|---|
| `core/layout.py` 常量区 | 基准坐标系 2026-10 重定过：1x 即原 2x 像素 | 改完跑硬回归（见「修改契约」） |
| `res/fonts/` | 思源黑体 OFL 1.1 有 Reserved Font Name：改字体文件必须连名一起改并更新 OFL.txt | 改前读 `res/fonts/OFL.txt` |
| `skills/mindmap/SKILL.md` | bot 行为规范：回复纪律（不解释工作流）、发送纪律（被动发图）写在这里 | 改工具行为必须同步此文件 |
| Windows 本机 pytest | Temp 目录 ACL 拒绝会让 tmp_path 夹具全挂 | 加 `--basetemp` 指向可写目录 |
| `check_plugin.py` 输出 | `PIL` 未声明与 tests 的 `import.self` 均为误报：依赖名在 `requirements.txt` 里写作 Pillow，测试必须用包名绝对导入 | 只看排除 tests 后的 error 数 |

## 出错怎么办

| 症状（可检索片段） | 处理 |
|---|---|
| 宿主插件页看不到插件 | 目录名须等于 metadata.yaml 的 `name` 且是合法 Python 标识符；查宿主日志的加载异常 |
| 发 `/mindmap` 无响应 | 指令匹配 `^/?mindmap`；检查平台指令前缀配置 |
| LLM 不调工具或复述工具返回值 | 检查 SKILL.md 与工具 docstring 的模型可见面（见「禁止操作」） |

## 维护

本文件与代码同 PR 更新。改动以下内容时必须同步本文件：验收命令、core 边界、主题/参数面、风险区。
发现内容与代码不符时，先改本文件再继续改动代码。
