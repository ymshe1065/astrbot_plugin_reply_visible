# 变更记录

本项目的重要变更会记录在这里。

## v0.1.0 — 2026-10-27

首个公开版本，也是 AstrBot 市场首发版本。

### 新增

- 捕获群内插件/指令的非 LLM 回复（纯文本 + 图片卡片）；
- 在下一次 LLM 请求前按群注入临时上下文，注入后清空；
- 图片识别：可选本地 OCR，未安装时回退视觉模型；
- 按 `unified_msg_origin` 隔离队列，支持群白名单；
- 5 秒内重复内容去重，以及单条文本、队列、图片数量上限；
- `<plugin_reply_context no_learn="true">` 防学习标注；
- `TextPart.mark_as_temp()` 临时注入，不写入会话历史；
- `/插件回复状态` 调试指令。

### AstrBot 市场信息

- 插件 ID：`ymshe1065/astrbot_plugin_reply_visible`；
- 作者：`ymshe1065`；
- 版本：`0.1.0`；
- 兼容 AstrBot `>=4.29.0`；
- 声明平台：`aiocqhttp`；
- 开源协议：MIT。

### 工程质量

- `metadata.yaml` 补齐 `short_desc`、`astrbot_version`、`support_platforms`、`tags`、`social_link`；
- 新增 GitHub Actions CI（编译 + 冒烟测试）；
- 新增 [ROADMAP.md](ROADMAP.md)，明确版本策略和后续版本范围；
- LICENSE、README、DEVELOPMENT_PLAN 和 CHANGELOG 完整同步。

### 插件页与文档

- 为捕获钩子、注入钩子和 `/插件回复状态` 指令补充 docstring，AstrBot 插件页不再显示“无描述”；
- README 和 `metadata.yaml` 增加本地 OCR 安装命令、识别顺序和 OCR / 视觉模型优劣对比；
- 配置提示说明本地 OCR 优先、视觉模型兜底的关系；
- `/插件回复状态` 显示本地 OCR 是否已安装及安装提示。

### 兼容性

- 使用公开钩子 `after_message_sent`、`on_llm_request`；
- 不修改 AstrBot 核心和其他插件。

### 已知限制

- 只捕获走标准回复链的插件；
- 暂存队列保存在内存中，插件重启后丢失；
- selflearning 仍会把原始插件回复当作 Bot 出站消息记录，需在 selflearning 侧过滤；
- 合并转发、文件、语音暂未解析；
- 当前只在 `aiocqhttp` 适配器实测。
