#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import platform
import shutil
import shlex
import time
# ADDED: Needed for server health check
import urllib.request
import urllib.error
from typing import Tuple, Optional, Dict, Any

# --- Configuration ---
CONFIG_FILE = "config.json"
MAIN_APP_SCRIPT = "main.py"
YML_FILE = "environment.yml"
REQUIREMENTS_FILE = "requirements.txt"

OMNIPARSER_REPO_URL = "https://github.com/zfoong/OmniParser_CraftOS.git"
OMNIPARSER_BRANCH = "CraftOS"
OMNIPARSER_ENV_NAME = "omni"
# ADDED: The expected URL for the Gradio server
OMNIPARSER_SERVER_URL = "http://localhost:7861"

# ==========================================
# HELPER FUNCTIONS (Config & System Internals)
# ==========================================
def load_config() -> Dict[str, Any]:
    """Reads the existing config file safely."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: {CONFIG_FILE} is corrupted. Starting with empty config.")
        return {}

def save_config_value(key: str, value: Any) -> None:
    """Updates a single key in the config file."""
    config = load_config()
    config[key] = value
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
            print(f"ℹ️ Updated config.json: Set '{key}' to '{value}'")
    except IOError as e:
        print(f"⚠️ Warning: Could not save config file: {e}")

# KEEP THIS FUNCTION: Use it for setup steps that MUST finish before continuing.
def run_command(cmd_list: list[str], cwd: Optional[str] = None, check: bool = True, capture: bool = False, env_extras: Dict[str, str] = None) -> subprocess.CompletedProcess:
    """
    Centralized helper to run subprocesses robustly (BLOCKING).
    Waits for command to finish.
    """
    # Prepare environment: inherit current env and add extras
    my_env = os.environ.copy()
    if env_extras:
        my_env.update(env_extras)
    
    # Force Python tools (pip, hf) to be unbuffered so output appears immediately
    my_env["PYTHONUNBUFFERED"] = "1"

    # Prepare I/O arguments
    kwargs = {}
    if capture:
        # Mode: Capture output into memory (doesn't show on screen)
        kwargs['capture_output'] = True
        kwargs['text'] = True
    else:
        # Mode: Stream directly to parent terminal (shows real-time progress bars)
        kwargs['stdout'] = sys.stdout
        kwargs['stderr'] = sys.stderr
        # We print what we are about to do, flush to ensure it appears before command starts
        print(f"Wait > Executing: {' '.join(cmd_list)}", flush=True)

    try:
        result = subprocess.run(
            cmd_list, 
            cwd=cwd, 
            check=check,
            env=my_env,
            **kwargs # unpack appropriate I/O settings
        )
        return result
    except subprocess.CalledProcessError as e:
        # Only print error details if we haven't already streamed them to screen
        if capture:
            print(f"\n❌ Error running command:\nCommand: {' '.join(cmd_list)}")
            print(f"STDOUT:\n{e.stdout}")
            print(f"STDERR:\n{e.stderr}")
        else:
             print(f"\n❌ Command failed (see output above).")
        print("Exiting setup script due to error.")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ Executable not found: {e.filename}")
        sys.exit(1)

# Use this for things like Gradio servers that run forever.
def launch_background_command(cmd_list: list[str], cwd: Optional[str] = None, env_extras: Dict[str, str] = None, silence_output: bool = False) -> Optional[subprocess.Popen]:
    """
    NEW HELPER: Launches a process in the background and moves on immediately (NON-BLOCKING).
    Using Popen instead of run.
    """
    # 1. Environment setup (same as above)
    my_env = os.environ.copy()
    if env_extras: my_env.update(env_extras)
    my_env["PYTHONUNBUFFERED"] = "1"

    # 2. Output handling
    if silence_output:
         stdout_target = subprocess.DEVNULL
         stderr_target = subprocess.DEVNULL
         print(f"ℹ️ Launching background process (silent): {' '.join(cmd_list)}")
    else:
         # Stream output to the current console while the script moves on
         stdout_target = sys.stdout
         stderr_target = sys.stderr
         print(f"ℹ️ Launching background process (streaming): {' '.join(cmd_list)}", flush=True)

    # 3. OS-specific detachment flags
    kwargs = {}
    if sys.platform != "win32":
         kwargs['start_new_session'] = True

    try:
        # Use Popen instead of run. This returns immediately.
        process = subprocess.Popen(
            cmd_list,
            cwd=cwd,
            env=my_env,
            stdout=stdout_target,
            stderr=stderr_target,
            **kwargs
        )
        print(f"✅ Process launched in background with PID: {process.pid}. Moving on immediately.")
        # Return the process handle
        return process
        
    except FileNotFoundError as e:
        print(f"⚠️ Cannot launch background process. Executable not found: {e.filename}")
        return None
    except Exception as e:
         print(f"⚠️ Error launching background process: {e}")
         return None

# --- NEW FUNCTION ADDED HERE ---
def wait_for_server_health(url: str, timeout_seconds: int = 180) -> bool:
    """
    Repeatedly polls a HTTP URL until it returns a 200 OK status or times out.
    """
    print(f"⏳ Waiting for server at {url} to become ready (Timeout: {timeout_seconds}s)...", end="", flush=True)
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            # Set a short timeout for individual requests so we poll quickly.
            # Using urllib.request because it's built-in (no need for 'requests' library)
            req = urllib.request.Request(url, method='HEAD') # HEAD is faster than GET
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    print(" ✅ Ready!")
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            # Server not reachable yet (connection refused or timed out)
            pass
        except Exception as e:
            # Some other unexpected error
            print(f"\n⚠️ Unexpected error checking server health: {e}")

        # Wait a second before retrying, print a dot to show activity
        print(".", end="", flush=True)
        time.sleep(1)

    print(f"\n❌ Error: Server at {url} did not start within {timeout_seconds} seconds.")
    return False


# ==========================================
# HELPER FUNCTIONS (Main Environment Setup)
# ==========================================
def initialize_environment(args: set[str]) -> bool:
    """Parses flags and sets environment variables. Returns True if CPU-only mode is requested."""
    flag_ignore_omniparse = "--no-omniparser" in args
    os.environ["USE_OMNIPARSER"] = str(not flag_ignore_omniparse)
    print(f"[*] Using Omniparser: {os.getenv('USE_OMNIPARSER')}")
    
    flag_ignore_conda = "--no-conda" in args
    os.environ["USE_CONDA"] = str(not flag_ignore_conda)
    print(f"[*] Using Conda base env: {os.getenv('USE_CONDA')}")

    force_cpu = "--cpu-only" in args
    if force_cpu:
        print("[*] CPU-Only mode requested for installations.")
    
    return force_cpu

def is_conda_installed_robust() -> Tuple[bool, str, Optional[str]]:
    """
    Checks if Conda is installed and returns its status, reason, and base path.
    """
    conda_exe = shutil.which("conda")
    if conda_exe:
        conda_base_path = os.path.dirname(os.path.dirname(conda_exe))
        return True, f"Found executable at {conda_exe}", conda_base_path

    if sys.platform == "win32":
        print("... Standard check failed on Windows. Attempting to locate hidden installation ...")
        current_python_dir = os.path.dirname(sys.executable)
        potential_base_paths = [
            os.path.dirname(current_python_dir), 
            os.path.dirname(os.path.dirname(current_python_dir))
        ]
        
        for base_path in potential_base_paths:
            activate_bat = os.path.join(base_path, "Scripts", "activate.bat")
            condabin_bat = os.path.join(base_path, "condabin", "conda.bat")
            if os.path.exists(activate_bat) or os.path.exists(condabin_bat):
                 return True, f"Found likely base installation at {base_path}", base_path
                 
    return False, "Not found in PATH or relative to current Python installation", None

def get_env_name_from_yml(yml_path: str = YML_FILE) -> str:
    try:
        with open(yml_path, 'r') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("name:"): return stripped.split(":", 1)[1].strip().strip("'").strip('"')
    except FileNotFoundError: 
        print(f"❌ Error: {yml_path} not found.")
        sys.exit(1)
    print(f"❌ Error: Could not find 'name:' in {yml_path}.")
    sys.exit(1)
   
def setup_conda_environment(env_name: str, yml_path: str = YML_FILE):
    print(f"Please wait, creating/updating Conda environment: '{env_name}'...")
    run_command(["conda", "env", "update", "-f", yml_path, "--prune"])
    print("✅ Conda environment installation command finished successfully.")

def verify_conda_env_ready(env_name: str):
    print(f"Attempting to verify environment '{env_name}' is active and working...")
    verification_cmd = ["conda", "run", "-n", env_name, "python", "-c", "import sys; print(f'SUCCESS: Verified {sys.executable}')"]
    run_command(verification_cmd, capture=True)
    print(f"✅ Verification successful. The environment is ready.")
    return True

def setup_global_environment(requirements_file: str = REQUIREMENTS_FILE):
    print("Setting up global environment using pip...")
    if not os.path.exists(requirements_file): print(f"❌ Error: {requirements_file} not found."); sys.exit(1)
    run_command([sys.executable, "-m", "pip", "install", "-r", requirements_file])
    print("✅ Pip install finished successfully.")

# ==========================================
# NEW: OMNIPARSER LOCAL SETUP FUNCTION
# ==========================================
def setup_omniparser_local(force_cpu: bool):
    if os.getenv("USE_CONDA") != "True":
        print("⚠️ Skipping OmniParser setup because Conda usage is disabled (--no-conda).")
        return

    print("\n======================================")
    print(" Setting up OmniParser locally")
    print("======================================")

    if not shutil.which("git"):
        print("❌ Error: 'git' is not installed or in the PATH. Cannot clone OmniParser.")
        sys.exit(1)

    # 1. Config & Path Management
    config = load_config()
    repo_path = config.get("omniparser_repo_path")

    if not repo_path:
        # Default directory next to the script
        repo_path = os.path.abspath("OmniParser_CraftOS")
        save_config_value("omniparser_repo_path", repo_path)
    else:
        repo_path = os.path.abspath(repo_path)

    # 2. Git Operations (Clone/Pull)
    print(f"\n--- STEP 1: Checking OmniParser Repository ({repo_path}) ---")
    if os.path.exists(repo_path):
        print(f"ℹ️ Directory exists. Checking for updates on branch '{OMNIPARSER_BRANCH}'...")
        run_command(["git", "-C", repo_path, "pull"])
    else:
        print(f"ℹ️ Cloning OmniParser ({OMNIPARSER_BRANCH} branch)...")
        run_command(["git", "clone", "-b", OMNIPARSER_BRANCH, OMNIPARSER_REPO_URL, repo_path])
        print("✅ Clone successful.")

    # 3. Conda Environment Creation ('omni')
    print(f"\n--- STEP 2: Creating Conda Environment '{OMNIPARSER_ENV_NAME}' ---")
    # capture=False ensures user sees conda progress bar
    run_command(["conda", "create", "-n", OMNIPARSER_ENV_NAME, "python=3.10", "-y"], capture=False)
    print(f"✅ Environment '{OMNIPARSER_ENV_NAME}' created successfully.")

    # Helper: executes commands *inside* the newly created omni env using 'conda run'
    def run_in_omni(cmd: list[str], work_dir: str = repo_path):
        full_cmd = ["conda", "run", "-n", OMNIPARSER_ENV_NAME] + cmd
        run_command(full_cmd, cwd=work_dir, capture=False)

    # 4. PyTorch Installation
    print(f"\n--- STEP 3: Installing PyTorch and core dependencies (This takes time) ---")
    if force_cpu:
        print("MODE: CPU Only")
        if sys.platform == "win32":
            run_in_omni(["conda", "install", "pytorch", "torchvision", "torchaudio", "cpuonly", "-c", "pytorch", "-y"])
        else: # Linux/Mac
            run_in_omni(["conda", "install", "pytorch", "torchvision", "torchaudio", "cpuonly", "-c", "pytorch", "-y"])
    else:
        print("MODE: GPU (Attempting CUDA 12.1 installation)")
        run_in_omni(["conda", "install", "pytorch", "torchvision", "torchaudio", "pytorch-cuda=12.1", "-c", "pytorch", "-c", "nvidia", "-y"])

    # 5. Pip Installations
    print(f"\n--- STEP 4: Installing pip requirements ---")
    # Install base packages, including hf_transfer for faster downloads later
    run_in_omni(["pip", "install", "mkl==2024.0", "sympy==1.13.1", "transformers==4.51.0", "huggingface_hub[cli]", "hf_transfer"])
    
    # Install repo-specific requirements if present
    req_txt_path = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_txt_path):
         run_in_omni(["pip", "install", "-r", "requirements.txt"])
    else:
         print(f"⚠️ Warning: {req_txt_path} not found. Skipping.")

    # 6. Model Weights Download (using 'hf' cli inside the env)
    print(f"\n--- STEP 5: Downloading model weights (This WILL take a while) ---")
    files_to_download = [
        {"file": "icon_detect/train_args.yaml", "local_path": "icon_detect/train_args.yaml"},
        {"file": "icon_detect/model.pt", "local_path": "icon_detect/model.pt"},
        {"file": "icon_detect/model.yaml", "local_path": "icon_detect/model.yaml"},
        {"file": "icon_caption/config.json", "local_path": "icon_caption_florence/config.json"},
        {"file": "icon_caption/generation_config.json", "local_path": "icon_caption_florence/generation_config.json"},
        {"file": "icon_caption/model.safetensors", "local_path": "icon_caption_florence/model.safetensors"}
    ]
    
    weights_dir = os.path.join(repo_path, "weights")
    os.makedirs(weights_dir, exist_ok=True)

    # Enable fast transfer env var for the download subprocesses
    hf_env_extras = {"HF_HUB_ENABLE_HF_TRANSFER": "1"}

    for i, file_info in enumerate(files_to_download, 1):
        print(f"\n[File {i}/{len(files_to_download)}]: {file_info['file']}")
        local_dest_path = os.path.join(weights_dir, file_info['local_path'])
        if os.path.exists(local_dest_path):
             print(f"ℹ️ File already exists locally at {local_dest_path}. Skipping download.")
             continue
        full_download_cmd = ["conda", "run", "-n", OMNIPARSER_ENV_NAME, "hf", "download", "microsoft/OmniParser-v2.0", file_info['file'], "--local-dir", "weights"]
        run_command(full_download_cmd, cwd=repo_path, env_extras=hf_env_extras, capture=True)

    # 7. File Rearrangement
    print(f"\n--- STEP 6: Finalizing Setup ---")
    src_caption_dir = os.path.join(weights_dir, "icon_caption")
    dst_caption_dir = os.path.join(weights_dir, "icon_caption_florence")

    if os.path.exists(src_caption_dir):
        if os.path.exists(dst_caption_dir):
            print(f"Removing outdated destination: {dst_caption_dir}")
            shutil.rmtree(dst_caption_dir)
        shutil.move(src_caption_dir, dst_caption_dir)
        print(f"Moved weights/icon_caption to weights/icon_caption_florence")

    print("\n-------------------------------------------------")
    print("🚀 Launching Gradio Demo in background...")
    # Add -u for unbuffered output so we see it start up
    run_gradio_command = ["conda", "run", "-n", OMNIPARSER_ENV_NAME, "python", "-u", "-m", "gradio_demo"]
    
    # Launch in background so we can check its health
    launch_background_command(run_gradio_command, cwd=repo_path, silence_output=False)

    # 8. Wait for server and set Environment Variable
    # We give it a generous timeout (3 mins) because sometimes model imports take a while.
    if wait_for_server_health(OMNIPARSER_SERVER_URL, timeout_seconds=180):
        os.environ["OMNIPARSER_BASE_URL"] = OMNIPARSER_SERVER_URL
        print(f"✅ OmniParser local setup complete.")
        print(f"Set OMNIPARSER_BASE_URL = {OMNIPARSER_SERVER_URL}")
        print("======================================\n")
    else:
         print("\n❌ CRITICAL ERROR: OmniParser server failed to start.")
         print("Please check the console output above for errors from the background process.")
         # Exit the script because the critical dependency failed.
         sys.exit(1)

# =========================================
# NEW LAUNCHER: SEPARATE MAXIMIZED TERMINAL
# =========================================
def launch_in_new_terminal(conda_env_name: Optional[str] = None, conda_base_path: Optional[str] = None):
    abs_main_script_path = os.path.abspath(MAIN_APP_SCRIPT)
    if not os.path.exists(abs_main_script_path):
        print(f"❌ Error: The main application script was not found at: {abs_main_script_path}")
        sys.exit(1)

    # Add --cpu-only to flags to ignore when passing to main.py
    setup_flags = {"--no-conda", "--no-omniparser", "--cpu-only"}
    pass_through_args = [arg for arg in sys.argv[1:] if arg not in setup_flags]
    current_os = sys.platform

    print("-------------------------------------------------")
    print(f"🚀 Setting up launch command for OS: {current_os}")
    print("-------------------------------------------------")

    # === Windows Implementation ===
    if current_os == "win32":
        if conda_env_name and os.getenv('USE_CONDA') == "True":
             cmd_list = ["conda", "run", "-n", conda_env_name, "python", "-u", abs_main_script_path] + pass_through_args
        else:
             cmd_list = [sys.executable, "-u", abs_main_script_path] + pass_through_args
        
        cmd_string = shlex.join(cmd_list)
        launch_cmd = f'start /MAX cmd /k "set PYTHONUNBUFFERED=1 && {cmd_string}"'
        subprocess.Popen(launch_cmd, shell=True)

    # === Linux & macOS Implementation (The "Activate then Run" strategy) ===
    else:
        python_cmd_string = shlex.join(["python", "-u", abs_main_script_path] + pass_through_args)
        shell_commands = []
        shell_commands.append('echo "--- Terminal Started ---"')

        use_conda = (conda_env_name and os.getenv('USE_CONDA') == "True" and conda_base_path)
        
        if use_conda:
            print(f"ℹ️ Configuring shell to activate conda environment: '{conda_env_name}'")
            conda_sh_path = os.path.join(conda_base_path, "etc", "profile.d", "conda.sh")
            if os.path.exists(conda_sh_path):
                shell_commands.append(f". '{conda_sh_path}'")
                shell_commands.append(f"conda activate '{conda_env_name}'")
            else:
                 print(f"⚠️ Warning: Could not find conda.sh at {conda_sh_path}. Trying fallback activation method.")
                 shell_commands.append(f"conda activate '{conda_env_name}'")
        else:
             print("ℹ️ Using global python environment.")

        shell_commands.append('echo "--- Launching main.py ---"')
        shell_commands.append(f"{python_cmd_string} || echo '\n❌ Process exited with error code $?'")
        shell_commands.append('echo "\n--- Session Finished ---"')

        full_shell_cmd_string = "; ".join(shell_commands)

        if current_os == "darwin":
            applescript = f'tell application "Terminal" to do script "{full_shell_cmd_string}" activate'
            subprocess.run(["osascript", "-e", applescript])

        elif current_os.startswith("linux"):
            terminals = [
                ("gnome-terminal", "--", "--maximize"),
                ("konsole", "-e", "--maximize"),
                ("xfce4-terminal", "-x", "--maximize"),
                ("terminator", "-x", "-m"),
            ]
            terminal_found = False
            for term_bin, exec_flag, max_flag in terminals:
                if shutil.which(term_bin):
                    print(f"✅ Found terminal emulator: {term_bin}")
                    launch_cmd = [term_bin, max_flag, exec_flag, "bash", "-l", "-i", "-c", full_shell_cmd_string]
                    subprocess.Popen(launch_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    terminal_found = True
                    break
            if not terminal_found:
                print("\n❌ Error: Could not find a supported terminal emulator.")
                sys.exit(1)

    print("✅ New terminal launched. Setup script exiting.")
    sys.exit(0)

# --- Main Execution ---
if __name__ == "__main__":
    args_set = set(sys.argv[1:])
    # initialize_environment now returns True if --cpu-only was passed
    requested_cpu_only = initialize_environment(args_set)
    
    conda_base_path = None
    main_env_name = None

    if os.getenv('USE_CONDA') == "True":
        is_installed, reason, conda_base_path = is_conda_installed_robust()
        
        if not is_installed:
            print(f"❌ Conda is not installed ({reason}). Please use --no-conda.")
            sys.exit(1)
        else:
            print(f"✅ Conda detected ({reason}). Base path: {conda_base_path}")
            main_env_name = get_env_name_from_yml(YML_FILE)

            # --- Main Environment Setup ---
            # Uncomment these lines to actually run the setup for the main environment
            # setup_conda_environment(env_name=main_env_name, yml_path=YML_FILE)
            # verify_conda_env_ready(env_name=main_env_name)

    else:
        print("✅ Conda is not used. Using global environment.")
        # setup_global_environment(...)

    # --- OmniParser Setup ---
    # This will run if USE_CONDA is true and USE_OMNIPARSER is true.
    if os.getenv('USE_OMNIPARSER') == "True":
        setup_omniparser_local(force_cpu=requested_cpu_only)

    # Launch the terminal with the necessary info for the MAIN environment
    launch_in_new_terminal(conda_env_name=main_env_name, conda_base_path=conda_base_path)