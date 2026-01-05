import subprocess
import sys
from typing import Optional, Tuple

class GUIHandler:
    """
    Static handler for interacting with VM/Container GUIs via agent injection.
    Automatically handles dependency installation for Linux containers.
    """

    # REPLACE with your container name
    TARGET_CONTAINER = "simple-agent-desktop"

    # Name of the Python package required for Linux screen capture
    _LINUX_REQUIRED_PKG = "Pillow"

    # --- Linux Payload (Python) ---
    # Tries to import Pillow. If missing, exits with code 10.
    # If present, takes screenshot and writes raw PNG bytes to stdout buffer.
    _LINUX_PYTHON_PAYLOAD = """
import sys
import io
import os

# Ensure DISPLAY is set if not already
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"

try:
    from PIL import ImageGrab
except ImportError:
    # Magic exit code 10 tells host that the package is missing
    sys.exit(10)

try:
    # Grab screen
    img = ImageGrab.grab()
    img_bytes = io.BytesIO()
    # Save as PNG to memory
    img.save(img_bytes, format='PNG')
    # Write raw binary data to stdout buffer
    sys.stdout.buffer.write(img_bytes.getvalue())
    sys.stdout.flush()
except Exception as e:
    # Write errors to stderr
    sys.stderr.write(f"AGENT_ERROR: {e}")
    sys.exit(1)
"""

    # --- Windows Payload (PowerShell) ---
    # (Using built-in .NET)
    _WINDOWS_PAYLOAD = r"""
try {
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    Add-Type -AssemblyName System.Drawing | Out-Null
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Bounds.Left, $screen.Bounds.Top, 0, 0, $bitmap.Size)
    $ms = New-Object System.IO.MemoryStream
    $bitmap.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    [Console]::OpenStandardOutput().Write($ms.ToArray(), 0, $ms.Length)
} catch {
    $host.ui.WriteErrorLine("AGENT_ERROR: " + $_.Exception.Message)
    exit 1
}
"""

    # ==========================
    # Public API
    # ==========================

    @classmethod
    def get_screen_state(cls, container_id: str) -> bytes:
        """
        Injects an agent script into the specified Docker container to take
        a screenshot and streams the raw PNG bytes back.
        """
        print(f"[GUIHandler] Initiating screen capture for '{container_id}'...")

        os_type = cls._detect_os(container_id)
        print(f"[GUIHandler] Detected OS: {os_type.upper()}")

        if os_type == "linux":
            return cls._get_linux_screen_with_auto_install(container_id)
        elif os_type == "windows":
            return cls._get_windows_screen(container_id)
        else:
             raise RuntimeError(f"Could not determine OS type for container '{container_id}'")

    # ==========================
    # Internal OS-Specific Logic
    # ==========================

    @classmethod
    def _get_linux_screen_with_auto_install(cls, container_id: str) -> bytes:
        """Handles the Linux capture lifecycle, including auto-installing dependencies."""
        
        # 1. Try executing the payload first
        print("[GUIHandler] Attempting Linux capture...")
        stdout, stderr, code = cls._run_docker_exec(
            container_id, 
            ["python3"], # Run python3 interpreter
            cls._LINUX_PYTHON_PAYLOAD.encode()
        )

        # 2. Check for Magic Exit Code 10 (Missing Package)
        if code == 10:
            print(f"[GUIHandler] Agent reported missing package: '{cls._LINUX_REQUIRED_PKG}'.")
            # Install the package
            cls._install_linux_package(container_id, cls._LINUX_REQUIRED_PKG)
            
            # Retry execution after installation
            print("[GUIHandler] Retrying capture after installation...")
            stdout, stderr, code = cls._run_docker_exec(
                container_id, 
                ["python3"], 
                cls._LINUX_PYTHON_PAYLOAD.encode()
            )

        # 3. Validate final output
        return cls._validate_agent_output(stdout, stderr, code)

    @classmethod
    def _get_windows_screen(cls, container_id: str) -> bytes:
        """Handles the Windows capture lifecycle."""
        print("[GUIHandler] Attempting Windows capture via PowerShell...")
        ps_cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "-"]
        stdout, stderr, code = cls._run_docker_exec(
            container_id, 
            ps_cmd, 
            cls._WINDOWS_PAYLOAD.encode()
        )
        return cls._validate_agent_output(stdout, stderr, code)

    # ==========================
    # Internal Helpers
    # ==========================

    @classmethod
    def _install_linux_package(cls, container_id: str, pkg_name: str):
        """Runs pip install inside the container."""
        print(f"[GUIHandler] Installing required package '{pkg_name}' inside container '{container_id}'...")
        # NOTE: We cannot use sys.executable here because that refers to the HOST python.
        # We must use 'python3' to refer to the container's python.
        cmd = ["python3", "-m", "pip", "install", "--quiet", pkg_name]
        
        try:
            # We use _run_docker_exec but we don't need stdin payload here.
            stdout, stderr, code = cls._run_docker_exec(container_id, cmd, stdin_data=None)
            
            if code != 0:
                 err_msg = stderr.decode(errors='replace').strip()
                 # Fallback if stderr is empty, check stdout
                 if not err_msg: err_msg = stdout.decode(errors='replace').strip()
                 raise RuntimeError(f"Failed to install '{pkg_name}' inside container. Exit code {code}. Error: {err_msg}")
            
            print(f"[GUIHandler] Successfully installed '{pkg_name}'.")
            
        except Exception as e:
             print(f"[GUIHandler] Installation failed. Ensure 'python3' and 'pip' are installed in the container.")
             raise e

    @classmethod
    def _run_docker_exec(cls, container_id: str, shell_cmd: list, stdin_data: Optional[bytes] = None) -> Tuple[bytes, bytes, int]:
        """Helper to run docker exec piping data in and out."""
        try:
            cmd = ["docker", "exec", "-i", container_id] + shell_cmd
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE if stdin_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(input=stdin_data)
            return stdout, stderr, process.returncode
        except FileNotFoundError:
             raise FileNotFoundError("The 'docker' command was not found on the host system.")

    @classmethod
    def _validate_agent_output(cls, stdout: bytes, stderr: bytes, code: int) -> bytes:
        """Ensures the agent finished successfully and returned valid image data."""
        if code != 0:
            err_msg = stderr.decode(errors='replace').strip()
            raise RuntimeError(f"Agent capture failed (Exit code {code}). Stderr: {err_msg}")
        
        if not stdout or len(stdout) == 0:
             raise RuntimeError("Agent finished successfully but returned zero data bytes.")

        # Basic PNG Header Check
        if not stdout.startswith(b'\x89PNG'):
             raise RuntimeError("Data returned by agent is not valid PNG format.")

        print(f"[GUIHandler] Successfully retrieved {len(stdout)} bytes.")
        return stdout

    @classmethod
    def _detect_os(cls, container_id: str) -> str:
        """Probes container to guess OS type."""
        stdout, _, code = cls._run_docker_exec(container_id, ["/bin/sh", "-c", "uname"])
        if code == 0 and b"Linux" in stdout: return "linux"
        
        stdout, _, code = cls._run_docker_exec(container_id, ["cmd.exe", "/c", "ver"])
        if code == 0 and b"Windows" in stdout: return "windows"
        
        return "unknown"

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    try:
        # On first run on a fresh container, this will take longer 
        # as it installs Pillow inside the container.
        screenshot_bytes = GUIHandler.get_screen_state(GUIHandler.TARGET_CONTAINER)

        print(f"\n>>> Main Program: Received {len(screenshot_bytes)} bytes of image data. <<<")

        # Verification: Save to disk
        filename = f"final_agent_capture.png"
        with open(filename, "wb") as f:
            f.write(screenshot_bytes)
        print(f"Verification image saved to: {filename}")

    except Exception as e:
        print(f"\n>>> ERROR: {e} <<<")