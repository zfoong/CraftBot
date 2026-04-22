# Install CraftBot

Five minutes, Python 3.10+, and at least one LLM API key.

## Prerequisites

- **Python 3.10+** — check with `python --version`
- **git** — to clone the repo
- **An LLM API key** from OpenAI, Google Gemini, Anthropic, BytePlus, or a local Ollama server
- *(optional)* **Node.js 18+** — only for [browser mode](../interfaces/browser.md)
- *(optional)* **conda** — `install.py` offers to auto-install Miniconda if you want it

## Quick install

```bash
git clone https://github.com/zfoong/CraftBot.git
cd CraftBot
python install.py
python run.py
```

On first run, the [onboarding wizard](onboarding.md) asks for your API key and a few preferences. Done.

## Install flags

`install.py` supports several flags for different setups:

=== "Simple (pip, no conda, no GUI)"

    ```bash
    python install.py
    ```

=== "With GUI support"

    ```bash
    # Full GUI with GPU support (downloads ~4GB of OmniParser weights)
    python install.py --gui

    # GUI on CPU-only systems
    python install.py --gui --cpu-only
    ```

=== "With conda environment"

    ```bash
    python install.py --conda
    # or with GUI
    python install.py --gui --conda
    ```

| Flag | Effect |
|---|---|
| *(none)* | pip install into current environment, no GUI, no conda |
| `--gui` | Install OmniParser + vision deps (≈4GB) |
| `--cpu-only` | CPU-only PyTorch (use with `--gui` if no NVIDIA GPU) |
| `--conda` | Create a `craftbot` conda env (offers to install Miniconda if missing) |

## Choose your interface

After install, pick a mode:

| Mode | Command | Needs |
|---|---|---|
| **Browser** | `python run.py` | Node.js 18+ |
| **TUI** | `python run.py --tui` | Nothing extra |
| **CLI** | `python run.py --cli` | Nothing extra |
| **GUI** | `python run.py --gui` | `install.py --gui` completed |

See [Interfaces overview](../interfaces/index.md) for the full comparison.

## No Node.js? No problem

If you don't have Node.js, the installer will say so. Use `python run.py --tui` — the terminal UI has the same features as the browser UI, just in your terminal.

## Docker

From the repo root:

```bash
docker build -t craftbot .
docker run --rm -it --env-file .env craftbot
```

For GUI mode in Docker, see [GUI / Vision](../interfaces/gui-vision.md).

## Platform notes

=== "macOS / Linux"

    Nothing special. `python install.py` handles everything. If Homebrew Python gives trouble, use `pyenv` or the version in the CraftBot conda env.

=== "Windows"

    - Use PowerShell or Git Bash.
    - If `python` is not on PATH, use `py` (Windows launcher).
    - `install.py --gui` on Windows installs GPU PyTorch by default; add `--cpu-only` if no CUDA GPU.

## Troubleshooting install

- **`npm not found`** — install Node.js from [nodejs.org](https://nodejs.org/) or use TUI mode.
- **Playwright install fails** — it's optional (for WhatsApp Web). Skip it; install later with `playwright install chromium`.
- **CUDA issues** — the installer falls back to CPU automatically. Force with `--cpu-only`.
- **Python version too low** — upgrade to Python 3.10+. Python 3.9 won't work.

See [Runtime issues](../troubleshooting/runtime.md) for more.

## Next

- [Quickstart](quickstart.md) — walk through first run
- [Your first task](hello-task.md) — talk to the agent
- [Service mode](service-mode.md) — run it as a background service
