
<div align="center">
    <img src="assets/WCA_README_banner.png" alt="CraftOS 横幅" width="1280"/>
</div>
<br>
<div align="center">
    <img src="assets/craftbot_logo_text_small.png" alt="CraftBot 标志" width="480"/>
</div>
<br>

<div align="center">
  <img src="https://img.shields.io/badge/OS-Windows-blue?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/OS-Linux-yellow?logo=linux&logoColor=black" alt="Linux">

  <a href="https://github.com/zfoong/CraftBot">
    <img src="https://img.shields.io/github/stars/zfoong/CraftBot?style=social" alt="GitHub Repo stars">
  </a>

  <img src="https://img.shields.io/github/license/zfoong/CraftBot" alt="License">

  <a href="https://discord.gg/ZN9YHc37HG">
    <img src="https://img.shields.io/badge/Discord-%E5%8A%A0%E5%85%A5%E7%A4%BE%E5%8C%BA-5865F2?logo=discord&logoColor=white" alt="Discord">
  </a>
<br/>
<br/>

[![SPONSORED BY E2B FOR STARTUPS](https://img.shields.io/badge/SPONSORED%20BY-E2B%20FOR%20STARTUPS-ff8800?style=for-the-badge)](https://e2b.dev/startups)
</div>

<p align="center">
  <a href="README.md"> English README</a> | <a href="README.ja.md"> 日本語版はこちら</a>
</p>

## 🚀 概览
<h3 align="center">
CraftBot 是你的个人 AI 助手，它驻留在你的设备中，全天候为你服务。
</h3>

它能够自主理解任务、规划行动并执行操作，以实现你的目标。

在你的设备或独立环境中部署 CraftBot。通过 TUI 界面或你喜爱的消息应用与它交互。通过 MCP 和技能扩展代理的能力，连接 Google Workspace、Slack、Notion、Telegram 等工具以扩大其触及范围。CraftBot 会智能地在 CLI 模式（用于标准任务）和 GUI 模式（需要屏幕交互时）之间切换。GUI 模式在隔离环境中运行，不会打扰你的工作。

CraftBot 静候你的指令，现在就部署属于你的 CraftBot 吧。

---

## ✨ 特性

- **CLI/GUI 模式** — 代理根据任务复杂度智能切换 CLI 和 GUI 模式。GUI 模式支持完整的桌面自动化，包括屏幕捕获、鼠标/键盘控制和窗口管理。
- **多 LLM 支持** — 灵活的 LLM 提供商系统，支持 OpenAI、Google Gemini、Anthropic Claude、BytePlus 和本地 Ollama 模型。可轻松切换提供商。
- **37+ 内置动作** — 全面的动作库，包括：
  - **文件操作**：查找、读取、写入、搜索和转换文件
  - **网络功能**：HTTP 请求、网页搜索、PDF 生成、图像生成
  - **GUI 自动化**：鼠标点击、键盘输入、截图、窗口控制
  - **应用控制**：打开应用、管理窗口、剪贴板操作
- **持久化记忆** — 基于 RAG 的语义记忆系统，由 ChromaDB 驱动。代理可跨会话记忆上下文，支持智能检索和增量更新。
- **外部工具集成** — 连接 Google Workspace、Slack、Notion、Zoom、LinkedIn、Discord 和 Telegram（更多即将推出！），支持嵌入式凭据和 OAuth。
- **MCP** — 模型上下文协议（Model Context Protocol）集成，通过外部工具和服务扩展代理能力。
- **技能系统** — 可扩展的技能框架，内置任务规划、研究、代码审查、Git 操作等技能。
- **跨平台** — 完整支持 Windows 和 Linux，具有平台特定代码变体和 Docker 容器化。

> [!IMPORTANT]
> **关于 GUI 模式的说明：** GUI 模式仍处于实验阶段。代理切换到 GUI 模式时可能会遇到一些问题。我们正在积极改进此功能。

---

## 🧩 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    用户界面层                                 │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │  TUI (Textual)   │  │  GUI 模块 (Docker + Gradio)       │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      代理基础层                               │
│           (任务编排与生命周期管理)                              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────┬──────────┼──────────┬─────────┐
        ▼         ▼          ▼          ▼         ▼
   ┌─────────┐ ┌────────┐ ┌────────┐ ┌───────┐ ┌────────┐
   │   LLM   │ │ 上下文  │ │  动作  │ │ 事件  │ │  记忆  │
   │  接口   │ │  引擎   │ │  管理  │ │  流   │ │ (RAG)  │
   └─────────┘ └────────┘ └────────┘ └───────┘ └────────┘
```

| 组件 | 说明 |
|-----------|-------------|
| **代理基础层 (Agent Base)** | 核心编排层，管理任务生命周期、协调各组件并处理主要的代理循环。 |
| **LLM 接口** | 统一接口，支持多个 LLM 提供商（OpenAI、Gemini、Anthropic、BytePlus、Ollama）。 |
| **上下文引擎** | 生成优化的提示词，支持 KV-cache。 |
| **动作管理器** | 从动作库中检索和执行动作。自定义动作易于扩展。 |
| **动作路由器** | 根据任务需求智能选择最佳匹配的动作，需要时通过 LLM 解析输入参数。 |
| **事件流** | 实时事件发布系统，用于任务进度跟踪、UI 更新和执行监控。 |
| **记忆管理器** | 基于 RAG 的语义记忆，使用 ChromaDB。处理记忆分块、向量化、检索和增量更新。 |
| **状态管理器** | 全局状态管理，跟踪代理执行上下文、对话历史和运行时配置。 |
| **任务管理器** | 管理任务定义，支持简单和复杂任务模式，创建待办事项，多步骤工作流跟踪。 |
| **技能管理器** | 加载并将可插拔技能注入代理上下文。 |
| **MCP 适配器** | 模型上下文协议集成，将 MCP 工具转换为原生动作。 |
| **TUI 界面** | 基于 Textual 框架构建的终端用户界面，用于交互式命令行操作。 |
| **GUI 模块** | 实验性 GUI 自动化，使用 Docker 容器、OmniParser 进行 UI 元素检测，以及 Gradio 客户端。 |

---

## 🔜 路线图

- [X] **记忆模块** — 已完成。
- [ ] **外部工具集成** — 持续添加中！
- [X] **MCP 层** — 已完成。
- [X] **技能层** — 已完成。
- [ ] **主动式行为** — 待定

---

## 🧰 环境设置

### 前置要求
- Python **3.9+**
- `git`、`conda`、`pip`
- 你所选 LLM 提供商的 API Key（例如 OpenAI 或 Gemini）

### 安装
```bash
git clone https://github.com/zfoong/CraftBot.git
cd CraftBot
conda env create -f environment.yml
```

---

## ⚡ 快速上手

导出你的 API Key：
```bash
export OPENAI_API_KEY=<YOUR_KEY_HERE>
或
export GOOGLE_API_KEY=<YOUR_KEY_HERE>
```
运行：
```bash
python start.py
```

这会启动内置的 **CraftBot**，你可以与它沟通：
1. 与代理对话
2. 让它执行复杂的任务序列
3. 运行命令 /help 获取帮助
4. 与 AI 代理协作
5. 通过专用但轻量的 WebRTC Linux 虚拟机执行高级 computer-use 任务

### 终端参数
| 参数 | 说明 |
| :--- | :--- |
| `--only-cpu` | 以 CPU 模式运行代理 |
| `--fast` | 跳过不必要的更新检查，更快启动代理。<br> <u><b>注意：</b></u> 首次启动时必须不使用 `--fast` |
| `--no-omniparser` | 禁用 Microsoft OmniParser 分析 UI - 这会大幅降低 GUI 动作准确度。强烈建议使用 OmniParser |
| `--no-conda` | 将所有包安装到全局环境而非 conda 环境中 |
| `--no-gui` | 禁用 GUI 模式。代理将以纯 CLI 模式运行，无法切换到 GUI 模式。此设置在重启后仍然保留。OmniParser 也会自动禁用 |
| `--enable-gui` | 重新启用之前通过 `--no-gui` 禁用的 GUI 模式。此设置在重启后仍然保留 |

**示例**
```bash
python start.py --only-cpu --fast
```

> [!HINT]
> **首次引导：** 首次启动 CraftBot 会触发引导流程，你将设置 API Key、代理名称、MCP 和技能。然后，首次与 CraftBot 聊天会启动一个面试环节，以便它更新 USER.md 和 AGENT.md 供将来参考。

---

## 🔐 OAuth 设置（可选）

代理可以使用 OAuth 连接各种服务。正式版本附带嵌入式凭据，但你也可以使用自己的凭据。

### 快速开始

对于附带嵌入式凭据的正式版本：
```
/google login    # 连接 Google Workspace
/zoom login      # 连接 Zoom
/slack invite    # 连接 Slack
/notion invite   # 连接 Notion
/linkedin login  # 连接 LinkedIn
```

### 服务详情

| 服务 | 认证类型 | 命令 | 需要密钥？ |
|---------|-----------|---------|------------------|
| Google | PKCE | `/google login` | 否 (PKCE) |
| Zoom | PKCE | `/zoom login` | 否 (PKCE) |
| Slack | OAuth 2.0 | `/slack invite` | 是 |
| Notion | OAuth 2.0 | `/notion invite` | 是 |
| LinkedIn | OAuth 2.0 | `/linkedin login` | 是 |

### 使用自己的凭据

如果你想使用自己的 OAuth 凭据，请将它们添加到 `.env` 文件中：

#### Google（PKCE - 仅需 Client ID）
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 启用 Gmail、Calendar、Drive 和 People API
3. 创建 OAuth 凭据，类型选择 **桌面应用**
4. 复制 Client ID（PKCE 不需要密钥）

#### Zoom（PKCE - 仅需 Client ID）
```bash
ZOOM_CLIENT_ID=your-zoom-client-id
```
1. 前往 [Zoom Marketplace](https://marketplace.zoom.us/)
2. 创建 OAuth 应用
3. 复制 Client ID

#### Slack（需要两者）
```bash
SLACK_SHARED_CLIENT_ID=your-slack-client-id
SLACK_SHARED_CLIENT_SECRET=your-slack-client-secret
```
1. 前往 [Slack API](https://api.slack.com/apps)
2. 创建新应用
3. 添加 OAuth 范围：`chat:write`、`channels:read`、`users:read` 等
4. 复制 Client ID 和 Client Secret

#### Notion（需要两者）
```bash
NOTION_SHARED_CLIENT_ID=your-notion-client-id
NOTION_SHARED_CLIENT_SECRET=your-notion-client-secret
```
1. 前往 [Notion Developers](https://developers.notion.com/)
2. 创建新集成（公共集成）
3. 复制 OAuth Client ID 和 Secret

#### LinkedIn（需要两者）
```bash
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
```
1. 前往 [LinkedIn Developers](https://developer.linkedin.com/)
2. 创建应用
3. 添加 OAuth 2.0 范围
4. 复制 Client ID 和 Client Secret

---
## 使用容器运行

仓库根目录包含 Docker 配置：使用 Python 3.10、关键系统依赖（包含用于 OCR 的 Tesseract），以及在 `environment.yml`/`requirements.txt` 中定义的所有 Python 库，从而让代理在隔离环境中保持一致运行。

下面是在容器中运行代理的配置步骤。

### 构建镜像

在仓库根目录执行：

```bash
docker build -t craftbot .
```

### 运行容器

镜像默认会用 `python -m core.main` 启动代理。要交互式运行：

```bash
docker run --rm -it craftbot
```

如果需要传入环境变量，可使用 env 文件（例如基于 `.env.example`）：

```bash
docker run --rm -it --env-file .env craftbot
```

使用 `-v` 挂载需要在容器外持久化的目录（例如数据或缓存文件夹），并根据部署需要调整端口或额外参数。该容器内置 OCR（`tesseract`）、屏幕自动化（`pyautogui`、`mss`、X11 工具与虚拟帧缓冲）以及常见 HTTP 客户端等系统依赖，使代理能够在容器中处理文件、网络 API 与 GUI 自动化。

### 启用 GUI/屏幕自动化

GUI 操作（鼠标/键盘事件、截图）需要 X11 服务器。你可以连接宿主机显示，或使用 `xvfb` 无头运行：

* 使用宿主机显示（需要带 X11 的 Linux）：

  ```bash
  docker run --rm -it
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/data:/app/core/data \
    craftbot
  ```

  如需让代理读写更多目录，可添加额外的 `-v` 挂载。

* 使用虚拟显示进行无头运行：

  ```bash
	docker run --rm -it --env-file .env craftbot bash -lc "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && exec python -m core.main"
  ```

默认情况下镜像会使用 Python 3.10，并打包了 `environment.yml`/`requirements.txt` 中的 Python 依赖，因此 `python -m core.main` 可开箱即用。

---

## 🤝 如何贡献

欢迎各种建议与反馈！你可以联系 [@zfoong](https://github.com/zfoong)，邮箱为 thamyikfoong(at)craftos.net。我们目前尚未配置检查流程，因此无法接受直接提交贡献，但非常感谢你的建议与反馈。

## 🧾 许可证

本项目采用 [MIT License](LICENSE) 许可。你可以自由使用、部署并将其商业化（在分发与商业化时必须注明本项目来源）。

---

## ⭐ 致谢

由 [CraftOS](https://craftos.net/) 与贡献者 [@zfoong](https://github.com/zfoong) 及 [@ahmad-ajmal](https://github.com/ahmad-ajmal) 开发与维护。
如果你觉得 **CraftBot** 有用，请给仓库点一个 ⭐ 并分享给更多人！
