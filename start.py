#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def main():
    """
    Universal launcher script.
    Detects the operating system and executes either run.bat or run.sh.
    """
    current_os = platform.system()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if current_os == "Windows":
        script_name = "run.bat"
        cmd = [os.path.join(script_dir, script_name)]
        print(f"[*] Detected Windows. Launching {script_name}...")
    else:
        # Linux or Darwin (macOS)
        script_name = "run.sh"
        script_path = os.path.join(script_dir, script_name)
        cmd = [script_path]
        print(f"[*] Detected {current_os}. Launching {script_name}...")

        # Ensure the script is executable on Unix-like systems
        if not os.access(script_path, os.X_OK):
            print(f"[*] Making {script_name} executable...")
            try:
                # equivalent to chmod +x
                current_permissions = os.stat(script_path).st_mode
                os.chmod(script_path, current_permissions | 0o111)
            except Exception as e:
                print(f"[!] Error making script executable: {e}")
                print("[!] Please run: chmod +x run.sh")
                sys.exit(1)

    try:
        exit_code = subprocess.call(cmd)
        sys.exit(exit_code)

    except FileNotFoundError:
        print(f"\n[ERROR] Could not find {script_name} in the same directory.")
        print("Please ensure run.sh and run.bat are present.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Launcher interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    args = set(sys.argv[1:])

    flag_ignore_omniparse = "no-omniparse" in args
    if flag_ignore_omniparse:
        os.environ["USE_OMNIPARSER"] = "False"
    else:
        os.environ["USE_OMNIPARSER"] = "True"

    print(f"[*] Using Omniparser: {os.getenv('USE_OMNIPARSER')}")

    flag_ignore_conda = "no-conda" in args
    if flag_ignore_conda:
        os.environ["USE_CONDA"] = "False"
    else:
        os.environ["USE_CONDA"] = "True"

    print(f"[*] Using Conda: {os.getenv('USE_CONDA')}")

    main()