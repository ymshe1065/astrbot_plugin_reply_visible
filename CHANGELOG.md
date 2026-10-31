# 变更记录

本项目的重要变更会记录在这里。

## v0.2.0 — 2026-10-31

捕获层重构版本。

### 捕获

- 新增 `on_decorating_result` 发送前捕获，保留 T2I 卡片渲染前的原始文本和组件；
- 保留 `after_message_sent` 作为发送后兜底，避免同一结果重复捕获；
- 新增 `component_parser.py`，支持 `Plain`、`At`、`Image`、`Json`、`Nodes` / `Forward`、`File`、`Record`、`Video`、`Reply`、`Face`、`Poke`、`Share`、`Location`；
- 合并转发递归提取，限制递归深度和节点数量；
- 未知组件只记录类型，不阻塞主流程；
- 新增多段回复合并窗口 `merge_window_ms`（默认 800ms）；
- 注入时标注插件来源、回复对象（发送者）和触发指令；无法识别插件时标注“未知插件”；
- 跳过自身调试指令、帮助菜单和明显错误信息。

### 图片与调试

- 图片识别改为后台任务，发送消息不再等待 OCR/视觉模型；
- 注入时最多等待 2 秒图片识别，超时使用占位符；
- 新增 `/插件回复调试`，显示最近捕获阶段、组件类型、跳过原因和队列概况。

### 工程

- 新增组件解析测试 `tests/test_component_parser.py`；
- CI 增加组件解析测试和 `component_parser.py` 编译检查；
- README、metadata 和配置提示同步更新。

### 兼容性

- 保持 v0.1.0 的配置键兼容；
- 新增 `merge_window_ms`，默认 800ms，设为 0 可关闭合并；
- 已发布并部署，GitHub tag / Release 为 `v0.2.0`。

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
