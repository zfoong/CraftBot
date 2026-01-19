import os
import sys
import subprocess
import platform
import time

# --- NEW HELPER FUNCTION: CROSS-PLATFORM PORT KILLER ---
def kill_process_on_port(port: int):
    """
    Finds and kills any process listening on the specified TCP port.
    Cross-platform solution for Windows and Unix-like systems.
    """
    current_os = platform.system()
    port_str = str(port)
    print(f"[*] Checking for leftover processes on port {port}...")

    try:
        if current_os == "Windows":
            # 1. Find PID using netstat. findstr filters for listening ports.
            find_cmd = f"netstat -ano | findstr TCP | findstr :{port_str}"
            try:
                # shell=True needed for pipes on Windows
                output = subprocess.check_output(find_cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                
                pids_to_kill = set()
                for line in output.strip().split('\n'):
                    # Typical line: "  TCP    0.0.0.0:7861   0.0.0.0:0   LISTENING   12345"
                    parts = line.strip().split()
                    # PID is usually the last element
                    if len(parts) >= 5 and parts[-2] == "LISTENING":
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) > 0:
                            pids_to_kill.add(pid)
                
                if not pids_to_kill:
                     print(f"[*] Port {port} is free.")
                     return

                for pid in pids_to_kill:
                    print(f"[!] Found stale process (PID: {pid}) on port {port}. Killing it...")
                    # 2. Kill PID using taskkill (/F = force, /T = kill child processes too)
                    kill_cmd = f"taskkill /F /T /PID {pid}"
                    subprocess.run(kill_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[*] Port {port} cleared.")
                time.sleep(0.5) # Let OS reclaim socket

            except subprocess.CalledProcessError:
                # findstr returns error code if nothing found
                print(f"[*] Port {port} is free.")

        else:
            # Linux or Darwin (macOS)
            # 1. Find PID using lsof. -t=terse(PID only), -i TCP:port
            find_cmd = ["lsof", "-t", "-i", f"TCP:{port_str}"]
            try:
                output = subprocess.check_output(find_cmd, text=True, stderr=subprocess.DEVNULL)
                pids = output.strip().split('\n')
                
                valid_pids = [pid for pid in pids if pid.isdigit() and int(pid) > 0]
                if not valid_pids:
                     print(f"[*] Port {port} is free.")
                     return

                for pid in valid_pids:
                    print(f"[!] Found stale process (PID: {pid}) on port {port}. Killing it...")
                    # 2. Kill PID using kill -SIGTERM first (gentle), then SIGKILL if needed.
                    # Using SIGKILL (-9) directly for immediate cleanup in this context.
                    subprocess.run(["kill", "-9", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[*] Port {port} cleared.")
                time.sleep(0.5)
                
            except subprocess.CalledProcessError:
                # lsof returns non-zero if nothing found
                print(f"[*] Port {port} is free.")
            except FileNotFoundError:
                 print(f"[!] Warning: 'lsof' command not found. Cannot cleanup port {port} automatically.")

    except Exception as e:
        print(f"[!] Warning: Failed to clean up port {port}: {e}")

# ================= MAIN SCRIPT =================
if __name__ == "__main__":

    current_os = platform.system()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize exit code variable
    final_exit_code = 0

    if current_os == "Windows":
        script_name = "run.bat"
        script_path = os.path.join(script_dir, script_name)
        use_shell = True
        cmd = [script_path]
        print(f"[*] Detected Windows. Preparing {script_name}...")
    else:
        script_name = "run.sh"
        script_path = os.path.join(script_dir, script_name)
        use_shell = False
        
        if not os.access(script_path, os.X_OK):
            print(f"[*] Making {script_name} executable...", flush=True)
            try:
                current_permissions = os.stat(script_path).st_mode
                os.chmod(script_path, current_permissions | 0o111)
            except Exception as e:
                print(f"[!] Error making script executable: {e}")
                # We cannot exit here directly anymore, must set code and let finally run
                final_exit_code = 1
        
        cmd = ["/bin/bash", script_path] 
        print(f"[*] Detected {current_os}. Preparing via: {' '.join(cmd)}", flush=True)


    # --- THE CRITICAL FIX: TRY...FINALLY BLOCK ---
    # If setup failed already, skip execution
    if final_exit_code == 0:
        try:
            sys.stdout.flush()
            print(f"[*] Starting main process...")
            # Use subprocess.run with explicit I/O passing
            result = subprocess.run(
                cmd,
                shell=use_shell,
                # Pass terminal handles directly to the grandchild process
                stdout=sys.stdout,
                stderr=sys.stderr,
                stdin=sys.stdin,
                check=False # We handle return codes manually below
            )
            # Capture the exit code of the run script
            final_exit_code = result.returncode

        except FileNotFoundError:
            print(f"\n[ERROR] Could not find the executable to run {script_name}.")
            print(f"Attempted command: {cmd}")
            final_exit_code = 1
        except KeyboardInterrupt:
            # This catches Ctrl+C passed to this python script itself
            print("\n[!] Launcher interrupted by user.")
            final_exit_code = 130
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred in main.py: {e}")
            final_exit_code = 1

    # --- FINALLY BLOCK RUNS NO MATTER WHAT ---
    # Whether the script finished normally, crashed, or was interrupted with Ctrl+C,
    # this block guarantees cleanup happens.
    try:
        print(f"\n[*] Main process shutdown (Exit Code: {final_exit_code}). Cleaning up...")
        # Clean up whatever is running on port 7861
        kill_process_on_port(7861)
    except KeyboardInterrupt:
        # Handle rare case where user spams Ctrl+C during cleanup
        print("\n[!] Cleanup interrupted.")
    finally:
        # Exit with the code captured from the main process or error handlers
        sys.exit(final_exit_code)