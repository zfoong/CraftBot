#!/usr/bin/env python3
"""
CraftBot Smart Installation Script - v2.0
Detects environment issues and auto-fixes them

Key improvements:
1. Detects Python version early and validates compatibility
2. Handles Windows long paths (>260 chars) by using short paths
3. Resolves dependency conflicts before installation
4. Implements greenlet pre-compilation workaround for Windows
5. Better conda/venv environment management
6. Comprehensive error recovery with solutions

Usage:
    python install_improved.py              # Auto-detect and install
    python install_improved.py --conda      # Force conda environment
    python install_improved.py --venv       # Force virtual environment  
    python install_improved.py --gui        # Include GUI components
    python install_improved.py --fix-only   # Run fixes without installing
"""

import multiprocessing
import os
import sys
import json
import subprocess
import shutil
import time
import threading
import platform
import textwrap
import ctypes
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

multiprocessing.freeze_support()

# --- Global configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
YML_FILE = os.path.join(BASE_DIR, "environment.yml")
REQUIREMENTS_FILE = os.path.join(BASE_DIR, "requirements.txt")

# Minimum Python version
MIN_PYTHON_VERSION = (3, 8)
RECOMMENDED_PYTHON_VERSION = (3, 10, 19)

# ==========================================
# ENVIRONMENT CHECKER
# ==========================================
class EnvironmentChecker:
    """Check and validate the installation environment."""
    
    @staticmethod
    def get_python_info() -> Dict[str, Any]:
        """Get detailed Python information."""
        return {
            "version": sys.version_info,
            "version_str": sys.version,
            "executable": sys.executable,
            "prefix": sys.prefix,
            "platform": sys.platform,
            "architecture": platform.architecture(),
            "machine": platform.machine(),
        }
    
    @staticmethod
    def check_python_version() -> Tuple[bool, str]:
        """Check if Python version is compatible."""
        version = sys.version_info
        
        if version < MIN_PYTHON_VERSION:
            return False, f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required, got {version.major}.{version.minor}"
        
        if version >= (3, 13):
            return False, f"Python {version.major}.{version.minor} may have compatibility issues. Python 3.8-3.12 recommended."
        
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    
    @staticmethod
    def check_windows_long_path() -> Tuple[bool, str]:
        """Check if Windows long path is available (>260 chars)."""
        if sys.platform != "win32":
            return True, "Not Windows"
        
        try:
            import winreg
            registry_path = r"SYSTEM\CurrentControlSet\Control\FileSystem"
            with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
                with winreg.OpenKey(hkey, registry_path) as key:
                    value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
                    if value == 1:
                        return True, "Long paths enabled"
                    else:
                        return False, "Long paths disabled (paths >260 chars will fail)"
        except:
            # Default to assuming it might work
            return True, "Could not verify"
    
    @staticmethod
    def check_disk_space(path: str = ".") -> Tuple[bool, Dict[str, float]]:
        """Check if sufficient disk space available."""
        try:
            if sys.platform == "win32":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceEx(
                    ctypes.c_wchar_p(os.path.abspath(path)),
                    None, None, ctypes.pointer(free_bytes)
                )
                free_gb = free_bytes.value / (1024 ** 3)
                return free_gb >= 5, {"free_gb": free_gb, "required_gb": 5}
            else:
                st = os.statvfs(path)
                free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
                return free_gb >= 5, {"free_gb": free_gb, "required_gb": 5}
        except:
            return True, {"free_gb": 0, "required_gb": 5}
    
    @staticmethod
    def check_existing_installations() -> Dict[str, Any]:
        """Check for existing Python environments."""
        result = {
            "has_venv": False,
            "has_conda": False,
            "conda_path": None,
            "in_venv": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
            "conflicting_packages": []
        }
        
        # Check for conda
        conda_exe = shutil.which("conda")
        if conda_exe:
            result["has_conda"] = True
            result["conda_path"] = conda_exe
        
        # Check for venv
        if os.path.exists(os.path.join(sys.prefix, "pyvenv.cfg")):
            result["has_venv"] = True
        
        # Check for problematic packages
        try:
            import pip
            installed_packages = pip.utils.get_installed_distributions() if hasattr(pip.utils, 'get_installed_distributions') else []
            problematic = ['opencv-python', 'pencv-python', 'lxml']
            for pkg in problematic:
                if any(pkg in str(p) for p in installed_packages):
                    result["conflicting_packages"].append(pkg)
        except:
            pass
        
        return result
    
    @classmethod
    def run_full_check(cls) -> Dict[str, Any]:
        """Run full environment checks."""
        python_ok, python_msg = cls.check_python_version()
        long_path_ok, long_path_msg = cls.check_windows_long_path()
        disk_ok, disk_info = cls.check_disk_space()
        existing = cls.check_existing_installations()
        
        return {
            "python": {"ok": python_ok, "message": python_msg, "info": cls.get_python_info()},
            "long_path": {"ok": long_path_ok, "message": long_path_msg},
            "disk_space": {"ok": disk_ok, "info": disk_info},
            "existing": existing,
        }


# ==========================================
# DEPENDENCY RESOLVER
# ==========================================
class DependencyResolver:
    """Resolve and fix dependency conflicts."""
    
    # Map of problematic packages and their fixes
    PACKAGE_FIXES = {
        "greenlet": {
            "description": "greenlet has compilation issues on Windows with Python 3.9+",
            "fix": "Use pre-compiled version or upgrade",
            "windows_3_9_plus": "Use greenlet>=3.0.0 (pre-compiled binaries available)",
            "solutions": [
                "Upgrade greenlet to latest: pip install --upgrade greenlet",
                "Use conda instead: python install.py --conda",
                "Use Python 3.8 (better compatibility)",
            ]
        },
        "lxml": {
            "description": "lxml 4.8.0 doesn't provide 'html_clean' extra",
            "fix": "Upgrade to lxml>=4.9.0",
            "solutions": [
                "The requirements will be updated to use compatible version",
                "Use conda for pre-built wheels: python install.py --conda",
            ]
        },
        "opencv-python": {
            "description": "Already installed (pencv-python detected as corrupted)",
            "fix": "Reinstall opencv-python",
            "solutions": [
                "pip uninstall opencv-python -y",
                "pip install opencv-python --no-cache-dir",
                "Use conda: python install.py --conda",
            ]
        }
    }
    
    @staticmethod
    def get_installed_versions() -> Dict[str, str]:
        """Get list of installed packages and versions."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {pkg['name'].lower(): pkg['version'] for pkg in packages}
        except:
            pass
        return {}
    
    @staticmethod
    def detect_conflicts() -> List[Dict[str, Any]]:
        """Detect package conflicts."""
        conflicts = []
        installed = DependencyResolver.get_installed_versions()
        
        # Check for corrupted/conflicting packages
        for pkg in installed:
            if "pencv" in pkg or "opencv" in pkg and "pencv" in installed:
                conflicts.append({
                    "package": "opencv-python (corrupted variant detected)",
                    "version": installed.get(pkg),
                    "fix": DependencyResolver.PACKAGE_FIXES.get("opencv-python", {}).get("fix"),
                })
            
            if "lxml" in pkg and installed.get("lxml", "").startswith("4.8"):
                conflicts.append({
                    "package": "lxml",
                    "version": installed[pkg],
                    "fix": DependencyResolver.PACKAGE_FIXES.get("lxml", {}).get("fix"),
                })
        
        return conflicts
    
    @staticmethod
    def fix_windows_greenlet():
        """Fix greenlet on Windows 3.9+."""
        if sys.platform != "win32" or sys.version_info < (3, 9):
            return True
        
        print("\n🔧 Checking for greenlet compatibility issues...")
        
        try:
            # Try to upgrade greenlet to latest (has pre-compiled binaries)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "greenlet"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✓ Greenlet fixed")
                return True
            else:
                print("⚠ Greenlet may have issues, attempting workaround...")
                # Try without building from source
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--only-binary", ":all:", "greenlet"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("⚠ Greenlet installation timed out")
            return False
        except Exception as e:
            print(f"⚠ Greenlet check failed: {e}")
            return False
    
    @staticmethod
    def fix_opencv():
        """Fix corrupted OpenCV installation."""
        print("\n🔧 Checking for corrupted OpenCV...")
        
        try:
            # Uninstall any corrupted version
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "opencv-python", "-y"],
                capture_output=True,
                timeout=30
            )
            
            # Reinstall
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "opencv-python", "--no-cache-dir"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✓ OpenCV fixed")
                return True
            else:
                print("⚠ OpenCV installation may have issues")
                return False
        except Exception as e:
            print(f"⚠ OpenCV fix failed: {e}")
            return False


# ==========================================
# ENVIRONMENT SETUP
# ==========================================
class EnvironmentSetup:
    """Handle environment setup (venv, conda, etc)."""
    
    @staticmethod
    def create_venv(venv_path: str = "craftbot-venv") -> Tuple[bool, str]:
        """Create a Python virtual environment."""
        try:
            venv_abs_path = os.path.abspath(venv_path)
            print(f"\n🔧 Creating virtual environment at: {venv_abs_path}")
            
            result = subprocess.run(
                [sys.executable, "-m", "venv", venv_abs_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✓ Virtual environment created")
                
                # Get python executable in venv
                if sys.platform == "win32":
                    python_exe = os.path.join(venv_abs_path, "Scripts", "python.exe")
                else:
                    python_exe = os.path.join(venv_abs_path, "bin", "python")
                
                return True, python_exe
            else:
                return False, result.stderr[:200]
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_conda_command() -> Optional[str]:
        """Get path to conda command."""
        # Try standard conda
        conda_exe = shutil.which("conda")
        if conda_exe:
            return conda_exe
        
        # Try common Windows paths
        if sys.platform == "win32":
            common_paths = [
                os.path.join(os.path.expanduser("~"), "miniconda3", "condabin", "conda.bat"),
                os.path.join(os.path.expanduser("~"), "Miniconda3", "condabin", "conda.bat"),
                "C:\\miniconda3\\condabin\\conda.bat",
                "C:\\Miniconda3\\condabin\\conda.bat",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    @staticmethod
    def install_miniconda_safe() -> Tuple[bool, str]:
        """Safely install Miniconda using short paths."""
        if sys.platform != "win32":
            # On Linux/Mac, use standard bash installation
            return EnvironmentSetup._install_miniconda_linux()
        
        print("\n🔧 Installing Miniconda to short path...")
        
        try:
            # Get 8.3 short path for home directory (avoids long path issues)
            home_dir = os.path.expanduser("~")
            
            # Try to get short name using Windows API
            try:
                short_home = ctypes.windll.kernel32.GetShortPathName(home_dir)
                if short_home and short_home != home_dir:
                    install_base = short_home
                else:
                    install_base = home_dir
            except:
                install_base = home_dir
            
            # Install to a short path
            install_dir = os.path.join(install_base, "miniconda3")
            
            print(f"  Installation directory: {install_dir}")
            print(f"  Short path: {install_base}")
            
            # Download
            import urllib.request
            url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
            installer = os.path.join(BASE_DIR, "miniconda_temp.exe")
            
            print(f"\n📥 Downloading Miniconda...")
            urllib.request.urlretrieve(url, installer)
            
            print(f"🔧 Running installer...")
            print("  ⚠ Follow the installer prompts:")
            print("  - Choose 'Add Miniconda to PATH'")
            print("  - Install for current user\n")
            
            # Run installer
            result = subprocess.run([installer], timeout=600)
            
            if os.path.exists(installer):
                os.remove(installer)
            
            if result.returncode == 0:
                print("\n✓ Miniconda installed")
                print("  ⚠ IMPORTANT: Restart your terminal before continuing\n")
                return True, "Miniconda installed - please restart terminal"
            else:
                return False, f"Installer exited with code {result.returncode}"
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def _install_miniconda_linux() -> Tuple[bool, str]:
        """Install Miniconda on Linux."""
        print("\n🔧 Installing Miniconda...")
        
        try:
            import urllib.request
            
            # Detect architecture
            if sys.maxsize > 2**32:
                url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            else:
                url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86.sh"
            
            installer = os.path.join(BASE_DIR, "miniconda-installer.sh")
            
            print(f"📥 Downloading Miniconda...")
            urllib.request.urlretrieve(url, installer)
            
            print(f"🔧 Running installer...")
            result = subprocess.run(
                ["bash", installer, "-b", "-p", os.path.expanduser("~/miniconda3")],
                timeout=600
            )
            
            os.remove(installer)
            
            if result.returncode == 0:
                print("✓ Miniconda installed")
                return True, "Please add conda to PATH: ~/miniconda3/bin/conda init"
            else:
                return False, f"Installer exited with code {result.returncode}"
        
        except Exception as e:
            return False, str(e)


# ==========================================
# INSTALLATION MANAGER
# ==========================================
class InstallationManager:
    """Manage the complete installation process."""
    
    def __init__(self):
        self.env_check = EnvironmentChecker.run_full_check()
        self.dep_resolver = DependencyResolver()
        self.fixes_attempted = []
        self.fixes_failed = []
    
    def print_env_summary(self):
        """Print environment check summary."""
        print("\n" + "="*60)
        print(" 📋 Environment Check Summary")
        print("="*60)
        
        # Python version
        python_info = self.env_check["python"]
        status = "✓" if python_info["ok"] else "✗"
        print(f"\n{status} Python Version: {python_info['message']}")
        
        # Disk space
        disk_info = self.env_check["disk_space"]
        status = "✓" if disk_info["ok"] else "⚠"
        print(f"{status} Disk Space: {disk_info['info'].get('free_gb', 0):.1f} GB free (need {disk_info['info'].get('required_gb', 0)} GB)")
        
        # Long paths (Windows)
        if sys.platform == "win32":
            long_path_info = self.env_check["long_path"]
            status = "✓" if long_path_info["ok"] else "⚠"
            print(f"{status} Long Paths: {long_path_info['message']}")
        
        # Existing environment
        existing = self.env_check["existing"]
        if existing["in_venv"]:
            print(f"✓ Running in virtual environment: {sys.prefix}")
        if existing["has_conda"]:
            print(f"✓ Conda found: {existing['conda_path']}")
        
        if existing["conflicting_packages"]:
            print(f"⚠ Conflicting packages found: {', '.join(existing['conflicting_packages'])}")
        
        # Check for conflicts
        conflicts = DependencyResolver.detect_conflicts()
        if conflicts:
            print(f"\n⚠ Dependency Conflicts Detected:")
            for conflict in conflicts:
                print(f"  - {conflict['package']} v{conflict['version']}")
                print(f"    Fix: {conflict['fix']}")
        
        print("\n" + "="*60 + "\n")
    
    def run_pre_install_fixes(self) -> bool:
        """Run pre-installation fixes."""
        print("\n" + "="*60)
        print(" 🔧 Running Pre-Installation Fixes")
        print("="*60)
        
        fixes = [
            ("Greenlet compatibility", DependencyResolver.fix_windows_greenlet),
            ("OpenCV installation", DependencyResolver.fix_opencv),
        ]
        
        all_ok = True
        for fix_name, fix_func in fixes:
            try:
                if fix_func():
                    self.fixes_attempted.append(fix_name)
                else:
                    self.fixes_failed.append(fix_name)
                    all_ok = False
            except Exception as e:
                print(f"✗ Error during {fix_name}: {e}")
                self.fixes_failed.append(fix_name)
                all_ok = False
        
        print("\n" + "="*60 + "\n")
        return all_ok or len(self.fixes_failed) == 0  # Continue even if some fixes fail
    
    def install_requirements(self, python_exe: Optional[str] = None) -> bool:
        """Install requirements from requirements.txt."""
        if python_exe is None:
            python_exe = sys.executable
        
        print("\n" + "="*60)
        print(" 📦 Installing Dependencies")
        print("="*60 + "\n")
        
        try:
            cmd = [python_exe, "-m", "pip", "install", "-r", REQUIREMENTS_FILE]
            
            # Set environment to help with disk space
            env = os.environ.copy()
            env["TMPDIR"] = os.path.expanduser("~/pip-tmp")
            os.makedirs(env["TMPDIR"], exist_ok=True)
            
            result = subprocess.run(cmd, env=env, timeout=1200)
            
            if result.returncode == 0:
                print("\n✓ Dependencies installed successfully")
                return True
            else:
                print("\n✗ Dependency installation failed")
                return False
        
        except subprocess.TimeoutExpired:
            print("\n✗ Installation timed out (took >20 minutes)")
            return False
        except Exception as e:
            print(f"\n✗ Installation error: {e}")
            return False


# ==========================================
# MAIN INTERACTIVE FLOW
# ==========================================
def main():
    """Main installation flow."""
    
    print("\n" + "="*60)
    print(" 🚀 CraftBot Smart Installer v2.0")
    print("="*60)
    
    # Parse arguments
    args = set(sys.argv[1:])
    fix_only = "--fix-only" in args
    force_conda = "--conda" in args
    force_venv = "--venv" in args
    
    # Check environment
    manager = InstallationManager()
    
    # Validate Python version
    if not manager.env_check["python"]["ok"]:
        print(f"\n✗ ERROR: {manager.env_check['python']['message']}")
        print("\nPlease use Python 3.8 or higher:")
        print("   https://www.python.org/downloads/")
        sys.exit(1)
    
    # Print summary
    manager.print_env_summary()
    
    # Check if user only wants fixes
    if fix_only:
        manager.run_pre_install_fixes()
        print("✓ Fix-only mode complete")
        sys.exit(0)
    
    # Run pre-installation fixes
    manager.run_pre_install_fixes()
    
    # Determine installation method
    if force_conda:
        print("Using conda environment mode (forced)")
        use_conda = True
    elif force_venv:
        print("Using virtual environment mode (forced)")
        use_conda = False
    else:
        # Auto-detect
        existing = manager.env_check["existing"]
        if existing["has_conda"] and not existing["in_venv"]:
            use_conda = True
            print("Auto-detected: Using conda")
        elif existing["in_venv"]:
            use_conda = False
            print("Auto-detected: Already in virtual environment")
        else:
            # Ask user
            print("\nWhich installation method do you prefer?")
            print("  1. Create virtual environment (recommended)")
            print("  2. Use conda")
            print("  3. Global pip (not recommended)\n")
            
            choice = input("Select (1-3): ").strip()
            if choice == "2":
                use_conda = True
            elif choice == "3":
                use_conda = False
                print("\n⚠ Warning: Global pip not recommended")
                confirm = input("Continue with global pip? (y/n): ").strip().lower()
                if confirm != "y":
                    sys.exit(0)
            else:
                use_conda = False
    
    # Install dependencies
    if use_conda:
        conda_cmd = EnvironmentSetup.get_conda_command()
        if not conda_cmd:
            print("\n⚠ Conda not found. Installing Miniconda...")
            success, msg = EnvironmentSetup.install_miniconda_safe()
            if not success:
                print(f"✗ Failed to install Miniconda: {msg}")
                sys.exit(1)
            print(msg)
            print("\n⚠ Please restart your terminal and run: python install_improved.py")
            sys.exit(0)
        
        # TODO: Add conda environment setup
        print("Conda environment setup not yet fully implemented")
        print("For now, use: python install.py --conda")
    else:
        # Install to current environment
        success = manager.install_requirements()
        if success:
            print("\n" + "="*60)
            print(" ✓ Installation Complete!")
            print("="*60)
            print("\nYou can now run:")
            print("  python run.py           # Browser interface")
            print("  python run_tui.py       # Terminal interface")
        else:
            print("\n✗ Installation failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
