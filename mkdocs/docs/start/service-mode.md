# Service mode

Run CraftBot as a **background service** that starts on login, survives terminal close, and keeps [proactive mode](../modes/proactive.md) firing 24/7. One command installs it; a desktop shortcut reopens the browser whenever you want.

## The core idea

The `service.py` entry point wraps `run.py` with:

- **Auto-start registration** — per-OS hook that relaunches CraftBot on login.
- **Detached process** — the agent runs independently of the terminal that started it.
- **Desktop shortcut** — double-click to reopen the browser UI.
- **Log rotation** — keep recent logs, discard old ones.

Under the hood it's the same agent as `python run.py` — just with lifecycle management around it.

## Scenarios

### 1) Personal workstation (the default)

Install once, CraftBot auto-starts on every login. You use the browser UI when you want; it's running quietly the rest of the time so proactive tasks and integrations stay live.

```bash
python service.py install
```

### 2) Always-on home server

Run on a persistent box (Raspberry Pi, home server, cheap VPS). Daily/weekly proactive tasks always fire even when your laptop's closed. Access via SSH port-forward or Tailscale.

```bash
# On the server:
python service.py install

# From your laptop:
ssh -N -L 8080:localhost:8080 you@server
# Open http://localhost:8080 in your browser
```

### 3) Per-user install on a shared machine

`service.py` installs into your user account — no sudo needed. Each user on the same machine can install their own CraftBot service with separate config and credentials.

## Command flow

```
   service.py install
         │
         ├─> install deps (pip install -r requirements.txt)
         ├─> register auto-start (Windows Task Scheduler / systemd user / LaunchAgent)
         ├─> start CraftBot detached (browser mode by default)
         ├─> create desktop shortcut
         └─> close the terminal
```

## CLI reference

| Command | What it does |
|---|---|
| `python service.py install` | Install deps + register auto-start + start + create shortcut + close terminal |
| `python service.py start` | Start in background (auto-restart if already running) |
| `python service.py stop` | Stop the running service |
| `python service.py restart` | Stop + start |
| `python service.py status` | Running? Auto-start enabled? |
| `python service.py logs [-n N]` | Show last N log lines (default 50) |
| `python service.py uninstall` | Stop + remove auto-start + uninstall pip packages + purge pip cache |

## Configuration

Service mode uses the same [`settings.json`](../configuration/config-json.md) as `run.py`. No separate config.

Browser mode is the default interface. To use TUI or CLI mode as a service, edit the command in the launcher script that `service.py install` creates (it's OS-specific — see platform deep-dives below).

## Credential precedence

Credentials resolve in the same order as regular `run.py`:

1. **Embedded** (release builds)
2. **Environment variables** — critical: the service runs under your user, so `.env` in the repo is loaded. System env vars work too.
3. **`settings.json` → `api_keys`**
4. *(nothing)* — connection unavailable

!!! warning "Env vars and auto-start"
    On Linux with systemd user, the service does **not** inherit your shell env. If you rely on env vars, put them in `.env` (the launcher loads it) or in `~/.config/systemd/user/craftbot.service` via `Environment=`.

## Browser UI access

- **Local** — `http://localhost:<port>` (port shown in `service.py status`).
- **Remote over SSH** — port-forward from client to server. See [Scenario 2](#2-always-on-home-server).
- **Remote over Tailscale / VPN** — access the server's tailnet IP directly.
- **Public internet** — not recommended. If you must, put a reverse proxy with auth in front.

## Security rules

- **Default bind** is `localhost` — no external access unless you tunnel or proxy.
- **No built-in auth** — the browser UI trusts whoever can reach the port. Don't expose it directly to the internet.
- **Credentials are local** — the service reads from the same credential store as `run.py`.
- **OAuth refresh** keeps tokens fresh; revoke in the provider's dashboard if a machine is compromised.

## Platform deep-dive

=== "Windows"

    **Auto-start via Task Scheduler:**

    ```powershell
    python service.py install
    ```

    Creates a scheduled task `CraftBot` with trigger "At log on of any user" and action running `run.py` detached.

    **Manual inspection:**

    ```powershell
    # List the task
    schtasks /Query /TN CraftBot /V /FO LIST

    # Remove manually if uninstall gets stuck
    schtasks /Delete /TN CraftBot /F
    ```

    **Shortcut location:** `%USERPROFILE%\Desktop\CraftBot.lnk`

    **Troubleshooting:**

    - Service won't start after reboot: check `schtasks /Query /TN CraftBot` returns `Ready`. If it's `Disabled`, re-enable in Task Scheduler UI.
    - Double-click shortcut does nothing: the browser picks the last-used window. Check `http://localhost:<port>` in your address bar.

=== "macOS"

    **Auto-start via LaunchAgent** — `python service.py install` writes `~/Library/LaunchAgents/com.craftos.craftbot.plist` and loads it.

    **Manual inspection:**

    ```bash
    launchctl list | grep craftbot
    launchctl print gui/$(id -u)/com.craftos.craftbot
    ```

    **Restart manually:**

    ```bash
    launchctl kickstart -k gui/$(id -u)/com.craftos.craftbot
    ```

    **Uninstall the LaunchAgent manually:**

    ```bash
    launchctl bootout gui/$(id -u)/com.craftos.craftbot
    rm ~/Library/LaunchAgents/com.craftos.craftbot.plist
    ```

=== "Linux (systemd user)"

    **Auto-start** — writes `~/.config/systemd/user/craftbot.service` + enables linger:

    ```bash
    loginctl enable-linger $USER
    systemctl --user enable craftbot
    systemctl --user start craftbot
    ```

    **Manual inspection:**

    ```bash
    systemctl --user status craftbot
    journalctl --user -u craftbot -f
    ```

    **Uninstall:**

    ```bash
    systemctl --user disable craftbot
    systemctl --user stop craftbot
    rm ~/.config/systemd/user/craftbot.service
    loginctl disable-linger $USER   # optional
    ```

## Logs

Logs go to the same `logs/` directory as interactive runs (`logs/<timestamp>.log`), rotating at 50 MB, kept 14 days. See [Logs](../concepts/logs.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `service.py install` runs but nothing happens on login | Check OS auto-start UI (Task Scheduler / Login Items / `systemctl --user status`) |
| Browser shortcut opens blank tab | CraftBot isn't running — `service.py start` |
| Proactive tasks not firing | Verify `proactive.enabled: true` in [settings.json](../configuration/config-json.md) AND `service.py status` shows running |
| Can't reach UI remotely | Default is localhost-only — use SSH port-forward (see Scenario 2) |

See [Runtime issues](../troubleshooting/runtime.md) for more.

## Related

- [Install](install.md) — what you do first
- [Interfaces overview](../interfaces/index.md) — pick which mode the service runs
- [Proactive](../modes/proactive.md) — the main reason to run as a service
- `service.py` — the source
