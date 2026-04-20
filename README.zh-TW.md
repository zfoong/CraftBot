
<div align="center">
    <img src="assets/craftbot_readme_banner.png" alt="CraftBot Banner" width="1280"/>
</div>
<br>

<div align="center">
  <img src="https://img.shields.io/badge/OS-Windows-blue?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/OS-macOS-lightgrey?logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/OS-Linux-yellow?logo=linux&logoColor=black" alt="Linux">

  <a href="https://github.com/CraftOS-dev/CraftBot">
    <img src="https://img.shields.io/github/stars/CraftOS-dev/CraftBot?style=social" alt="GitHub Repo stars">
  </a>

  <img src="https://img.shields.io/github/license/CraftOS-dev/CraftBot" alt="License">

  <a href="https://discord.gg/ZN9YHc37HG">
    <img src="https://img.shields.io/badge/Discord-%E5%8A%A0%E5%85%A5%E7%A4%BE%E7%BE%A4-5865F2?logo=discord&logoColor=white" alt="Discord">
  </a>
<br/>
<br/>

[![SPONSORED BY E2B FOR STARTUPS](https://img.shields.io/badge/SPONSORED%20BY-E2B%20FOR%20STARTUPS-ff8800?style=for-the-badge)](https://e2b.dev/startups)

<a href="https://www.producthunt.com/products/craftbot?embed=true&amp;utm_source=badge-top-post-badge&amp;utm_medium=badge&amp;utm_campaign=badge-craftbot" target="_blank" rel="noopener noreferrer"><img alt="CraftBot - Self-hosted proactive AI assistant that lives locally | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1110300&amp;theme=dark&amp;period=daily&amp;t=1776679679509"></a>
</div>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.cn.md">简体中文</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a>
</p>

## 🚀 概覽
<h3 align="center">
CraftBot 是你的個人 AI 助理，它駐留在你的裝置中，全天候為你服務。
</h3>

它會自主解讀任務、規劃行動並執行它們，協助你達成目標。
它會學習你的偏好與目標，主動協助你規劃並展開任務，幫助你實現人生目標。
支援 MCP、技能（Skills）以及外部應用整合。

CraftBot 正在等待你的指令，立刻建立屬於你自己的 CraftBot 吧。

<div align="center">
    <img src="assets/craftbot_overview.png" alt="CraftBot Overview" width="1280"/>
</div>

---

## ✨ 功能特色

- **自帶金鑰（BYOK）** — 靈活的 LLM 供應商系統，支援 OpenAI、Google Gemini、Anthropic Claude、BytePlus 及本地 Ollama 模型，可輕鬆切換。
- **記憶系統** — 每天午夜時分提煉並整合當日所發生的事件。
- **主動式代理人** — 學習你的偏好、習慣與人生目標，接著進行規劃並（在取得同意後）主動啟動任務，協助你在生活中不斷進步。
- **外部工具整合** — 連接 Google Workspace、Slack、Notion、Zoom、LinkedIn、Discord 及 Telegram（更多服務陸續推出！），內建憑證與 OAuth 支援。
- **MCP** — 整合 Model Context Protocol，以外部工具與服務擴充代理人的能力。
- **技能（Skills）** — 可擴充的技能框架，內建任務規劃、研究、程式碼審查、Git 操作等多種技能。
- **跨平台** — 完整支援 Windows、macOS 與 Linux，並提供對應的平台程式碼與 Docker 容器化。

> [!IMPORTANT]
> **關於 GUI 模式：** GUI 模式目前仍處於實驗階段。當代理人切換到 GUI 模式時可能會遇到問題。我們正在持續改進此功能。

<div align="center">
    <img src="assets/craftbot_readme_features.png" alt="CraftBot Banner" width="1280"/>
	<img src="assets/craftbot_features_custom.png" alt="CraftBot Banner" width="1280"/>
</div>

---


## 🧰 快速開始

### 先決條件
- Python **3.10+**
- `git`（複製儲存庫時需要）
- 所選 LLM 供應商的 API 金鑰（OpenAI、Gemini 或 Anthropic）
- `Node.js` **18+**（選用——僅於使用瀏覽器介面時需要）
- `conda`（選用——若未安裝，安裝程式可代為安裝 Miniconda）

### 快速安裝

```bash
# 複製儲存庫
git clone https://github.com/CraftOS-dev/CraftBot.git
cd CraftBot

# 安裝相依套件
python install.py

# 執行代理人
python run.py
```

這樣就完成了！首次執行時會引導你設定 API 金鑰。

**注意：** 若尚未安裝 Node.js，安裝程式會提供逐步指引。你也可以跳過瀏覽器模式，改用 TUI（請見下方模式說明）。

### 立即能做什麼？
- 用自然語言與代理人對話
- 請它執行複雜的多步驟任務
- 輸入 `/help` 查看可用指令
- 連接 Google、Slack、Notion 等服務

### 🖥️ 介面模式

<div align="center">
    <img src="assets/WCA_README_banner.png" alt="CraftOS Banner" width="1280"/>
</div>

CraftBot 支援多種 UI 模式，可依個人偏好選擇：

| 模式 | 指令 | 需求 | 適用情境 |
|------|---------|--------------|----------|
| **Browser** | `python run.py` | Node.js 18+ | 現代化網頁介面，最易使用 |
| **TUI** | `python run.py --tui` | 無 | 終端機 UI，無須額外相依套件 |
| **CLI** | `python run.py --cli` | 無 | 命令列，輕量化 |
| **GUI** | `python run.py --gui` | `install.py --gui` | 帶視覺回饋的桌面自動化 |

**Browser 模式**為預設與建議選項。若沒有 Node.js，安裝程式會提供安裝指引，或你可改用 **TUI 模式**。

---

## 🧩 架構概覽

| 元件 | 說明 |
|-----------|-------------|
| **Agent Base** | 負責管理任務生命週期、協調各元件並處理主要代理人迴圈的核心編排層。 |
| **LLM Interface** | 支援多家 LLM 供應商（OpenAI、Gemini、Anthropic、BytePlus、Ollama）的統一介面。 |
| **Context Engine** | 產生最佳化的 Prompt，支援 KV-Cache。 |
| **Action Manager** | 從動作庫中擷取並執行動作，方便擴充自訂動作。 |
| **Action Router** | 依任務需求智慧挑選最合適的動作，並在需要時透過 LLM 解析輸入參數。 |
| **Event Stream** | 即時事件發佈系統，用於任務進度追蹤、UI 更新與執行監控。 |
| **Memory Manager** | 以 ChromaDB 為基礎的 RAG 語意記憶，處理記憶分塊、嵌入、檢索與增量更新。 |
| **State Manager** | 全域狀態管理，追蹤代理人執行脈絡、對話歷史與執行期設定。 |
| **Task Manager** | 管理任務定義，支援簡單與複雜任務模式、待辦清單建立，以及多步驟流程追蹤。 |
| **Skill Manager** | 載入並將可插拔技能注入到代理人情境中。 |
| **MCP Adapter** | Model Context Protocol 整合，將 MCP 工具轉換為原生動作。 |
| **TUI Interface** | 以 Textual 框架打造的終端機使用者介面，提供互動式命令列操作。 |
| **GUI Module** | 實驗性的 GUI 自動化，採用 Docker 容器、OmniParser（用於 UI 元素偵測）與 Gradio 用戶端。 |

---

## 🔜 藍圖

- [X] **記憶模組** — 完成。
- [ ] **外部工具整合** — 仍在持續新增！
- [X] **MCP 層** — 完成。
- [X] **技能層** — 完成。
- [X] **主動式行為** — 進行中

---

## 🖥️ GUI 模式（選用）

GUI 模式可啟用螢幕自動化——代理人能看見桌面並與其互動。此為選用功能，需要額外安裝。

```bash
# 安裝 GUI 支援（使用 pip，不需 conda）
python install.py --gui

# 安裝 GUI 支援並搭配 conda
python install.py --gui --conda

# 以 GUI 模式執行
python run.py --gui
```

> [!NOTE]
> GUI 模式屬於實驗性，需要額外相依套件（模型權重約 4GB）。若不需桌面自動化，請改用沒有額外相依套件的 Browser/TUI 模式。

---

## 📋 指令參考

### install.py

| 旗標 | 說明 |
|------|-------------|
| `--gui` | 安裝 GUI 元件（OmniParser） |
| `--conda` | 使用 conda 環境（選用） |
| `--cpu-only` | 僅安裝 CPU 版 PyTorch（需搭配 `--gui`） |

### run.py

| 旗標 | 說明 |
|------|-------------|
| （無） | 以 **Browser** 模式執行（建議，需 Node.js） |
| `--tui` | 以 **Terminal UI** 模式執行（無需額外相依） |
| `--cli` | 以 **CLI** 模式執行（輕量） |
| `--gui` | 啟用 GUI 自動化模式（需先執行 `install.py --gui`） |

### service.py

| 指令 | 說明 |
|---------|-------------|
| `install` | 安裝相依套件、註冊開機自動啟動，並啟動 CraftBot |
| `start` | 在背景啟動 CraftBot |
| `stop` | 停止 CraftBot |
| `restart` | 停止後重新啟動 |
| `status` | 顯示執行狀態與自動啟動狀態 |
| `logs [-n N]` | 顯示最後 N 行記錄（預設 50） |
| `uninstall` | 移除自動啟動註冊 |

**安裝範例：**
```bash
# 單純使用 pip 安裝（不使用 conda）
python install.py

# 安裝 GUI 支援（使用 pip，不使用 conda）
python install.py --gui

# 於僅 CPU 的系統安裝 GUI 支援（使用 pip，不使用 conda）
python install.py --gui --cpu-only

# 使用 conda 環境（建議給 conda 使用者）
python install.py --conda

# 同時啟用 GUI 與 conda
python install.py --gui --conda

# 於僅 CPU 的系統使用 GUI 及 conda
python install.py --gui --conda --cpu-only
```

**執行 CraftBot：**

```powershell
# Browser 模式（預設，需 Node.js）
python run.py

# TUI 模式（無需 Node.js）
python run.py --tui

# CLI 模式（輕量）
python run.py --cli

# GPU/GUI 模式
python run.py --gui

# 使用 conda 環境
conda run -n craftbot python run.py

# 若 conda 不在 PATH，使用完整路徑
&"$env:USERPROFILE\miniconda3\Scripts\conda.exe" run -n craftbot python run.py
```

**Linux/macOS（Bash）：**
```bash
# Browser 模式（預設，需 Node.js）
python run.py

# TUI 模式（無需 Node.js）
python run.py --tui

# CLI 模式（輕量）
python run.py --cli

# GPU/GUI 模式
python run.py --gui

# 使用 conda 環境
conda run -n craftbot python run.py
```

### 🔧 背景服務（建議）

將 CraftBot 當成背景服務執行，即使關閉終端機仍能持續運作。系統會自動建立桌面捷徑，讓你隨時可重新開啟瀏覽器。

```bash
# 安裝相依套件、註冊登入時自動啟動並啟動 CraftBot
python service.py install
```

這樣就完成了。終端機會自動關閉，CraftBot 在背景執行，瀏覽器也會自動開啟。

```bash
# 其他服務指令：
python service.py start    # 在背景啟動 CraftBot
python service.py status   # 檢查是否正在執行
python service.py stop     # 停止 CraftBot
python service.py restart  # 重新啟動 CraftBot
python service.py logs     # 檢視最近的記錄
```

| 指令 | 說明 |
|---------|-------------|
| `python service.py install` | 安裝相依套件、註冊登入時自動啟動、啟動 CraftBot、開啟瀏覽器並自動關閉終端機 |
| `python service.py start` | 在背景啟動 CraftBot——若已在執行，會自動重啟（終端機自動關閉） |
| `python service.py stop` | 停止 CraftBot |
| `python service.py restart` | 停止並重新啟動 CraftBot |
| `python service.py status` | 檢查 CraftBot 是否執行中，以及自動啟動是否啟用 |
| `python service.py logs` | 顯示最近的記錄（使用 `-n 100` 顯示更多行） |
| `python service.py uninstall` | 停止 CraftBot、移除自動啟動註冊、解除 pip 套件並清除 pip 快取 |

> [!TIP]
> 執行 `service.py start` 或 `service.py install` 後，會自動建立 **CraftBot 桌面捷徑**。若不小心關閉了瀏覽器，雙擊捷徑即可重新開啟。

> [!NOTE]
> **安裝：** 若相依套件缺失，安裝程式會提供清楚的指引。若找不到 Node.js，會提示你安裝或切換至 TUI 模式。安裝程式會自動偵測 GPU 是否可用，必要時會自動回退至 CPU 模式。

> [!TIP]
> **首次設定：** CraftBot 會引導你完成初始化流程，包含設定 API 金鑰、代理人名稱、MCP 與技能。

> [!NOTE]
> **Playwright Chromium：** 整合 WhatsApp Web 時選用。若安裝失敗，代理人仍可正常執行其他任務。稍後可以手動安裝：`playwright install chromium`。

---

## � 疑難排解與常見問題

### 缺少 Node.js（Browser 模式）
若執行 `python run.py` 時看到 **"npm not found in PATH"**：
1. 從 [nodejs.org](https://nodejs.org/) 下載（建議 LTS 版本）
2. 安裝完成後重新啟動終端機
3. 再次執行 `python run.py`

**替代方案：** 改用 TUI 模式（不需 Node.js）：
```bash
python run.py --tui
```

### 相依套件安裝失敗
安裝程式現在會提供詳細錯誤訊息及解決方案。若安裝失敗：
- **確認 Python 版本：** 確保安裝 Python 3.10+（`python --version`）
- **檢查網路連線：** 安裝過程需下載相依套件
- **清除 pip 快取：** 執行 `pip install --upgrade pip` 後再試

### Playwright 安裝問題
Playwright chromium 為選用安裝，若失敗：
- 代理人的其他功能**仍可正常運作**
- 可先跳過，日後再安裝：`playwright install chromium`
- 僅於整合 WhatsApp Web 時需要

### GPU/CUDA 問題
安裝程式會自動偵測 GPU：
- CUDA 安裝失敗時會自動切換至 CPU 模式
- 手動 CPU 安裝：`python install.py --gui --cpu-only`

更多疑難排解請參閱 [INSTALLATION_FIX.md](INSTALLATION_FIX.md)。

---

代理人可透過 OAuth 連接多種服務。Release 版本內建憑證，但你也可以使用自己的憑證。

### 快速上手

若使用內建憑證的 Release 版本：
```
/google login    # 連接 Google Workspace
/zoom login      # 連接 Zoom
/slack invite    # 連接 Slack
/notion invite   # 連接 Notion
/linkedin login  # 連接 LinkedIn
```

### 服務細節

| 服務 | 驗證方式 | 指令 | 是否需要密鑰？ |
|---------|-----------|---------|------------------|
| Google | PKCE | `/google login` | 否（PKCE） |
| Zoom | PKCE | `/zoom login` | 否（PKCE） |
| Slack | OAuth 2.0 | `/slack invite` | 是 |
| Notion | OAuth 2.0 | `/notion invite` | 是 |
| LinkedIn | OAuth 2.0 | `/linkedin login` | 是 |

### 使用自己的憑證

若希望使用自己的 OAuth 憑證，請將其加入 `.env` 檔：

#### Google（PKCE，只需 Client ID）
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 啟用 Gmail、Calendar、Drive 與 People API
3. 建立 OAuth 憑證，類型選 **Desktop app**
4. 複製 Client ID（PKCE 不需 secret）

#### Zoom（PKCE，只需 Client ID）
```bash
ZOOM_CLIENT_ID=your-zoom-client-id
```
1. 前往 [Zoom Marketplace](https://marketplace.zoom.us/)
2. 建立 OAuth 應用程式
3. 複製 Client ID

#### Slack（兩者皆需）
```bash
SLACK_SHARED_CLIENT_ID=your-slack-client-id
SLACK_SHARED_CLIENT_SECRET=your-slack-client-secret
```
1. 前往 [Slack API](https://api.slack.com/apps)
2. 建立新應用程式
3. 新增 OAuth 範圍：`chat:write`、`channels:read`、`users:read` 等
4. 複製 Client ID 與 Client Secret

#### Notion（兩者皆需）
```bash
NOTION_SHARED_CLIENT_ID=your-notion-client-id
NOTION_SHARED_CLIENT_SECRET=your-notion-client-secret
```
1. 前往 [Notion Developers](https://developers.notion.com/)
2. 建立新的整合（Public integration）
3. 複製 OAuth Client ID 與 Secret

#### LinkedIn（兩者皆需）
```bash
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
```
1. 前往 [LinkedIn Developers](https://developer.linkedin.com/)
2. 建立應用程式
3. 新增 OAuth 2.0 範圍
4. 複製 Client ID 與 Client Secret

---
## 使用容器執行

儲存庫根目錄提供 Docker 設定，內含 Python 3.10、OCR 用的 Tesseract 等關鍵系統套件，以及 `environment.yml`/`requirements.txt` 中定義的所有 Python 相依套件，讓代理人可在隔離環境中穩定執行。

以下是透過容器執行代理人的設定說明。

### 建置映像檔

於儲存庫根目錄執行：

```bash
docker build -t craftbot .
```

### 執行容器

映像檔預設會以 `python -m app.main` 啟動代理人。若要以互動方式執行：

```bash
docker run --rm -it craftbot
```

若需傳入環境變數，可透過 env 檔（例如以 `.env.example` 為基礎）：

```bash
docker run --rm -it --env-file .env craftbot
```

可使用 `-v` 掛載需要保存在容器外的目錄（如資料或快取資料夾），並依部署需求調整連接埠或其他旗標。映像檔內建 OCR（`tesseract`）、螢幕自動化（`pyautogui`、`mss`、X11 工具與虛擬 framebuffer）以及常見 HTTP 用戶端等系統相依，能讓代理人在容器中處理檔案、網路 API 與 GUI 自動化。

### 啟用 GUI／螢幕自動化

GUI 動作（滑鼠／鍵盤事件、截圖）需要 X11 伺服器。你可以連接到主機顯示或使用 `xvfb` 以無頭方式執行：

* 使用主機顯示（需 Linux 搭配 X11）：

  ```bash
  docker run --rm -it 
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/data:/app/app/data \
    craftbot
  ```

  針對代理人需要讀寫的資料夾，可再新增 `-v` 掛載。

* 以虛擬顯示無頭執行：

  ```bash
	docker run --rm -it --env-file .env craftbot bash -lc "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && exec python -m app.main"
  ```

映像檔預設使用 Python 3.10，並內建 `environment.yml`/`requirements.txt` 中的 Python 相依套件，因此 `python -m app.main` 可直接運作。

---

## 🤝 如何貢獻

歡迎提交 PR！詳細流程（fork → 由 `dev` 建分支 → 提 PR）請見 [CONTRIBUTING.md](CONTRIBUTING.md)。所有 Pull Request 都會自動執行 lint 與 smoke-test CI。如果你有任何疑問，或想更快速地溝通，歡迎加入 [Discord](https://discord.gg/ZN9YHc37HG) 或寄信至 thamyikfoong(at)craftos.net。

## 🧾 授權條款

本專案採用 [MIT 授權條款](LICENSE)。你可以自由使用、部署並商業化本專案（如需散佈或商業化，請註明出處）。

---

## ⭐ 致謝

本專案由 [CraftOS](https://craftos.net/) 與貢獻者 [@zfoong](https://github.com/zfoong)、[@ahmad-ajmal](https://github.com/ahmad-ajmal) 共同開發與維護。
如果你覺得 **CraftBot** 好用，歡迎為儲存庫按下 ⭐ 並分享給更多人！
