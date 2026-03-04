#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import time
import socket
import signal
import shutil # Needed for lsof check on Linux/macOS

# --- CONFIGURATION ---
# Path to the directory containing the docker-compose.yml file
VM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "gui"))
# The main python command to run after setup (args added at runtime)
PYTHON_APP_BASE_CMD = [sys.executable, "-m", "app.main"]
# Service readiness check
READY_HOST = "localhost"
READY_PORT = 3001
MAX_WAIT_SECONDS = 60
# Port to clean up at the very end
CLEANUP_PORT = 7861
# ---------------------


# --- HELPER FUNCTIONS ---

def run_command(cmd: list, cwd: str = None, check: bool = True, capture: bool = False, quiet: bool = False) -> subprocess.CompletedProcess:
    """Helper to run subprocess commands robustly."""
    try:
        use_shell = (platform.system() == "Windows")
        # Always capture output when quiet mode is enabled
        should_capture = capture or quiet
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            shell=use_shell,
            stdout=subprocess.PIPE if should_capture else sys.stdout,
            stderr=subprocess.PIPE if should_capture else sys.stderr,
            text=True if should_capture else False
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed: {' '.join(cmd)}")
        if capture or quiet:
            print(f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        raise
    except FileNotFoundError:
         print(f"\n[ERROR] Command executable not found: {cmd[0]}")
         raise

def is_port_open(host: str, port: int, timeout: int = 1) -> bool:
    """Checks if a TCP port is open on a given host."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def kill_process_on_port(port: int):
    """Finds and kills any process listening on the specified TCP port (Cross-platform)."""
    current_os = platform.system()
    port_str = str(port)
    print(f"[*] Checking for leftover processes on port {port}...")

    try:
        if current_os == "Windows":
            find_cmd = f"netstat -ano | findstr TCP | findstr :{port_str}"
            try:
                output = subprocess.check_output(find_cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                pids_to_kill = set()
                for line in output.strip().split('\n'):
                    parts = line.strip().split()
                    if len(parts) >= 5 and parts[-2] == "LISTENING":
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) > 0: pids_to_kill.add(pid)
                
                if not pids_to_kill:
                     print(f"[*] Port {port} is free.")
                     return

                for pid in pids_to_kill:
                    print(f"[!] Found stale process (PID: {pid}) on port {port}. Killing it...")
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[*] Port {port} cleared.")
                time.sleep(0.5)
            except subprocess.CalledProcessError:
                print(f"[*] Port {port} is free.")

        else: # Linux/macOS
            find_cmd = ["lsof", "-t", "-i", f"TCP:{port_str}"]
            if shutil.which("lsof"):
                try:
                    output = subprocess.check_output(find_cmd, text=True, stderr=subprocess.DEVNULL)
                    pids = [p for p in output.strip().split('\n') if p.isdigit() and int(p) > 0]
                    if not pids:
                        print(f"[*] Port {port} is free.")
                        return
                    for pid in pids:
                        print(f"[!] Found stale process (PID: {pid}) on port {port}. Killing it...")
                        subprocess.run(["kill", "-9", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"[*] Port {port} cleared.")
                    time.sleep(0.5)
                except subprocess.CalledProcessError:
                    print(f"[*] Port {port} is free.")
            else:
                 print(f"[!] Warning: 'lsof' not found. Cannot automatically clean port {port}.")

    except Exception as e:
        print(f"[!] Warning: Failed to clean up port {port}: {e}")

def kill_process_on_port_quiet(port: int):
    """Quietly kill any process listening on the specified TCP port."""
    current_os = platform.system()
    port_str = str(port)

    try:
        if current_os == "Windows":
            find_cmd = f"netstat -ano | findstr TCP | findstr :{port_str}"
            try:
                output = subprocess.check_output(find_cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                pids_to_kill = set()
                for line in output.strip().split('\n'):
                    parts = line.strip().split()
                    if len(parts) >= 5 and parts[-2] == "LISTENING":
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) > 0: pids_to_kill.add(pid)
                for pid in pids_to_kill:
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                pass
        else:
            find_cmd = ["lsof", "-t", "-i", f"TCP:{port_str}"]
            if shutil.which("lsof"):
                try:
                    output = subprocess.check_output(find_cmd, text=True, stderr=subprocess.DEVNULL)
                    pids = [p for p in output.strip().split('\n') if p.isdigit() and int(p) > 0]
                    for pid in pids:
                        subprocess.run(["kill", "-9", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    pass
    except Exception:
        pass

# --- MAIN LOGIC ---

def main():
    # === IGNORE CTRL+C ===
    # Tell this Python wrapper script to completely ignore SIGINT (Ctrl+C).
    # It will not raise KeyboardInterrupt. It will just keep doing what it's doing.
    # The child process will still receive the signal from the terminal driver.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    # ------------------------------

    final_exit_code = 0

    # === TRY BLOCK: Setup and Run ===
    try:
        # 1. Start Docker VM
        print("[1/8] Starting Docker containers...")
        if not os.path.isdir(VM_DIR):
             print(f"[ERROR] Docker directory not found: {VM_DIR}")
             sys.exit(1)
        run_command(["docker", "compose", "up", "-d"], cwd=VM_DIR, quiet=True)

        # 2. Wait Loop
        print("[2/8] Waiting for VM service...")
        waited = 0
        while not is_port_open(READY_HOST, READY_PORT):
            if waited >= MAX_WAIT_SECONDS:
                print(f"\n[ERROR] Timed out waiting for VM port {READY_PORT}.")
                raise TimeoutError(f"Service on port {READY_PORT} did not become ready.")
            time.sleep(1)
            waited += 1

        # Run the main Python app in the foreground.
        # This call BLOCKS until the app exits.
        python_app_cmd = PYTHON_APP_BASE_CMD + sys.argv[1:]
        result = subprocess.run(
            python_app_cmd,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=False
        )
        final_exit_code = result.returncode

    except (subprocess.CalledProcessError, TimeoutError, FileNotFoundError):
        final_exit_code = 1

    except Exception:
        final_exit_code = 1


    # === FINALLY BLOCK: Guaranteed Cleanup ===
    # This block runs only when the 'try' block finishes naturally or hits a non-signal error.
    finally:
        # 1. Stop Docker containers (quietly)
        try:
            run_command(["docker", "compose", "down"], cwd=VM_DIR, check=False, quiet=True)
        except Exception:
            pass

        # 2. Clean up ports (quietly)
        try:
            kill_process_on_port_quiet(CLEANUP_PORT)
        except Exception:
            pass

        sys.exit(final_exit_code)

if __name__ == "__main__":
    main()