# AstrBot 插件回复可见（Plugin Reply Visible）

[![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.29.0-blue.svg)](https://github.com/AstrBotDevs/AstrBot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/ymshe1065/astrbot_plugin_reply_visible/actions/workflows/ci.yml/badge.svg)](https://github.com/ymshe1065/astrbot_plugin_reply_visible/actions/workflows/ci.yml)
[![GitHub release](https://img.shields.io/github/v/release/ymshe1065/astrbot_plugin_reply_visible?label=release)](https://github.com/ymshe1065/astrbot_plugin_reply_visible/releases)

> 状态：**v0.1.0 首个公开版本 / AstrBot 市场首发版**，已实现基础捕获、文本注入、图片识别、防学习标注、调试指令
> 兼容版本：AstrBot `>=4.29.0`
> GitHub 仓库：<https://github.com/ymshe1065/astrbot_plugin_reply_visible>
> 版本路线图：[ROADMAP.md](./ROADMAP.md)
> 开发细节：[DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md)

| 项目 | 信息 |
| --- | --- |
| 插件 ID | `ymshe1065/astrbot_plugin_reply_visible` |
| 当前版本 | `0.1.0` |
| 作者 | `ymshe1065` |
| 支持平台 | `aiocqhttp` |
| 开源协议 | MIT |

## 1. 这个插件解决什么问题

AstrBot 的群聊 AI 通常只能看到：

- 用户发的消息；
- AI 自己上一轮的回复；
- AstrBot 的群聊上下文/长期记忆。

但**插件指令的回复**（例如修仙插件的 `/签到`、`/购买`、`/切磋`、`/我的信息` 卡片）不经过 LLM，默认不会进入 AI 的上下文。于是会出现：

```text
用户：/购买 护灵丹 1
插件：成功购买丹药【护灵丹】x1，已放入丹药背包。
用户：这个药干嘛的？
AI：我不知道你买了什么……
```

本插件把群里插件的回复捕获下来，在下一次 AI 回复时作为临时上下文注入，让 AI 能接着聊。

## 2. 已实现能力

| 能力 | 状态 |
| --- | --- |
| 捕获插件纯文本回复 | ✅ |
| 捕获插件图片卡片 | ✅ |
| 图片 OCR（可选，本地运行） | ✅ 未安装时自动回退视觉模型 |
| 视觉模型生成图片描述 | ✅ |
| 按群隔离 | ✅ |
| 5 秒内重复内容去重 | ✅ |
| 单条/单轮/队列长度限制 | ✅ |
| 注入后清空，只出现一次 | ✅ |
| 防提示词注入包装 | ✅ |
| 防学习标注（`no_learn`，兼容自学习插件） | ✅ |
| 调试指令 `/插件回复状态` | ✅ |

## 3. 使用效果

```text
用户：/我的信息
插件：[角色面板图片]
用户：我法防多少？
AI：你当前法防 2745……
```

```text
用户：/签到
插件：签到成功，获得 888 灵石
用户：我刚才签到赚了多少？
AI：你刚才签到获得了 888 灵石。
```

## 4. 安装

1. 把整个 `astrbot_plugin_reply_visible` 文件夹复制到：

```text
...\core\data\plugins\astrbot_plugin_reply_visible
```

也可以直接克隆：

```powershell
cd ...\core\data\plugins
git clone https://github.com/ymshe1065/astrbot_plugin_reply_visible.git
```

2. 如果之前装过旧版 `astrbot_plugin_reply_bridge`，先删除旧目录再安装，避免两个插件同时捕获；
3. 完整重启 AstrBot（不是只重载插件）；
4. 在 WebUI 的插件管理里确认已启用；
5. 打开插件配置，按需填写视觉模型。

## 5. 配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `enabled` | `true` | 总开关 |
| `group_only` | `true` | 只处理群聊 |
| `whitelist_groups` | `[]` | 生效群号；空表示全部 |
| `max_pending` | `10` | 每群最多暂存条数 |
| `text_limit` | `800` | 单条文本最大字符数 |
| `image_caption_enable` | `true` | 是否识别图片；开启时优先本地 OCR，再回退视觉模型 |
| `vision_provider_id` | 空 | 本地 OCR 未命中时使用的视觉模型；空则用 AstrBot 默认图片描述模型 |
| `image_caption_prompt` | 见默认 | 视觉模型提示词；本地 OCR 成功时不使用 |
| `image_caption_limit` | `300` | 单张描述最大字符数 |
| `image_max_per_turn` | `3` | 单轮最多识别图片数 |
| `inject_header` | 见默认 | 注入块标题 |
| `no_learn_enable` | `true` | 是否添加 `no_learn` 防学习标注 |

> 视觉模型必须是**支持图片**的模型。DeepSeek 文本模型不能直接看图，建议填 Qwen-VL、GLM-4V、Gemini 等。
> 如果主要识别卡片里的文字和数字，优先安装本地 OCR：图片不外发、无 API 费用，数字通常更准。

## 6. 可选：本地 OCR

本地 OCR 是在运行 AstrBot 的机器上，直接把图片里的文字和数字识别成文本，**不把图片发给视觉模型**。

### 安装

进入 AstrBot 使用的 Python 环境后执行：

```powershell
python -m pip install "rapidocr_onnxruntime>=1.3.0"
```

Windows 启动器实例也可以直接使用实例的 venv：

```powershell
<实例目录>\venv\Scripts\python.exe -m pip install "rapidocr_onnxruntime>=1.3.0"
```

安装后重启或重载 AstrBot。不安装也能用，插件会自动回退到视觉模型。

### OCR 与视觉模型的区别

| 对比项 | 本地 OCR | 视觉模型 |
| --- | --- | --- |
| 运行位置 | 本机 CPU | 云端 Provider 或自建服务 |
| 图片是否上传 | 否 | 是 |
| 费用 | 免费 | 可能按 token / 图片计费 |
| 擅长 | 文字、数字、表格、卡片数值 | 角色、图标、布局、画面语义 |
| 数字准确度 | 通常更高 | 取决于模型，可能误读 |
| 速度 | 首次加载较慢，后续较快 | 受网络、模型和图片大小影响 |
| 资源占用 | 额外磁盘和 CPU | API 配额和网络 |
| 配置成本 | 安装依赖即可 | 需要配置支持图片的 Provider |
| 局限 | 只读文字，不理解图标和画面 | 可能幻觉，数字不一定准 |

识别顺序为：**本地 OCR -> 视觉模型 -> 占位符**。

当前 OCR 只处理**本地图片文件路径**；如果插件图片是 `http/https` 远程 URL，会跳过 OCR，直接交给视觉模型。

## 7. 调试指令

| 指令 | 作用 |
| --- | --- |
| `/插件回复状态` | 查看当前群暂存数量、图片识别、本地 OCR 安装状态、视觉模型、防学习标注 |

## 8. 兼容性

- AstrBot `>=4.29.0`；
- 当前实测平台：`aiocqhttp`（其他平台需验证后再加入 `support_platforms`）；
- 使用公开钩子：`after_message_sent`、`on_llm_request`；
- 不修改 AstrBot 核心；
- 不修改其他插件。

版本号、发布流程和后续范围见 [ROADMAP.md](./ROADMAP.md)。

## 9. 目录结构

```text
astrbot_plugin_reply_visible/
├── README.md
├── ROADMAP.md
├── DEVELOPMENT_PLAN.md
├── CHANGELOG.md
├── LICENSE
├── metadata.yaml
├── _conf_schema.json
├── main.py
├── requirements.txt
├── .github/
│   └── workflows/
│       └── ci.yml
└── tests/
    └── test_smoke.py
```

## 10. 开源协议

本项目采用 [MIT License](LICENSE) 开源。你可以自由使用、修改和分发，但需保留原始版权声明和协议文本。
