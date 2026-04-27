#!/usr/bin/env python3
"""
CraftBot Service Manager

Run CraftBot as a background process that survives terminal closure,
and optionally register it to auto-start when your system boots.

Commands:
    python craftbot.py start [options]    Start CraftBot in background
    python craftbot.py stop               Stop CraftBot
    python craftbot.py restart [options]  Stop then start
    python craftbot.py status             Show if CraftBot is running
    python craftbot.py logs [-n N]        Show last N log lines (default: 50)
    python craftbot.py install [options]  Register for auto-start on boot/login
    python craftbot.py uninstall          Remove auto-start registration

Options passed to 'start' / 'install':
    --tui                   Run in TUI mode instead of browser
    --cli                   Run in CLI mode
    --no-open-browser       Don't open browser automatically (default for service)
    --frontend-port PORT    Frontend port (default: 7925)
    --backend-port PORT     Backend port (default: 7926)
    --conda                 Use conda environment
    --no-conda              Don't use conda

Examples:
    python craftbot.py start                   # Start in background (browser mode)
    python craftbot.py start --tui             # Start in background (TUI mode)
    python craftbot.py install                 # Auto-start on login (browser mode)
    python craftbot.py install --no-open-browser  # Auto-start without opening browser
    python craftbot.py stop
    python craftbot.py logs -n 100
"""
import os
import sys
import signal
import subprocess
import threading
import time
import webbrowser
from typing import List, Optional

# Store platform once so static analysers don't short-circuit platform branches
_PLATFORM: str = sys.platform

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_SCRIPT = os.path.join(BASE_DIR, "run.py")
PID_FILE = os.path.join(BASE_DIR, "craftbot.pid")
LOG_FILE = os.path.join(BASE_DIR, "craftbot.log")

TASK_NAME = "CraftBot"          # Windows Task Scheduler task name
SYSTEMD_SERVICE = "craftbot"    # Linux systemd service name
LAUNCHD_LABEL = "com.craftbot.agent"  # macOS launchd label
BROWSER_URL = "http://localhost:7925"
SHORTCUT_NAME = "CraftBot.lnk"
LOGO_PNG = os.path.join(BASE_DIR, "craftbot_logo_1.png")
LOGO_ICO = os.path.join(BASE_DIR, "craftbot_logo_1.ico")

# ─── Terminal colors (orange/white brand palette) ─────────────────────────────

def _enable_windows_vtp() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-11)
        m = ctypes.c_ulong()
        k32.GetConsoleMode(h, ctypes.byref(m))
        k32.SetConsoleMode(h, m.value | 0x0004)
    except Exception:
        pass

_enable_windows_vtp()
_USE_COLOR = sys.stdout.isatty()

def _c(code: str) -> str:
    return code if _USE_COLOR else ""

ORANGE = _c("\033[38;2;255;79;24m")   # #FF4F18
WHITE  = _c("\033[38;2;255;255;255m") # #FFFFFF
BOLD   = _c("\033[1m")
DIM    = _c("\033[38;2;80;80;80m")    # dark gray
GREEN  = _c("\033[38;2;80;220;100m")
RED    = _c("\033[91m")
RESET  = _c("\033[0m")

def _retro_step(num: int, total: int, desc: str) -> None:
    """Print a retro-style step header box."""
    W = 62
    visible = f"  ▸ STEP {num}/{total}  ░░  {desc.upper()}"
    pad = max(0, W - len(visible))
    content = (
        f"  {ORANGE}▸ STEP {num}/{total}{RESET}"
        f"  {DIM}░░{RESET}"
        f"  {WHITE}{desc.upper()}{RESET}"
        + " " * pad
    )
    print(f"\n{ORANGE}╔{'═' * W}╗{RESET}")
    print(f"{ORANGE}║{RESET}{content}{ORANGE}║{RESET}")
    print(f"{ORANGE}╚{'═' * W}╝{RESET}")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _to_short_path(path: str) -> str:
    """Return the Windows 8.3 short path form to avoid Unicode / long-path
    issues when embedding paths inside command strings (e.g. schtasks /tr)."""
    if _PLATFORM != "win32":
        return path
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(path, buf, len(buf)):
            return buf.value
    except Exception:
        pass
    return path


def _warn_path_issues() -> None:
    """Print warnings if BASE_DIR is too long or contains non-ASCII characters."""
    if len(BASE_DIR) > 200:
        print(f"WARNING: Installation path is very long ({len(BASE_DIR)} chars).")
        print("         Windows MAX_PATH limit may cause failures.")
        print(f"         Consider moving CraftBot to a shorter path.\n")
    try:
        BASE_DIR.encode("ascii")
    except UnicodeEncodeError:
        print("WARNING: Installation path contains non-ASCII characters (e.g. Japanese).")
        print("         Some commands may fail. Short paths will be used where possible.\n")


def _python_exe() -> str:
    """Return the Python executable to use for the service process."""
    # On Windows prefer pythonw.exe (no console window) when not in TUI/CLI mode
    if _PLATFORM == "win32":
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if os.path.isfile(pythonw):
            return pythonw
    return sys.executable


def _read_pid() -> Optional[int]:
    """Read PID from the PID file. Returns None if file missing or invalid."""
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def _write_pid(pid: int) -> None:
    with open(PID_FILE, "w") as f:
        f.write(str(pid))


def _remove_pid() -> None:
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


def _is_running(pid: int) -> bool:
    """Return True if a process with the given PID is currently alive."""
    if _PLATFORM == "win32":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=5,
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def _build_run_args(extra: List[str], service_mode: bool = True) -> List[str]:
    """Build the argument list for run.py.

    Adds --no-open-browser by default in service mode (auto-start at boot
    should not pop open a browser without the user asking).
    """
    args = list(extra)
    # TUI/CLI modes don't use the browser flag
    if service_mode and "--tui" not in args and "--cli" not in args:
        if "--no-open-browser" not in args:
            args.append("--no-open-browser")
    return args


# ─── Core operations ──────────────────────────────────────────────────────────

def _open_browser_when_ready(url: str, pid_check_fn, delay: float = 4.0) -> None:
    """Wait for the server to start, then open the browser."""
    time.sleep(delay)
    if not pid_check_fn():
        print("\nWarning: CraftBot process exited before browser could open.")
        print(f"Check logs: python craftbot.py logs")
        return
    webbrowser.open(url)


def _open_browser_detached(url: str) -> None:
    """Launch a detached Python process that polls for the server then opens the browser.

    Uses Python's built-in webbrowser module — no PowerShell execution policy issues.
    The spawned process is fully detached so the calling script can exit immediately.
    """
    # Inline Python script: poll until the server responds (max 30s), then open.
    poll_script = (
        "import sys, time, webbrowser\n"
        "try:\n"
        "    from urllib.request import urlopen\n"
        "    deadline = time.time() + 30\n"
        "    while time.time() < deadline:\n"
        "        try:\n"
        f"            urlopen('{url}', timeout=1).close()\n"
        "            break\n"
        "        except Exception:\n"
        "            time.sleep(0.5)\n"
        "except Exception:\n"
        "    pass\n"
        f"webbrowser.open('{url}')\n"
    )

    # On Windows use pythonw.exe so no console window flashes up.
    python = sys.executable
    if _PLATFORM == "win32":
        pythonw = python.replace("python.exe", "pythonw.exe")
        if os.path.isfile(pythonw):
            python = pythonw

    kwargs: dict = dict(
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if _PLATFORM == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NO_WINDOW
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True

    subprocess.Popen([python, "-c", poll_script], **kwargs)


def cmd_start(extra_args: List[str]) -> None:
    """Start CraftBot as a detached background process."""
    pid = _read_pid()
    if pid and _is_running(pid):
        cmd_stop()


    # service_mode=False — don't suppress the browser; we open it ourselves below
    run_args = _build_run_args(extra_args, service_mode=False)
    # Always pass --no-open-browser to run.py; craftbot.py handles opening the browser
    if "--tui" not in run_args and "--cli" not in run_args:
        if "--no-open-browser" not in run_args:
            run_args.append("--no-open-browser")

    python = _python_exe()

    # Use plain python.exe for TUI/CLI because pythonw has no console
    if "--tui" in run_args or "--cli" in run_args:
        python = sys.executable

    cmd = [python, RUN_SCRIPT] + run_args

    log_fh = open(LOG_FILE, "a")
    log_fh.write(f"\n{'='*60}\n")
    log_fh.write(f"CraftBot service started at {_timestamp()}\n")
    log_fh.write(f"Command: {' '.join(cmd)}\n")
    log_fh.write(f"{'='*60}\n")
    log_fh.flush()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    kwargs = dict(
        cwd=BASE_DIR,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=env,
    )

    if _PLATFORM == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except FileNotFoundError as e:
        print(f"  {RED}✗{RESET} {WHITE}Could not launch CraftBot — {e}{RESET}")
        return

    _write_pid(proc.pid)
    print(f"  {GREEN}▸{RESET} {WHITE}CRAFTBOT STARTED{RESET}  {DIM}PID {proc.pid}{RESET}")

    # Create a desktop shortcut so the user can reopen the browser anytime
    if "--tui" not in run_args and "--cli" not in run_args:
        if _PLATFORM == "win32":
            _create_desktop_shortcut_windows()
        else:
            _create_desktop_shortcut_unix()

    open_browser = "--tui" not in run_args and "--cli" not in run_args and "--no-open-browser" not in extra_args
    if open_browser:
        print(f"  {DIM}░░{RESET} {ORANGE}{BROWSER_URL}{RESET}")
        _open_browser_detached(BROWSER_URL)


def cmd_stop() -> None:
    """Stop the running CraftBot service."""
    pid = _read_pid()
    if pid is None:
        print("CraftBot does not appear to be running (no PID file found).")
        return

    if not _is_running(pid):
        print(f"  {DIM}▸ PID {pid} not running — cleaning up stale PID file{RESET}")
        _remove_pid()
        return

    print(f"  {ORANGE}▸{RESET} {WHITE}STOPPING CRAFTBOT{RESET}  {DIM}PID {pid}{RESET}")

    if _PLATFORM == "win32":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True, timeout=15,
            )
        except Exception as e:
            print(f"Warning: taskkill failed — {e}")
    else:
        try:
            # Kill the entire process group so child processes also die
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGTERM)
            # Give it a moment to exit gracefully
            for _ in range(10):
                time.sleep(0.5)
                if not _is_running(pid):
                    break
            else:
                os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"Warning: {e}")

    _remove_pid()
    print(f"  {GREEN}▸{RESET} {WHITE}CRAFTBOT STOPPED{RESET}")


def cmd_status() -> None:
    """Print whether CraftBot is currently running and whether auto-start is installed."""
    W = 50
    pid = _read_pid()
    print(f"\n{ORANGE}╔{'═' * W}╗{RESET}")
    if pid and _is_running(pid):
        print(f"{ORANGE}║{RESET}  {GREEN}▸ RUNNING{RESET}  {DIM}PID {pid}{RESET}{' ' * (W - 14 - len(str(pid)))}{ORANGE}║{RESET}")
        print(f"{ORANGE}║{RESET}  {DIM}░░ LOG: {LOG_FILE[:W-8]}{RESET}{' ' * max(0, W - 8 - len(LOG_FILE[:W-8]))}{ORANGE}║{RESET}")
    else:
        if pid:
            _remove_pid()
        print(f"{ORANGE}║{RESET}  {RED}▸ NOT RUNNING{RESET}{' ' * (W - 14)}{ORANGE}║{RESET}")
    print(f"{ORANGE}║{' ' * W}║{RESET}")
    if _is_installed():
        print(f"{ORANGE}║{RESET}  {GREEN}▸ AUTO-START: INSTALLED{RESET}{' ' * (W - 23)}{ORANGE}║{RESET}")
    else:
        print(f"{ORANGE}║{RESET}  {DIM}▸ AUTO-START: NOT INSTALLED{RESET}{' ' * (W - 27)}{ORANGE}║{RESET}")
    print(f"{ORANGE}╚{'═' * W}╝{RESET}\n")


def cmd_logs(n: int = 50) -> None:
    """Print the last N lines of the CraftBot log."""
    if not os.path.isfile(LOG_FILE):
        print(f"No log file found at {LOG_FILE}")
        return
    try:
        with open(LOG_FILE, "r", errors="replace") as f:
            lines = f.readlines()
        tail = lines[-n:] if len(lines) > n else lines
        print(f"\n{ORANGE}╔{'═' * 60}╗{RESET}")
        print(f"{ORANGE}║{RESET}  {WHITE}CRAFTBOT LOG{RESET}  {DIM}last {len(tail)} lines{RESET}{' ' * (44 - len(str(len(tail))))}{ORANGE}║{RESET}")
        print(f"{ORANGE}╚{'═' * 60}╝{RESET}\n")
        print("".join(tail), end="")
    except Exception as e:
        print(f"  {RED}✗{RESET} {WHITE}Error reading log: {e}{RESET}")


def cmd_restart(extra_args: List[str]) -> None:
    cmd_stop()
    time.sleep(1)
    cmd_start(extra_args)


# ─── Desktop shortcut ─────────────────────────────────────────────────────────

def _find_desktop() -> Optional[str]:
    """Return the path to the user's Desktop folder.

    Works for all users regardless of language, OneDrive config, or custom paths.
    On Windows reads the Shell Folders registry key directly (no subprocess).
    """
    if _PLATFORM == "win32":
        # Method 1: Read the registry directly — fast, no subprocess
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
                0, winreg.KEY_READ,
            )
            raw, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            path = os.path.expandvars(raw)
            if path and os.path.isdir(path):
                return path
        except Exception:
            pass

        # Method 2: ctypes SHGetFolderPath (CSIDL_DESKTOPDIRECTORY = 0x0010)
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetFolderPathW(None, 0x0010, None, 0, buf)
            path = buf.value
            if path and os.path.isdir(path):
                return path
        except Exception:
            pass

    # Fallback: check common paths
    for candidate in [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
    ]:
        if os.path.isdir(candidate):
            return candidate
    return None


def _ensure_ico() -> Optional[str]:
    """Convert craftbot_logo_1.png to .ico if needed. Returns .ico path or None."""
    if os.path.isfile(LOGO_ICO):
        return LOGO_ICO
    if not os.path.isfile(LOGO_PNG):
        return None
    try:
        from PIL import Image
        img = Image.open(LOGO_PNG)
        img.save(LOGO_ICO, format="ICO", sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
        return LOGO_ICO
    except Exception:
        return None


def _create_desktop_shortcut_windows() -> None:
    """Create a .lnk shortcut on the Windows Desktop with the CraftBot icon."""
    desktop = _find_desktop()
    if not desktop:
        return
    shortcut_path = os.path.join(desktop, SHORTCUT_NAME)
    if os.path.exists(shortcut_path):
        return  # already exists, don't recreate
    ico_path = _ensure_ico()
    try:
        # Write the PS script to a temp file with UTF-8-BOM so PowerShell
        # handles non-ASCII paths (e.g. Japanese Desktop folder) correctly.
        import tempfile
        ps_lines = [
            f'$ws = New-Object -ComObject WScript.Shell',
            f'$s = $ws.CreateShortcut("{shortcut_path}")',
            f'$s.TargetPath = "cmd.exe"',
            f'$s.Arguments = "/c start {BROWSER_URL}"',
            f'$s.WindowStyle = 7',  # minimized (hides the cmd flash)
        ]
        if ico_path:
            ps_lines.append(f'$s.IconLocation = "{ico_path},0"')
        ps_lines += [
            f'$s.Description = "Open CraftBot in your browser"',
            f'$s.Save()',
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps1", delete=False, encoding="utf-8-sig"
        ) as tf:
            tf.write("\n".join(ps_lines))
            tmp_ps1 = tf.name
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tmp_ps1],
                capture_output=True, timeout=15,
            )
        finally:
            try:
                os.remove(tmp_ps1)
            except Exception:
                pass
        if os.path.exists(shortcut_path):
            print(f"  Desktop shortcut created: {shortcut_path}")
            print(f"  Double-click it anytime to open CraftBot in your browser.")
        else:
            print(f"  (Shortcut creation may have failed — check {desktop})")
    except Exception as e:
        print(f"  (Could not create desktop shortcut: {e})")


def _create_desktop_shortcut_unix() -> None:
    """Create a .desktop shortcut on Linux/macOS Desktop."""
    desktop = _find_desktop()
    if not desktop:
        return
    shortcut_path = os.path.join(desktop, "CraftBot.desktop")
    try:
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=CraftBot\n"
            f"Exec=xdg-open {BROWSER_URL}\n"
            "Icon=web-browser\n"
            "Terminal=false\n"
        )
        with open(shortcut_path, "w") as f:
            f.write(content)
        os.chmod(shortcut_path, 0o755)
        print(f"  Desktop shortcut created: {shortcut_path}")
        print(f"  Double-click it anytime to open CraftBot in your browser.")
    except Exception as e:
        print(f"  (Could not create desktop shortcut: {e})")


# ─── Auto-start: Windows Task Scheduler ───────────────────────────────────────

def _install_windows_registry(action: str) -> bool:
    """Fallback: register auto-start via HKCU Run registry key (no admin needed)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, TASK_NAME, 0, winreg.REG_SZ, action)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _install_windows(run_args: List[str]) -> None:
    python = _python_exe()
    # Use 8.3 short paths to avoid Unicode/long-path failures in schtasks /tr
    python_s = _to_short_path(python)
    script_s = _to_short_path(RUN_SCRIPT)
    action = f'"{python_s}" "{script_s}" {" ".join(run_args)}'

    # Try Task Scheduler first; silently fall back to Registry on failure
    registered = False
    try:
        result = subprocess.run(
            ["schtasks", "/create", "/tn", TASK_NAME, "/tr", action, "/sc", "ONLOGON", "/f"],
            capture_output=True, text=True, timeout=30,
        )
        registered = result.returncode == 0
    except Exception:
        pass

    if not registered:
        registered = _install_windows_registry(action)

    if registered:
        print(f"Auto-start registered. CraftBot will start automatically on login.")
        print(f"Open CraftBot: {BROWSER_URL}")
        _create_desktop_shortcut_windows()
    else:
        print("Could not register auto-start. Use 'python craftbot.py start' to start manually.")


def _uninstall_windows() -> None:
    removed_any = False

    # Remove from Task Scheduler
    try:
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            print(f"Auto-start removed (task '{TASK_NAME}' deleted).")
            removed_any = True
    except Exception as e:
        print(f"Warning: Could not query Task Scheduler — {e}")

    # Remove from Registry (HKCU\...\Run) — the fallback auto-start method
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        try:
            winreg.DeleteValue(key, TASK_NAME)
            print(f"Auto-start removed (registry entry '{TASK_NAME}' deleted).")
            removed_any = True
        except FileNotFoundError:
            pass  # Entry didn't exist in registry — that's fine
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        print(f"Warning: Could not clean registry — {e}")

    if not removed_any:
        print("No auto-start registration found (already uninstalled?).")


# ─── Auto-start: Linux systemd (user service) ─────────────────────────────────

def _install_linux(run_args: List[str]) -> None:
    service_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(service_dir, exist_ok=True)

    service_file = os.path.join(service_dir, f"{SYSTEMD_SERVICE}.service")
    python = sys.executable
    exec_start = f"{python} {RUN_SCRIPT} {' '.join(run_args)}"

    content = f"""[Unit]
Description=CraftBot AI Agent
After=network.target

[Service]
Type=simple
ExecStart={exec_start}
WorkingDirectory={BASE_DIR}
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
    with open(service_file, "w") as f:
        f.write(content)

    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=10)
        subprocess.run(["systemctl", "--user", "enable", SYSTEMD_SERVICE], check=True, timeout=10)
        print(f"Auto-start registered as systemd user service '{SYSTEMD_SERVICE}'.")
        print("CraftBot will start automatically when you log in.")
        print(f"\nOpen CraftBot: {BROWSER_URL}")
        print(f"  Tip: Bookmark {BROWSER_URL} so you never have to remember it!")
        _create_desktop_shortcut_unix()
        print(f"\nTo start it now: systemctl --user start {SYSTEMD_SERVICE}")
        print(f"To view logs:    journalctl --user -u {SYSTEMD_SERVICE} -f")
    except subprocess.CalledProcessError as e:
        print(f"Error enabling systemd service: {e}")
        print(f"Service file written to: {service_file}")
        print("Try manually: systemctl --user daemon-reload && systemctl --user enable craftbot")
    except FileNotFoundError:
        print("systemctl not found. Is systemd running on this system?")


def _uninstall_linux() -> None:
    service_file = os.path.expanduser(f"~/.config/systemd/user/{SYSTEMD_SERVICE}.service")
    try:
        subprocess.run(["systemctl", "--user", "disable", SYSTEMD_SERVICE], capture_output=True, timeout=10)
        subprocess.run(["systemctl", "--user", "stop", SYSTEMD_SERVICE], capture_output=True, timeout=10)
    except Exception:
        pass
    if os.path.isfile(service_file):
        os.remove(service_file)
        print(f"Auto-start removed (service file deleted).")
    else:
        print("No systemd service file found.")
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, timeout=10)
    except Exception:
        pass


# ─── Auto-start: macOS launchd ────────────────────────────────────────────────

def _install_macos(run_args: List[str]) -> None:
    agents_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(agents_dir, exist_ok=True)

    plist_file = os.path.join(agents_dir, f"{LAUNCHD_LABEL}.plist")
    python = sys.executable
    program_args = [python, RUN_SCRIPT] + run_args
    program_args_xml = "\n".join(f"        <string>{a}</string>" for a in program_args)

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
{program_args_xml}
    </array>
    <key>WorkingDirectory</key>
    <string>{BASE_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{LOG_FILE}</string>
    <key>StandardErrorPath</key>
    <string>{LOG_FILE}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
"""
    with open(plist_file, "w") as f:
        f.write(content)

    try:
        subprocess.run(["launchctl", "load", plist_file], check=True, timeout=10)
        print(f"Auto-start registered as launchd agent '{LAUNCHD_LABEL}'.")
        print("CraftBot will start automatically when you log in.")
        print(f"\nOpen CraftBot: {BROWSER_URL}")
        print(f"  Tip: Bookmark {BROWSER_URL} so you never have to remember it!")
        _create_desktop_shortcut_unix()
        print(f"\nPlist file: {plist_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error loading launchd agent: {e}")
        print(f"Plist written to: {plist_file}")
        print(f"Try manually: launchctl load {plist_file}")


def _uninstall_macos() -> None:
    plist_file = os.path.expanduser(f"~/Library/LaunchAgents/{LAUNCHD_LABEL}.plist")
    if os.path.isfile(plist_file):
        try:
            subprocess.run(["launchctl", "unload", plist_file], capture_output=True, timeout=10)
        except Exception:
            pass
        os.remove(plist_file)
        print("Auto-start removed.")
    else:
        print("No launchd agent found.")


# ─── Install / Uninstall dispatch ─────────────────────────────────────────────

def _is_installed() -> bool:
    """Return True if CraftBot is registered for auto-start on this platform."""
    plat = _PLATFORM
    if plat == "win32":
        # Check Task Scheduler
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/tn", TASK_NAME],
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
        # Check Registry fallback
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ,
            )
            winreg.QueryValueEx(key, TASK_NAME)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    elif plat == "darwin":
        plist = os.path.expanduser(f"~/Library/LaunchAgents/{LAUNCHD_LABEL}.plist")
        return os.path.isfile(plist)
    else:
        service_file = os.path.expanduser(f"~/.config/systemd/user/{SYSTEMD_SERVICE}.service")
        return os.path.isfile(service_file)


def cmd_install(extra_args: List[str]) -> None:
    """Install dependencies, register auto-start, and start CraftBot."""
    _warn_path_issues()
    # ── Step 1: Install dependencies via install.py ────────────────────────
    install_script = os.path.join(BASE_DIR, "install.py")
    if os.path.isfile(install_script):
        _retro_step(1, 3, "Installing dependencies")
        # Pass through any user flags (--conda etc.) and add --no-launch
        install_flags = [a for a in extra_args if a in ("--conda", "--mamba", "--cpu-only")]
        result = subprocess.run(
            [sys.executable, install_script, "--no-launch"] + install_flags,
            cwd=BASE_DIR,
        )
        if result.returncode != 0:
            print(f"\n  {RED}✗{RESET} {WHITE}Dependency installation failed. Aborting.{RESET}")
            return
        print()
    else:
        print(f"  {DIM}(install.py not found — skipping dependency install){RESET}\n")

    # ── Step 2: Register auto-start ────────────────────────────────────────
    if _is_installed():
        print(f"\n  {DIM}▸ STEP 2/3  ░░  AUTO-START ALREADY REGISTERED — SKIPPING{RESET}")
        if _PLATFORM == "win32":
            _create_desktop_shortcut_windows()
        elif _PLATFORM != "darwin":
            _create_desktop_shortcut_unix()
    else:
        _retro_step(2, 3, "Registering auto-start")
        run_args = _build_run_args(extra_args, service_mode=True)
        plat = _PLATFORM
        if plat == "win32":
            _install_windows(run_args)
        elif plat == "darwin":
            _install_macos(run_args)
        else:
            _install_linux(run_args)
        print()

    # ── Step 3: Start the service now ──────────────────────────────────────
    _retro_step(3, 3, "Starting CraftBot")
    cmd_start(extra_args)

    print(f"\n  {GREEN}▸{RESET} {WHITE}CRAFTBOT IS RUNNING IN THE BACKGROUND{RESET}")
    print(f"  {DIM}░░{RESET} {ORANGE}{BROWSER_URL}{RESET}")
    print("You can close this window now.")
    time.sleep(2)
    _close_console_window()


def _remove_desktop_shortcut() -> None:
    """Remove the CraftBot desktop shortcut if it exists."""
    desktop = _find_desktop()
    if not desktop:
        return
    if _PLATFORM == "win32":
        shortcut_path = os.path.join(desktop, SHORTCUT_NAME)
    else:
        shortcut_path = os.path.join(desktop, "CraftBot.desktop")
    if os.path.isfile(shortcut_path):
        try:
            os.remove(shortcut_path)
            print(f"Desktop shortcut removed: {shortcut_path}")
        except Exception as e:
            print(f"Warning: Could not remove desktop shortcut — {e}")


def cmd_uninstall() -> None:
    """Remove auto-start registration and uninstall dependencies."""
    # Stop the service first if running
    pid = _read_pid()
    if pid and _is_running(pid):
        cmd_stop()

    # Clean up PID file
    _remove_pid()

    # Remove auto-start registration
    plat = _PLATFORM
    if plat == "win32":
        _uninstall_windows()
    elif plat == "darwin":
        _uninstall_macos()
    else:
        _uninstall_linux()

    # Remove desktop shortcut
    _remove_desktop_shortcut()

    # Uninstall pip packages
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.isfile(req_file):
        print("\nUninstalling pip packages...")
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-r", req_file, "-y"],
            cwd=BASE_DIR,
        )
    else:
        print("\n(requirements.txt not found — skipping pip uninstall)")

    # Purge pip cache
    print("\nPurging pip cache...")
    subprocess.run([sys.executable, "-m", "pip", "cache", "purge"])

    print("\nUninstall complete.")


# ─── Utility ──────────────────────────────────────────────────────────────────

def _get_parent_pid() -> Optional[int]:
    """Return the PID of the parent process (cmd.exe / terminal)."""
    try:
        result = subprocess.run(
            ["wmic", "process", "where", f"ProcessId={os.getpid()}", "get", "ParentProcessId", "/value"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            if "ParentProcessId=" in line:
                return int(line.split("=")[1].strip())
    except Exception:
        pass
    return None


def _close_console_window() -> None:
    """Close the current console/terminal window on Windows then exit."""
    if _PLATFORM != "win32":
        sys.exit(0)
    # Use PowerShell to kill the parent cmd.exe after a short delay
    try:
        parent_pid = _get_parent_pid()
        if parent_pid:
            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                [
                    "powershell", "-NoProfile", "-Command",
                    f"Start-Sleep -Milliseconds 500; Stop-Process -Id {parent_pid} -Force -ErrorAction SilentlyContinue",
                ],
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass
    sys.exit(0)


def _timestamp() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _usage() -> None:
    print(__doc__)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        _usage()
        return

    command = args[0]
    rest = args[1:]

    if command == "start":
        cmd_start(rest)

    elif command == "stop":
        cmd_stop()

    elif command == "restart":
        cmd_restart(rest)

    elif command == "status":
        cmd_status()

    elif command == "logs":
        n = 50
        if "-n" in rest:
            idx = rest.index("-n")
            try:
                n = int(rest[idx + 1])
            except (IndexError, ValueError):
                print("Warning: invalid -n value, using 50")
        cmd_logs(n)

    elif command == "install":
        cmd_install(rest)

    elif command == "uninstall":
        cmd_uninstall()

    else:
        print(f"Unknown command: '{command}'")
        print("Run 'python craftbot.py --help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
