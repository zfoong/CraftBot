# Runtime issues

Install failures, launch issues, and hot-path problems.

## Install: `npm not found`

Browser mode needs Node.js 18+. Either:

1. Install Node.js from [nodejs.org](https://nodejs.org/) (LTS) and restart your terminal, or
2. Use TUI mode instead: `python run.py --tui`

## Install: Playwright install fails

Playwright (used for [WhatsApp Web](../connections/whatsapp-web.md)) is optional. If it fails:

- The rest of the agent still works.
- Install later: `playwright install chromium`
- On Linux, you may also need system libraries: `playwright install-deps`

## Install: CUDA / GPU issues with `--gui`

The installer auto-detects GPU. If CUDA install fails, it falls back to CPU. Force CPU-only:

```bash
python install.py --gui --cpu-only
```

## Install: Python version too low

You need **3.10+**. Upgrade via `pyenv`, your OS package manager, or use the conda path (`python install.py --conda` installs a 3.10 env).

## Launch: agent hangs on startup

Check the log for the last line — `tail -f logs/*.log`. Common culprits:

- **Invalid API key** — the connection test fails. Re-run onboarding.
- **Ollama URL unreachable** — if `llm_provider: "remote"`, verify `REMOTE_MODEL_URL`.
- **ChromaDB lock** — if the previous run crashed, ChromaDB can hold a lock. `rm -rf chroma_db_memory/` as last resort (this wipes memory, not your agent file system).

## Launch: `/menu` or commands don't work

The UI layer failed to register commands. Look for `[CommandRegistry]` errors in logs. Most common:

- A custom command module has a syntax error — fix it or remove it.
- A required settings field is missing — re-run onboarding.

## Runtime: agent loop stops after one action

If the agent stops after one action in a complex task, it likely hit `MAX_ACTIONS_PER_TASK` (default 500). Check `[TASK]` logs for "action budget exceeded" and either:

- Break the work into smaller tasks, or
- Edit [`app/config.py`](../configuration/config-json.md#constants-not-in-json) to raise the limit.

## Runtime: memory search returns empty

- Check `memory.enabled` in [settings.json](../configuration/config-json.md) is `true`.
- Verify `chroma_db_memory/` exists and isn't zero-sized.
- Trigger a re-index: restart the agent — the `MemoryFileWatcher` re-scans on startup.

## Runtime: event stream grows forever, tokens balloon

Summarization should kick in at 30k tokens. If it's not:

- Check logs for `[EventStream] Triggering summarization` — if absent, the threshold is likely too high.
- LLM might be in a consecutive-failure state — streams fall back to prune-without-summary. Check provider connectivity.

See [Event stream concept](../concepts/event-stream.md).

## Runtime: GUI mode can't take screenshots

- Ensure a graphical display is available (X11 on Linux).
- On Linux headless: use `Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99`.
- Verify `pyautogui` is installed: `pip show pyautogui`.
- OmniParser unreachable: check `omniparser_url` in [settings.json](../configuration/config-json.md) → `gui.*`.

## Runtime: browser mode shows blank page

- `npm` build probably failed. Re-run `python install.py`.
- Port conflict: check logs for the port — another service may be bound.
- DevTools network tab: if WebSocket connection fails, the Python backend isn't up.

## Service mode: doesn't auto-start

See [Service mode platform deep-dive](../start/service-mode.md#platform-deep-dive) for OS-specific checks.

## Getting help

- Logs: `logs/<timestamp>.log`
- [Discord](https://discord.gg/ZN9YHc37HG)
- [GitHub issues](https://github.com/zfoong/CraftBot/issues)

## Related

- [Logs](../concepts/logs.md)
- [Connection issues](connections.md)
- [Provider issues](providers.md)
