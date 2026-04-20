
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
    <img src="https://img.shields.io/badge/Discord-Join%20the%20community-5865F2?logo=discord&logoColor=white" alt="Discord">
  </a>
<br/>
<br/>

[![SPONSORED BY E2B FOR STARTUPS](https://img.shields.io/badge/SPONSORED%20BY-E2B%20FOR%20STARTUPS-ff8800?style=for-the-badge)](https://e2b.dev/startups)

<a href="https://www.producthunt.com/products/craftbot?embed=true&amp;utm_source=badge-top-post-badge&amp;utm_medium=badge&amp;utm_campaign=badge-craftbot" target="_blank" rel="noopener noreferrer"><img alt="CraftBot - Self-hosted proactive AI assistant that lives locally | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1110300&amp;theme=dark&amp;period=daily&amp;t=1776679679509"></a>
</div>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.cn.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.es.md">Español</a>
</p>

## 🚀 개요
<h3 align="center">
CraftBot은 당신의 기기 안에 상주하며 24시간 내내 당신을 위해 일하는 개인 AI 어시스턴트입니다.
</h3>

CraftBot은 작업을 자율적으로 해석하고, 행동을 계획하며, 당신의 목표를 달성하기 위해 이를 실행합니다.
사용자의 선호도와 목표를 학습하여, 삶의 목표를 이루도록 작업을 계획하고 능동적으로 시작하는 것을 도와줍니다.
MCP, 스킬, 그리고 외부 앱 통합을 지원합니다.

CraftBot이 당신의 명령을 기다리고 있습니다. 지금 나만의 CraftBot을 설정해 보세요.

<div align="center">
    <img src="assets/craftbot_overview.png" alt="CraftBot Overview" width="1280"/>
</div>

---

## ✨ 주요 기능

- **Bring Your Own Key (BYOK)** — OpenAI, Google Gemini, Anthropic Claude, BytePlus, 로컬 Ollama 모델을 지원하는 유연한 LLM 제공자 시스템. 제공자 간 손쉬운 전환이 가능합니다.
- **메모리 시스템** — 하루 동안 발생한 사건들을 자정에 정제하고 통합합니다.
- **능동형 에이전트(Proactive Agent)** — 사용자의 선호도, 습관, 인생 목표를 학습합니다. 그리고 (물론 승인을 받은 뒤) 계획을 수행하고 작업을 시작하여 삶을 개선하도록 도와줍니다.
- **외부 도구 통합** — Google Workspace, Slack, Notion, Zoom, LinkedIn, Discord, Telegram과 연결됩니다(계속 추가 예정!). 내장된 자격 증명 및 OAuth가 지원됩니다.
- **MCP** — 외부 도구 및 서비스로 에이전트 기능을 확장하기 위한 Model Context Protocol 통합.
- **스킬(Skills)** — 작업 계획, 리서치, 코드 리뷰, Git 작업 등 내장 스킬을 갖춘 확장형 스킬 프레임워크.
- **크로스 플랫폼** — 플랫폼별 코드 변형 및 Docker 컨테이너화를 통해 Windows, macOS, Linux를 완벽하게 지원합니다.

> [!IMPORTANT]
> **GUI 모드 안내:** GUI 모드는 아직 실험 단계입니다. 이로 인해 에이전트가 GUI 모드로 전환할 때 문제가 발생할 수 있습니다. 현재 활발히 개선 중입니다.

<div align="center">
    <img src="assets/craftbot_readme_features.png" alt="CraftBot Banner" width="1280"/>
	<img src="assets/craftbot_features_custom.png" alt="CraftBot Banner" width="1280"/>
</div>

---


## 🧰 시작하기

### 필수 요구 사항
- Python **3.10+**
- `git` (리포지토리 클론 시 필요)
- 사용할 LLM 제공자의 API 키(OpenAI, Gemini 또는 Anthropic)
- `Node.js` **18+** (선택 사항 - 브라우저 인터페이스 사용 시에만 필요)
- `conda` (선택 사항 - 없을 경우 설치 프로그램이 Miniconda 자동 설치를 제안합니다)

### 빠른 설치

```bash
# 리포지토리 클론
git clone https://github.com/CraftOS-dev/CraftBot.git
cd CraftBot

# 의존성 설치
python install.py

# 에이전트 실행
python run.py
```

이게 전부입니다! 첫 실행 시 API 키 설정 과정을 안내해 줍니다.

**참고:** Node.js가 설치되어 있지 않다면 설치 프로그램이 단계별로 안내해 드립니다. 브라우저 모드를 건너뛰고 TUI를 사용할 수도 있습니다(아래 모드 참고).

### 바로 할 수 있는 일
- 에이전트와 자연스럽게 대화
- 복잡한 다단계 작업 요청
- `/help`를 입력해 사용 가능한 명령 확인
- Google, Slack, Notion 등과 연결

### 🖥️ 인터페이스 모드

<div align="center">
    <img src="assets/WCA_README_banner.png" alt="CraftOS Banner" width="1280"/>
</div>

CraftBot은 여러 UI 모드를 지원합니다. 선호에 따라 선택하세요.

| 모드 | 명령어 | 요구 사항 | 적합한 용도 |
|------|---------|--------------|----------|
| **Browser** | `python run.py` | Node.js 18+ | 최신 웹 인터페이스, 가장 사용하기 쉬움 |
| **TUI** | `python run.py --tui` | 없음 | 터미널 UI, 별도 의존성 불필요 |
| **CLI** | `python run.py --cli` | 없음 | 커맨드라인, 경량 |
| **GUI** | `python run.py --gui` | `install.py --gui` | 시각적 피드백이 있는 데스크톱 자동화 |

**브라우저 모드**가 기본이자 권장 모드입니다. Node.js가 없는 경우 설치 프로그램이 설치 안내를 제공하거나, 대신 **TUI 모드**를 사용할 수 있습니다.

---

## 🧩 아키텍처 개요

| 구성 요소 | 설명 |
|-----------|-------------|
| **Agent Base** | 작업 라이프사이클을 관리하고 구성 요소 간 조정을 담당하며 주요 에이전틱 루프를 처리하는 핵심 오케스트레이션 계층. |
| **LLM Interface** | 여러 LLM 제공자(OpenAI, Gemini, Anthropic, BytePlus, Ollama)를 지원하는 통합 인터페이스. |
| **Context Engine** | KV 캐시를 지원하는 최적화된 프롬프트를 생성합니다. |
| **Action Manager** | 라이브러리에서 액션을 가져와 실행합니다. 커스텀 액션을 쉽게 확장할 수 있습니다. |
| **Action Router** | 작업 요구 사항에 가장 잘 맞는 액션을 지능적으로 선택하고, 필요 시 LLM을 통해 입력 매개변수를 해결합니다. |
| **Event Stream** | 작업 진행 추적, UI 업데이트, 실행 모니터링을 위한 실시간 이벤트 게시 시스템. |
| **Memory Manager** | ChromaDB 기반의 RAG 시맨틱 메모리. 메모리 청킹, 임베딩, 검색, 점진적 업데이트를 처리합니다. |
| **State Manager** | 에이전트 실행 컨텍스트, 대화 이력, 런타임 구성을 추적하는 전역 상태 관리. |
| **Task Manager** | 작업 정의를 관리하며 단순/복잡 작업 모드, 할 일 생성, 다단계 워크플로우 추적을 가능하게 합니다. |
| **Skill Manager** | 플러그형 스킬을 로드하여 에이전트 컨텍스트에 주입합니다. |
| **MCP Adapter** | MCP 도구를 네이티브 액션으로 변환하는 Model Context Protocol 통합. |
| **TUI Interface** | 대화형 커맨드라인 조작을 위해 Textual 프레임워크로 구축된 터미널 사용자 인터페이스. |
| **GUI Module** | Docker 컨테이너, UI 요소 감지를 위한 OmniParser, Gradio 클라이언트를 사용한 실험적 GUI 자동화. |

---

## 🔜 로드맵

- [X] **메모리 모듈** — 완료.
- [ ] **외부 도구 통합** — 계속 추가 중!
- [X] **MCP 레이어** — 완료.
- [X] **스킬 레이어** — 완료.
- [X] **능동형 동작(Proactive Behaviour)** — 진행 중

---

## 🖥️ GUI 모드 (선택 사항)

GUI 모드는 화면 자동화를 지원합니다 — 에이전트가 데스크톱 환경을 보고 상호작용할 수 있습니다. 선택 사항이며 추가 설정이 필요합니다.

```bash
# GUI 지원 설치 (pip 사용, conda 불필요)
python install.py --gui

# GUI 지원과 conda를 함께 사용
python install.py --gui --conda

# GUI 모드로 실행
python run.py --gui
```

> [!NOTE]
> GUI 모드는 실험적이며 추가 의존성(모델 가중치로 약 4GB)이 필요합니다. 데스크톱 자동화가 필요하지 않다면 이를 건너뛰고 추가 의존성이 없는 Browser/TUI 모드를 사용하세요.

---

## 📋 명령어 레퍼런스

### install.py

| 플래그 | 설명 |
|------|-------------|
| `--gui` | GUI 구성 요소(OmniParser) 설치 |
| `--conda` | conda 환경 사용 (선택 사항) |
| `--cpu-only` | CPU 전용 PyTorch 설치 (`--gui`와 함께 사용) |

### run.py

| 플래그 | 설명 |
|------|-------------|
| (없음) | **Browser** 모드로 실행 (권장, Node.js 필요) |
| `--tui` | **터미널 UI** 모드로 실행 (의존성 불필요) |
| `--cli` | **CLI** 모드로 실행 (경량) |
| `--gui` | GUI 자동화 모드 활성화 (`install.py --gui` 선행 필요) |

### service.py

| 명령 | 설명 |
|---------|-------------|
| `install` | 의존성 설치, 자동 시작 등록, CraftBot 실행 |
| `start` | CraftBot을 백그라운드에서 실행 |
| `stop` | CraftBot 중지 |
| `restart` | 중지 후 다시 시작 |
| `status` | 실행 상태 및 자동 시작 상태 표시 |
| `logs [-n N]` | 마지막 N개의 로그 라인 표시 (기본값: 50) |
| `uninstall` | 자동 시작 등록 해제 |

**설치 예시:**
```bash
# 간단한 pip 설치 (conda 미사용)
python install.py

# GUI 지원 설치 (pip, conda 미사용)
python install.py --gui

# CPU 전용 시스템에서 GUI 지원 설치 (pip, conda 미사용)
python install.py --gui --cpu-only

# conda 환경 사용 (conda 사용자에게 권장)
python install.py --conda

# GUI 지원과 conda
python install.py --gui --conda

# CPU 전용 시스템에서 GUI와 conda 함께
python install.py --gui --conda --cpu-only
```

**CraftBot 실행:**

```powershell
# Browser 모드 (기본, Node.js 필요)
python run.py

# TUI 모드 (Node.js 불필요)
python run.py --tui

# CLI 모드 (경량)
python run.py --cli

# GPU/GUI 모드
python run.py --gui

# conda 환경에서 실행
conda run -n craftbot python run.py

# conda가 PATH에 없는 경우 전체 경로 사용
&"$env:USERPROFILE\miniconda3\Scripts\conda.exe" run -n craftbot python run.py
```

**Linux/macOS (Bash):**
```bash
# Browser 모드 (기본, Node.js 필요)
python run.py

# TUI 모드 (Node.js 불필요)
python run.py --tui

# CLI 모드 (경량)
python run.py --cli

# GPU/GUI 모드
python run.py --gui

# conda 환경에서 실행
conda run -n craftbot python run.py
```

### 🔧 백그라운드 서비스 (권장)

터미널을 닫아도 CraftBot이 계속 실행되도록 백그라운드 서비스로 실행합니다. 데스크톱 바로가기가 자동으로 생성되므로 언제든지 브라우저를 다시 열 수 있습니다.

```bash
# 의존성 설치, 로그인 시 자동 시작 등록, CraftBot 실행
python service.py install
```

이게 전부입니다. 터미널은 자동으로 닫히고, CraftBot은 백그라운드에서 실행되며, 브라우저가 자동으로 열립니다.

```bash
# 기타 서비스 명령:
python service.py start    # CraftBot을 백그라운드에서 시작
python service.py status   # 실행 여부 확인
python service.py stop     # CraftBot 중지
python service.py restart  # CraftBot 재시작
python service.py logs     # 최근 로그 출력 확인
```

| 명령 | 설명 |
|---------|-------------|
| `python service.py install` | 의존성 설치, 로그인 시 자동 시작 등록, CraftBot 실행, 브라우저 열기 후 터미널 자동 종료 |
| `python service.py start` | CraftBot을 백그라운드에서 시작 — 이미 실행 중이면 자동 재시작 (터미널 자동 종료) |
| `python service.py stop` | CraftBot 중지 |
| `python service.py restart` | CraftBot 중지 후 재시작 |
| `python service.py status` | CraftBot 실행 여부와 자동 시작 활성화 여부 확인 |
| `python service.py logs` | 최근 로그 출력 표시 (`-n 100`으로 더 많은 줄 표시) |
| `python service.py uninstall` | CraftBot 중지, 자동 시작 등록 해제, pip 패키지 제거 및 pip 캐시 정리 |

> [!TIP]
> `service.py start` 또는 `service.py install` 실행 후 **CraftBot 데스크톱 바로가기**가 자동으로 생성됩니다. 브라우저를 실수로 닫았다면 바로가기를 더블클릭해 다시 열 수 있습니다.

> [!NOTE]
> **설치:** 의존성이 누락된 경우 설치 프로그램이 명확한 안내를 제공합니다. Node.js가 없으면 설치 여부를 묻거나 TUI 모드로 전환할 수 있습니다. GPU 가용성을 자동으로 감지하고 필요한 경우 CPU 전용 모드로 대체합니다.

> [!TIP]
> **첫 실행 설정:** CraftBot은 API 키, 에이전트 이름, MCP, 스킬 설정을 위한 온보딩 과정을 안내합니다.

> [!NOTE]
> **Playwright Chromium:** WhatsApp Web 통합에 필요한 선택 사항입니다. 설치에 실패해도 다른 작업에서는 에이전트가 정상 작동합니다. 나중에 `playwright install chromium`으로 수동 설치할 수 있습니다.

---

## � 문제 해결 및 자주 발생하는 이슈

### Node.js 누락 (브라우저 모드용)
`python run.py` 실행 시 **"npm not found in PATH"** 오류가 보인다면:
1. [nodejs.org](https://nodejs.org/)에서 다운로드 (LTS 버전 권장)
2. 설치 후 터미널 재시작
3. `python run.py`를 다시 실행

**대안:** TUI 모드를 사용하세요 (Node.js 불필요):
```bash
python run.py --tui
```

### 의존성 설치 실패
설치 프로그램은 이제 해결 방법이 포함된 자세한 오류 메시지를 제공합니다. 설치가 실패한다면:
- **Python 버전 확인:** Python 3.10+인지 확인 (`python --version`)
- **인터넷 연결 확인:** 설치 중 의존성이 다운로드됩니다
- **pip 캐시 초기화:** `pip install --upgrade pip` 후 다시 시도

### Playwright 설치 문제
Playwright chromium 설치는 선택 사항입니다. 실패 시:
- 에이전트는 다른 작업에서 **정상 작동**합니다
- 건너뛰거나 나중에 설치 가능: `playwright install chromium`
- WhatsApp Web 통합에만 필요합니다

### GPU/CUDA 문제
설치 프로그램은 GPU 가용성을 자동으로 감지합니다:
- CUDA 설치가 실패하면 자동으로 CPU 모드로 대체됩니다
- CPU 수동 설정: `python install.py --gui --cpu-only`

자세한 문제 해결은 [INSTALLATION_FIX.md](INSTALLATION_FIX.md)를 참고하세요.

---

에이전트는 OAuth를 사용해 다양한 서비스에 연결할 수 있습니다. 릴리스 빌드에는 자격 증명이 내장되어 있지만, 자신의 자격 증명을 사용할 수도 있습니다.

### 빠른 시작

자격 증명이 내장된 릴리스 빌드의 경우:
```
/google login    # Google Workspace 연결
/zoom login      # Zoom 연결
/slack invite    # Slack 연결
/notion invite   # Notion 연결
/linkedin login  # LinkedIn 연결
```

### 서비스 세부 정보

| 서비스 | 인증 유형 | 명령 | 시크릿 필요? |
|---------|-----------|---------|------------------|
| Google | PKCE | `/google login` | 불필요 (PKCE) |
| Zoom | PKCE | `/zoom login` | 불필요 (PKCE) |
| Slack | OAuth 2.0 | `/slack invite` | 필요 |
| Notion | OAuth 2.0 | `/notion invite` | 필요 |
| LinkedIn | OAuth 2.0 | `/linkedin login` | 필요 |

### 자신의 자격 증명 사용하기

자체 OAuth 자격 증명을 사용하려면 `.env` 파일에 추가하세요.

#### Google (PKCE - Client ID만 필요)
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. Gmail, Calendar, Drive, People API 활성화
3. **데스크톱 앱** 유형으로 OAuth 자격 증명 생성
4. Client ID 복사 (PKCE에서는 시크릿 불필요)

#### Zoom (PKCE - Client ID만 필요)
```bash
ZOOM_CLIENT_ID=your-zoom-client-id
```
1. [Zoom Marketplace](https://marketplace.zoom.us/) 접속
2. OAuth 앱 생성
3. Client ID 복사

#### Slack (둘 다 필요)
```bash
SLACK_SHARED_CLIENT_ID=your-slack-client-id
SLACK_SHARED_CLIENT_SECRET=your-slack-client-secret
```
1. [Slack API](https://api.slack.com/apps) 접속
2. 새 앱 생성
3. OAuth 스코프 추가: `chat:write`, `channels:read`, `users:read` 등
4. Client ID와 Client Secret 복사

#### Notion (둘 다 필요)
```bash
NOTION_SHARED_CLIENT_ID=your-notion-client-id
NOTION_SHARED_CLIENT_SECRET=your-notion-client-secret
```
1. [Notion Developers](https://developers.notion.com/) 접속
2. 새 통합 생성 (Public integration)
3. OAuth Client ID와 Secret 복사

#### LinkedIn (둘 다 필요)
```bash
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
```
1. [LinkedIn Developers](https://developer.linkedin.com/) 접속
2. 앱 생성
3. OAuth 2.0 스코프 추가
4. Client ID와 Client Secret 복사

---
## 컨테이너로 실행하기

리포지토리 루트에는 Python 3.10, OCR을 위한 Tesseract를 포함한 주요 시스템 패키지, 그리고 `environment.yml`/`requirements.txt`에 정의된 모든 Python 의존성을 갖춘 Docker 구성이 포함되어 있습니다. 이를 통해 격리된 환경에서 에이전트를 일관되게 실행할 수 있습니다.

아래는 컨테이너로 에이전트를 실행하는 설정 방법입니다.

### 이미지 빌드

리포지토리 루트에서:

```bash
docker build -t craftbot .
```

### 컨테이너 실행

이 이미지는 기본적으로 `python -m app.main`으로 에이전트를 실행하도록 구성되어 있습니다. 대화형으로 실행하려면:

```bash
docker run --rm -it craftbot
```

환경 변수를 제공하려면 env 파일을 전달하세요 (예: `.env.example` 기반):

```bash
docker run --rm -it --env-file .env craftbot
```

컨테이너 외부에 유지해야 하는 디렉터리(데이터, 캐시 폴더 등)는 `-v`를 사용해 마운트하고, 배포 환경에 맞게 포트나 추가 플래그를 조정하세요. 이미지에는 OCR(`tesseract`), 화면 자동화(`pyautogui`, `mss`, X11 유틸리티, 가상 프레임버퍼), 일반 HTTP 클라이언트 등의 시스템 의존성이 포함되어 있어 컨테이너 내에서 파일, 네트워크 API, GUI 자동화를 모두 처리할 수 있습니다.

### GUI/화면 자동화 활성화

GUI 작업(마우스/키보드 이벤트, 스크린샷)은 X11 서버가 필요합니다. 호스트 디스플레이에 연결하거나 `xvfb`를 사용해 헤드리스로 실행할 수 있습니다.

* 호스트 디스플레이 사용 (X11이 있는 Linux 필요):

  ```bash
  docker run --rm -it 
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/data:/app/app/data \
    craftbot
  ```

  에이전트가 읽거나 쓸 폴더에 대해 추가 `-v` 마운트를 더해주세요.

* 가상 디스플레이로 헤드리스 실행:

  ```bash
	docker run --rm -it --env-file .env craftbot bash -lc "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && exec python -m app.main"
  ```

기본적으로 이미지는 Python 3.10을 사용하고 `environment.yml`/`requirements.txt`의 Python 의존성을 번들로 포함하므로 `python -m app.main`이 바로 동작합니다.

---

## 🤝 기여 방법

PR을 환영합니다! 워크플로우(포크 → `dev`에서 브랜치 생성 → PR)는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요. 모든 풀 리퀘스트는 린트 + 스모크 테스트 CI를 자동으로 거칩니다. 질문이 있거나 더 빠른 대화를 원하시면 [Discord](https://discord.gg/ZN9YHc37HG)에 참여하거나 thamyikfoong(at)craftos.net로 이메일을 보내주세요.

## 🧾 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)로 배포됩니다. 이 프로젝트를 자유롭게 사용, 호스팅, 수익화할 수 있습니다(배포 및 수익화 시 이 프로젝트를 크레딧으로 명시해야 합니다).

---

## ⭐ 감사의 말

[CraftOS](https://craftos.net/)와 기여자 [@zfoong](https://github.com/zfoong), [@ahmad-ajmal](https://github.com/ahmad-ajmal)이 개발 및 유지 관리하고 있습니다.
**CraftBot**이 유용하다고 느끼신다면 리포지토리에 ⭐를 눌러주시고 다른 분들에게도 공유해 주세요!
