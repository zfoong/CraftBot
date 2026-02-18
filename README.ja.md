
<div align="center">
    <img src="assets/WCA_README_banner.png" alt="CraftOS Banner" width="1280"/>
</div>
<br>
<div align="center">
    <img src="assets/craftbot_logo_text_small.png" alt="CraftBot Logo" width="480"/>
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
    <img src="https://img.shields.io/badge/Discord-Join%20the%20community-5865F2?logo=discord&logoColor=white" alt="Discord">
  </a>
<br/>
<br/>

[![SPONSORED BY E2B FOR STARTUPS](https://img.shields.io/badge/SPONSORED%20BY-E2B%20FOR%20STARTUPS-ff8800?style=for-the-badge)](https://e2b.dev/startups)
</div>

<p align="center">
  <a href="README.md">English version here</a> | <a href="README.cn.md"> 中文版README </a>
</p>

## 🚀 概要
<h3 align="center">
CraftBotは、あなたのマシンに常駐し、24時間365日働くパーソナルAIアシスタントです。
</h3>

タスクを自律的に解釈し、アクションを計画し、目標を達成するために実行します。

CraftBotをあなたのマシンまたは別の環境にセットアップしてください。TUIまたはお気に入りのメッセージングアプリからどこからでも対話できます。MCPとスキルでエージェントの機能を拡張し、Google Workspace、Slack、Notion、Telegramなどのツールに接続してその範囲を広げることができます。CraftBotは標準タスク用のCLIモードと画面操作が必要な場合のGUIモードをインテリジェントに切り替えます（GUIモードは隔離された環境で実行されるため、作業の邪魔になりません）。

CraftBotはあなたの命令を待っています。今すぐあなた専用のCraftBotをセットアップしましょう。

---

## ✨ 特徴

- **CLI/GUIモード** — エージェントはタスクの複雑さに応じてCLIモードとGUIモードをインテリジェントに切り替えます。GUIモードでは、画面キャプチャ、マウス/キーボード制御、ウィンドウ管理を含むフルデスクトップ自動化が可能です。
- **マルチLLMサポート** — OpenAI、Google Gemini、Anthropic Claude、BytePlus、ローカルOllamaモデルをサポートする柔軟なLLMプロバイダーシステム。プロバイダー間の切り替えが簡単です。
- **37以上の組み込みアクション** — 包括的なアクションライブラリ:
  - **ファイル操作**: ファイルの検索、読み取り、書き込み、grep、変換
  - **Web機能**: HTTPリクエスト、Web検索、PDF生成、画像生成
  - **GUI自動化**: マウスクリック、キーボード入力、スクリーンショット、ウィンドウ制御
  - **アプリケーション制御**: アプリの起動、ウィンドウ管理、クリップボード操作
- **永続メモリ** — ChromaDBを活用したRAGベースのセマンティックメモリシステム。エージェントはインテリジェントな検索と増分更新によりセッション間でコンテキストを記憶します。
- **外部ツール統合** — 埋め込みクレデンシャルとOAuthサポートにより、Google Workspace、Slack、Notion、Zoom、LinkedIn、Discord、Telegramに接続（今後さらに追加予定！）。
- **MCP** — 外部ツールやサービスでエージェント機能を拡張するためのModel Context Protocol統合。
- **スキル** — タスク計画、リサーチ、コードレビュー、Git操作などの組み込みスキルを含む拡張可能なスキルフレームワーク。
- **クロスプラットフォーム** — プラットフォーム固有のコードバリアントとDockerコンテナ化によるWindowsとLinuxの完全サポート。

> [!IMPORTANT]
> **GUIモードに関する注意:** GUIモードはまだ実験段階です。エージェントがGUIモードに切り替える際に問題が発生する可能性があります。この機能の改善に積極的に取り組んでいます。

---

## 🧩 アーキテクチャの概要

```
┌─────────────────────────────────────────────────────────────┐
│                    ユーザーインターフェースレイヤー           │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │  TUI (Textual)   │  │  GUIモジュール (Docker + Gradio) │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      エージェントベース                       │
│           (タスクオーケストレーション＆ライフサイクル管理)      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────┬──────────┼──────────┬─────────┐
        ▼         ▼          ▼          ▼         ▼
   ┌─────────┐ ┌────────┐ ┌────────┐ ┌───────┐ ┌────────┐
   │   LLM   │ │コンテキ │ │アクショ │ │イベン │  │メモリ  │
   │インター  │ │ストエン│  │ン管理  │ │トスト  │ │ (RAG)  │
   │フェース  │ │ジン    │ │        │ │リーム  │ │        │
   └─────────┘ └────────┘ └────────┘ └───────┘ └────────┘
```

| コンポーネント | 説明 |
|-----------|-------------|
| **エージェントベース** | タスクライフサイクルを管理し、コンポーネント間を調整し、メインのエージェントループを処理するコアオーケストレーションレイヤー。 |
| **LLMインターフェース** | 複数のLLMプロバイダー（OpenAI、Gemini、Anthropic、BytePlus、Ollama）をサポートする統一インターフェース。 |
| **コンテキストエンジン** | KVキャッシュサポートで最適化されたプロンプトを生成。 |
| **アクションマネージャー** | ライブラリからアクションを取得して実行。カスタムアクションの拡張が容易。 |
| **アクションルーター** | タスク要件に基づいて最適なアクションをインテリジェントに選択し、必要に応じてLLMを介して入力パラメータを解決。 |
| **イベントストリーム** | タスク進行状況の追跡、UI更新、実行モニタリング用のリアルタイムイベント発行システム。 |
| **メモリマネージャー** | ChromaDBを使用したRAGベースのセマンティックメモリ。メモリのチャンキング、埋め込み、検索、増分更新を処理。 |
| **ステートマネージャー** | エージェント実行コンテキスト、会話履歴、ランタイム設定を追跡するグローバルステート管理。 |
| **タスクマネージャー** | タスク定義を管理し、シンプルタスクと複雑タスクモードの切り替え、TODO作成、マルチステップワークフロー追跡を可能にします。 |
| **スキルマネージャー** | エージェントコンテキストにプラグイン可能なスキルをロードして注入。 |
| **MCPアダプター** | MCPツールをネイティブアクションに変換するModel Context Protocol統合。 |
| **TUIインターフェース** | 対話的なコマンドライン操作のためにTextualフレームワークで構築されたターミナルユーザーインターフェース。 |
| **GUIモジュール** | Dockerコンテナ、UI要素検出用のOmniParser、Gradioクライアントを使用した実験的なGUI自動化。 |

---

## 🔜 ロードマップ

- [X] **メモリモジュール** — 完了。
- [ ] **外部ツール統合** — さらに追加中！
- [X] **MCPレイヤー** — 完了。
- [X] **スキルレイヤー** — 完了。
- [ ] **プロアクティブな動作** — 実装予定

---

## 🧰 はじめに

### 前提条件
- Python **3.9+**
- `git`、`conda`、`pip`
- 選択したLLMプロバイダー（OpenAIやGeminiなど）のAPIキー

### インストール
```bash
git clone https://github.com/zfoong/CraftBot.git
cd CraftBot
conda env create -f environment.yml
```

---

## ⚡ クイックスタート

APIキーをエクスポート:
```bash
export OPENAI_API_KEY=<YOUR_KEY_HERE>
or
export GOOGLE_API_KEY=<YOUR_KEY_HERE>
```
実行:
```bash
python start.py
```

これにより、組み込みの**CraftBot**が実行され、以下のことができます:
1. エージェントと会話
2. 複雑な一連のタスクを実行するよう依頼
3. /helpコマンドを実行してヘルプを求める
4. AIエージェントと仲良くなる
5. 専用の軽量WebRTC Linux VMで高度なコンピュータ操作タスクを実行

### ターミナル引数
| 引数 | 説明 |
| :--- | :--- |
| `--only-cpu` | CPUモードでエージェントを実行 |
| `--fast` | 不要な更新チェックをスキップしてエージェントを高速起動。<br> <u><b>注意:</b></u> 初回起動時は`--fast`なしで実行する必要があります |
| `--no-omniparser` | Microsoft OmniParserによるUI分析を無効化 - GUIアクションの精度が大幅に低下します。OmniParserの使用を強く推奨します |
| `--no-conda` | conda環境内ではなくグローバルにすべてのパッケージをインストール |
| `--no-gui` | GUIモードを無効化。エージェントはCLI専用モードで実行され、GUIモードに切り替えることができません。この設定は再起動後も保持されます。OmniParserも自動的に無効化されます |
| `--enable-gui` | `--no-gui`で無効化されたGUIモードを再度有効化。この設定は再起動後も保持されます |

**例**
```bash
python start.py --only-cpu --fast
```

> [!HINT]
> **オンボーディング:** CraftBotを初めて起動すると、APIキー、エージェントの名前、MCP、スキルを設定するオンボーディングシーケンスがトリガーされます。その後、CraftBotと初めてチャットすると、将来の参照用にUSER.mdとAGENT.mdを更新するためのインタビューセッションが開始されます。

---

## 🔐 OAuth設定（オプション）

エージェントはOAuthを使用してさまざまなサービスに接続できます。リリースビルドには埋め込みクレデンシャルが付属していますが、独自のクレデンシャルを使用することもできます。

### クイックスタート

埋め込みクレデンシャル付きのリリースビルドの場合:
```
/google login    # Google Workspaceに接続
/zoom login      # Zoomに接続
/slack invite    # Slackに接続
/notion invite   # Notionに接続
/linkedin login  # LinkedInに接続
```

### サービス詳細

| サービス | 認証タイプ | コマンド | シークレットが必要? |
|---------|-----------|---------|------------------|
| Google | PKCE | `/google login` | いいえ (PKCE) |
| Zoom | PKCE | `/zoom login` | いいえ (PKCE) |
| Slack | OAuth 2.0 | `/slack invite` | はい |
| Notion | OAuth 2.0 | `/notion invite` | はい |
| LinkedIn | OAuth 2.0 | `/linkedin login` | はい |

### 独自のクレデンシャルを使用する

独自のOAuthクレデンシャルを使用する場合は、`.env`ファイルに追加してください:

#### Google (PKCE - クライアントIDのみ必要)
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. Gmail、カレンダー、ドライブ、People APIを有効化
3. **デスクトップアプリ**タイプとしてOAuthクレデンシャルを作成
4. クライアントIDをコピー（PKCEではシークレットは不要）

#### Zoom (PKCE - クライアントIDのみ必要)
```bash
ZOOM_CLIENT_ID=your-zoom-client-id
```
1. [Zoom Marketplace](https://marketplace.zoom.us/)にアクセス
2. OAuthアプリを作成
3. クライアントIDをコピー

#### Slack (両方必要)
```bash
SLACK_SHARED_CLIENT_ID=your-slack-client-id
SLACK_SHARED_CLIENT_SECRET=your-slack-client-secret
```
1. [Slack API](https://api.slack.com/apps)にアクセス
2. 新しいアプリを作成
3. OAuthスコープを追加: `chat:write`、`channels:read`、`users:read`など
4. クライアントIDとクライアントシークレットをコピー

#### Notion (両方必要)
```bash
NOTION_SHARED_CLIENT_ID=your-notion-client-id
NOTION_SHARED_CLIENT_SECRET=your-notion-client-secret
```
1. [Notion Developers](https://developers.notion.com/)にアクセス
2. 新しいインテグレーション（パブリックインテグレーション）を作成
3. OAuthクライアントIDとシークレットをコピー

#### LinkedIn (両方必要)
```bash
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
```
1. [LinkedIn Developers](https://developer.linkedin.com/)にアクセス
2. アプリを作成
3. OAuth 2.0スコープを追加
4. クライアントIDとクライアントシークレットをコピー

---
## コンテナで実行

リポジトリのルートには、Python 3.10、主要なシステムパッケージ（OCR用のTesseractを含む）、および`environment.yml`/`requirements.txt`で定義されたすべてのPython依存関係を含むDocker構成が含まれており、エージェントは隔離された環境で一貫して実行できます。

以下は、コンテナでエージェントを実行するためのセットアップ手順です。

### イメージのビルド

リポジトリのルートから:

```bash
docker build -t craftbot .
```

### コンテナの実行

イメージはデフォルトで`python -m core.main`でエージェントを起動するように構成されています。対話的に実行するには:

```bash
docker run --rm -it craftbot
```

環境変数を渡す必要がある場合は、envファイル（例えば`.env.example`に基づく）を渡します:

```bash
docker run --rm -it --env-file .env craftbot
```

コンテナの外部で永続化する必要があるディレクトリ（データやキャッシュフォルダなど）は`-v`を使用してマウントし、デプロイに必要に応じてポートや追加のフラグを調整してください。コンテナには、OCR（`tesseract`）、画面自動化（`pyautogui`、`mss`、X11ユーティリティ、仮想フレームバッファ）、および一般的なHTTPクライアント用のシステム依存関係が含まれているため、エージェントはコンテナ内でファイル、ネットワークAPI、GUI自動化を扱うことができます。

### GUI/画面自動化の有効化

GUIアクション（マウス/キーボードイベント、スクリーンショット）にはX11サーバーが必要です。ホストディスプレイにアタッチするか、`xvfb`でヘッドレスで実行できます:

* ホストディスプレイを使用（X11を使用するLinuxが必要）:

  ```bash
  docker run --rm -it
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/data:/app/core/data \
    craftbot
  ```

  エージェントが読み書きする必要があるフォルダには、追加の`-v`マウントを追加してください。

* 仮想ディスプレイでヘッドレス実行:

  ```bash
	docker run --rm -it --env-file .env craftbot bash -lc "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && exec python -m core.main"
  ```

デフォルトでは、イメージはPython 3.10を使用し、`environment.yml`/`requirements.txt`からのPython依存関係をバンドルしているため、`python -m core.main`はそのまま動作します。

---

## 🤝 貢献方法

貢献と提案を歓迎します！[@zfoong](https://github.com/zfoong) @ thamyikfoong(at)craftos.net までご連絡ください。現在、チェック機能を設定していないため、直接的な貢献は受け付けられませんが、提案やフィードバックは大変ありがたく思います。

## 🧾 ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下でライセンスされています。このプロジェクトは自由に使用、ホスト、収益化できます（配布や収益化の場合は、このプロジェクトのクレジット表記が必要です）。

---

## ⭐ 謝辞

[CraftOS](https://craftos.net/)および貢献者[@zfoong](https://github.com/zfoong)と[@ahmad-ajmal](https://github.com/ahmad-ajmal)によって開発・維持されています。
**CraftBot**が役に立つと思われた場合は、リポジトリに⭐をつけて、他の人と共有してくださると嬉しいです！
