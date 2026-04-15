---
name: cli-anything
description: "Use any supported GUI application (GIMP, Blender, LibreOffice, Audacity, OBS, etc.) on behalf of the user. Auto-installs the app and CLI harness, then executes the task directly."
action-sets: ["shell", "file_operations"]
---

# CLI-Anything Skill

**Core rule: Do everything yourself. Never give the user a command to run. Never explain steps. Just execute the task and report the result.**

---

## Help Response (no tools needed — just reply with text)

If the user's message matches any of these (case-insensitive, any wording):
- "cli anything help" / "cli-anything help" / "cli help"
- "what apps does cli-anything support" / "what can cli-anything do"
- "show cli apps" / "cli anything guide" / "list cli apps"
- Any variation asking what CLI-Anything can do or which apps are supported

**Do not run any tools. Reply directly with this message:**

---

**CLI-Anything — What I Can Do**

Just tell me what you want done in plain English. I'll auto-install the app if it's not on your system and complete the task for you — you never need to run any commands yourself.

**Creative & Media**
| App | Example prompt |
|---|---|
| GIMP | "Resize photo.jpg to 1920×1080 and save as photo_hd.jpg" |
| Blender | "Render scene.blend to PNG frames in the frames/ folder" |
| Inkscape | "Export logo.svg as a 300 DPI PNG" |
| Krita | "Export painting.kra as PNG" |
| Audacity | "Trim the first 30 seconds from audio.mp3 and save as clip.mp3" |
| OBS Studio | "Record my screen for 60 seconds" |
| Kdenlive | "Render project.kdenlive to MP4" |
| Shotcut | "Render project.mlt to MP4" |

**Office & Productivity**
| App | Example prompt |
|---|---|
| LibreOffice | "Convert report.docx to PDF" / "Run a macro on spreadsheet.xlsx" |
| Mubu | "Open my outline in Mubu" |

**Communication**
| App | Example prompt |
|---|---|
| Zoom | "Start a Zoom meeting" |

**Diagramming**
| App | Example prompt |
|---|---|
| Draw.io | "Export diagram.drawio as PNG" |
| Mermaid | "Render this diagram to PNG: graph TD; A-->B; B-->C" |

**AI & ML**
| App | Example prompt |
|---|---|
| ComfyUI | "Run workflow.json and save images to output/" |
| AnyGen | "Generate content using AnyGen" |
| NotebookLM | "Summarize this PDF using NotebookLM" |
| Ollama | "Run llama3 and summarize this text: ..." |
| Stable Diffusion | "Generate 'a sunset over mountains' and save as out.png" |

**Dev & Infrastructure**
| App | Example prompt |
|---|---|
| JupyterLab | "Execute notebook.ipynb and save the output" |
| Grafana | "Export my dashboard as JSON" |
| Gitea | "Create a private repo called myrepo on Gitea" |
| GitLab | "Create a new project on GitLab" |
| NextCloud | "Sync my files to NextCloud" |
| Jenkins | "Trigger my build pipeline" |
| AdGuard Home | "Set up network-wide ad blocking with AdGuard Home" |

**GIS & Design**
| App | Example prompt |
|---|---|
| FreeCAD | "Export model.fcstd as STL" |
| QGIS | "Export map.qgz as PNG" |

**Tips:**
- Always give me the full file path (e.g. `C:\Users\you\Desktop\photo.jpg`)
- If the app isn't installed, I'll install it automatically — just wait a few minutes
- I never ask you to run commands yourself — I do everything for you

---

## Supported Apps Reference

Use this table to look up the correct names for every step.

| App | cli-hub name | Windows (winget) | macOS (brew cask) | Linux (apt) |
|---|---|---|---|---|
| GIMP | `gimp` | `GIMP.GIMP` | `gimp` | `gimp` |
| Blender | `blender` | `BlenderFoundation.Blender` | `blender` | `blender` |
| Inkscape | `inkscape` | `Inkscape.Inkscape` | `inkscape` | `inkscape` |
| Audacity | `audacity` | `Audacity.Audacity` | `audacity` | `audacity` |
| OBS Studio | `obs` | `OBSProject.OBSStudio` | `obs` | `obs-studio` |
| Kdenlive | `kdenlive` | `KDE.Kdenlive` | `kdenlive` | `kdenlive` |
| Shotcut | `shotcut` | `Meltytech.Shotcut` | `shotcut` | `shotcut` |
| Krita | `krita` | `KDE.Krita` | `krita` | `krita` |
| LibreOffice | `libreoffice` | `TheDocumentFoundation.LibreOffice` | `libreoffice` | `libreoffice` |
| Mubu | `mubu` | _(web app — skip winget)_ | _(web app)_ | _(web app)_ |
| Zoom | `zoom` | `Zoom.Zoom` | `zoom` | `zoom` |
| Draw.io | `draw-io` | `JGraph.Draw` | `drawio` | _(AppImage)_ |
| Mermaid | `mermaid` | `OpenJS.NodeJS` _(then npm i -g @mermaid-js/mermaid-cli)_ | `mermaid` | _(npm)_ |
| ComfyUI | `comfyui` | _(git clone — see below)_ | _(git clone)_ | _(git clone)_ |
| AnyGen | `anygen` | _(pip install)_ | _(pip install)_ | _(pip install)_ |
| NotebookLM | `notebooklm` | _(web app — Playwright)_ | _(web app)_ | _(web app)_ |
| Ollama | `ollama` | `Ollama.Ollama` | `ollama` | _(curl install)_ |
| AdGuard Home | `adguard-home` | `AdGuard.AdGuardHome` | `adguard-home` | _(binary release)_ |
| Stable Diffusion | `stable-diffusion` | _(git clone AUTOMATIC1111)_ | _(git clone)_ | _(git clone)_ |
| JupyterLab | `jupyterlab` | _(pip install jupyterlab)_ | _(pip install)_ | _(pip install)_ |
| FreeCAD | `freecad` | `FreeCAD.FreeCAD` | `freecad` | `freecad` |
| QGIS | `qgis` | `OSGeo.QGIS` | `qgis` | `qgis` |
| Grafana | `grafana` | `GrafanaLabs.Grafana` | `grafana` | `grafana` |
| Gitea | `gitea` | `Gitea.Gitea` | `gitea` | _(binary)_ |
| GitLab | `gitlab` | _(docker or package)_ | _(docker)_ | `gitlab-ce` |
| NextCloud | `nextcloud` | `Nextcloud.NextcloudDesktop` | `nextcloud` | _(snap/docker)_ |
| Jenkins | `jenkins` | `Jenkins.Jenkins` | `jenkins` | `jenkins` |

---

## Execution Flow (follow every time — use EXACT timeouts listed)

**CRITICAL: Always pass the timeout shown below to run_shell. Never use the default (30s). winget/brew installs take minutes — without a timeout they die silently and the agent loops forever.**

### Step 1 — Detect OS
Run with `timeout: 10`:
```bash
python -c "import platform; print(platform.system())"
```
Result: `Windows`, `Darwin`, or `Linux`.

### Step 2 — Check if the app is installed
Run with `timeout: 10`:
```bash
gimp --version      # or blender --version, libreoffice --version, etc.
```
- Exit 0 → already installed → skip to Step 4
- Exit non-zero → not installed → go to Step 3

### Step 3 — Install the app (ONE attempt only — never retry install)

**Windows** — run with `timeout: 600`:
```bash
winget install --id <WingetID> --silent --accept-package-agreements --accept-source-agreements
```

**macOS** — run with `timeout: 600`:
```bash
brew install --cask <cask-name>
```

**Linux** — run with `timeout: 300`:
```bash
sudo apt-get install -y <package>
```

**Special cases:**
- ComfyUI / Stable Diffusion: `git clone` + `pip install -r requirements.txt` — `timeout: 600`
- Mermaid: `npm install -g @mermaid-js/mermaid-cli` — `timeout: 120`
- JupyterLab / AnyGen: `pip install <package>` — `timeout: 120`
- Web apps (Mubu, NotebookLM): no install needed — use `playwright-mcp`
- Ollama on Linux: `curl -fsSL https://ollama.com/install.sh | sh` — `timeout: 300`

After install, re-run Step 2 check once (`timeout: 10`). If still fails → tell the user, stop completely.

### Step 4 — Check if CLI harness is installed
Run with `timeout: 10`:
```bash
cli-anything-<appname> --version
```
- Found → skip to Step 6
- Not found → go to Step 5

### Step 5 — Install CLI harness (ONE attempt only)

**Always try CLI-Hub first** — run with `timeout: 120`:
```bash
pip install cli-anything-hub --quiet && cli-hub install <cli-hub-name>
```

If CLI-Hub fails → generate a minimal harness with `write_file` (a Click CLI wrapping the app's real scripting API), then run with `timeout: 60`:
```bash
pip install -e cli_anything/<appname> --quiet
```

If harness install also fails → tell the user, stop completely.

### Step 6 — Execute the user's task
Run with `timeout: 300` (or `timeout: 600` for renders/exports):

```bash
# Image editing
cli-anything-gimp image resize input.jpg output.jpg 1920 1080
cli-anything-gimp filter blur input.jpg --radius 3 --output out.jpg
cli-anything-gimp export input.xcf output.png

# 3D / rendering
cli-anything-blender render scene.blend --output frames/ --format PNG
cli-anything-blender script run myscript.py scene.blend

# Vector
cli-anything-inkscape export logo.svg logo.png --dpi 300
cli-anything-inkscape convert input.svg output.pdf

# Audio
cli-anything-audacity trim audio.mp3 output.mp3 --start 0 --end 30
cli-anything-audacity export-mp3 project.aup3 output.mp3

# Video
cli-anything-kdenlive render project.kdenlive output.mp4
cli-anything-shotcut render project.mlt output.mp4

# Office
cli-anything-libreoffice convert doc.docx output.pdf
cli-anything-libreoffice calc run macro.py spreadsheet.xlsx

# Diagrams
cli-anything-draw-io export diagram.drawio output.png
cli-anything-mermaid render diagram.mmd output.png

# AI / ML
cli-anything-comfyui run workflow.json --output images/
cli-anything-ollama run llama3 --prompt "summarize this"
cli-anything-stable-diffusion generate "a sunset over mountains" --output out.png

# Dev / Infra
cli-anything-jupyterlab execute notebook.ipynb --output result.ipynb
cli-anything-grafana export-dashboard my-dashboard dashboard.json
cli-anything-gitea create-repo myrepo --private
```

**Always run the task. Never print commands and ask the user to run them.**

If the task command fails → retry once with adjusted args. If it fails again → report the error and stop.

### Step 7 — Report result
One or two sentences only:
> "Done — rendered `output.mp4` from your Kdenlive project."
> "Converted `report.docx` to PDF at `report.pdf`."

---

## Hard Stop Rules (prevents infinite loops)

- **Never retry an install** — if `winget install` or `cli-hub install` fails, stop and tell the user.
- **Never loop on a timeout** — if a command times out once, it will time out again. Stop immediately.
- **Max 1 retry on the task command (Step 6) only** — not on installs.
- **If stuck after 3 total run_shell calls** for the same step → stop, tell the user what failed.
