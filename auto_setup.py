#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CraftBot Auto Environment Setup - v1.0

This script MUST be run FIRST, before anything else.

It automatically:
1. Detects your Python version and environment
2. Identifies conflicts and issues
3. Creates the optimal environment for your system
4. Prepares everything for safe installation

Usage:
    python auto_setup.py

This is the ONLY command users need to run first!
"""

import os
import sys
import subprocess
import shutil
import platform
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, List

# Fix encoding on Windows
import io
if sys.platform == "win32":
    # Use UTF-8 for stdout
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ==========================================
# CONFIGURATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETUP_CONFIG = os.path.join(BASE_DIR, ".craftbot_setup.json")

# ==========================================
# COLOR OUTPUT
# ==========================================
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    
    @staticmethod
    def disable():
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

# Disable colors on Windows if not supported
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        Colors.disable()

# ==========================================
# ENVIRONMENT DETECTOR
# ==========================================
class EnvironmentDetector:
    """Detects Python environment and potential issues."""
    
    @staticmethod
    def get_python_info() -> Dict:
        """Get detailed Python information."""
        return {
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "version_info": (sys.version_info.major, sys.version_info.minor, sys.version_info.micro),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "platform": sys.platform,
            "is_conda": "conda" in sys.prefix or "anaconda" in sys.prefix or "miniconda" in sys.prefix,
            "is_venv": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
        }
    
    @staticmethod
    def detect_issues() -> List[Dict]:
        """Detect environment issues."""
        issues = []
        info = EnvironmentDetector.get_python_info()
        version = info["version_info"]
        
        # Python 3.9 with conda has greenlet issues
        if version >= (3, 9) and version < (3, 11) and info["is_conda"]:
            issues.append({
                "severity": "warning",
                "name": "conda_python_39_greenlet",
                "message": f"Python {version[0]}.{version[1]} with Conda + greenlet has known issues",
                "solution": "Create clean virtual environment instead",
                "fix_auto": True
            })
        
        # Python < 3.8 not supported
        if version < (3, 8):
            issues.append({
                "severity": "error",
                "name": "python_too_old",
                "message": f"Python {version[0]}.{version[1]} is too old (need 3.8+)",
                "solution": "Upgrade Python to 3.8 or higher",
                "fix_auto": False
            })
        
        # Python >= 3.13 may have issues
        if version >= (3, 13):
            issues.append({
                "severity": "warning",
                "name": "python_too_new",
                "message": f"Python {version[0]}.{version[1]} may have compatibility issues",
                "solution": "Consider using Python 3.10-3.12",
                "fix_auto": False
            })
        
        # Check for corrupted opencv
        if EnvironmentDetector._has_corrupted_opencv():
            issues.append({
                "severity": "error",
                "name": "opencv_corrupted",
                "message": "Corrupted 'pencv-python' package detected",
                "solution": "Remove and reinstall opencv-python",
                "fix_auto": True
            })
        
        # Check for old lxml
        if EnvironmentDetector._has_old_lxml():
            issues.append({
                "severity": "warning",
                "name": "lxml_old",
                "message": "lxml 4.8.0 found - doesn't provide 'html_clean' extra",
                "solution": "Upgrade lxml to 4.9.3+",
                "fix_auto": True
            })
        
        # Check disk space
        if EnvironmentDetector._check_disk_space() < 5:
            issues.append({
                "severity": "error",
                "name": "disk_space_low",
                "message": f"Only {EnvironmentDetector._check_disk_space():.1f} GB free (need 5+ GB)",
                "solution": "Free up disk space before continuing",
                "fix_auto": False
            })
        
        return issues
    
    @staticmethod
    def _has_corrupted_opencv() -> bool:
        """Check for corrupted OpenCV."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout.lower()
            return "pencv" in output and "opencv" not in output
        except:
            return False
    
    @staticmethod
    def _has_old_lxml() -> bool:
        """Check for old lxml version."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "lxml"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "Version: 4.8" in result.stdout:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def _check_disk_space() -> float:
        """Check free disk space in GB."""
        try:
            if sys.platform == "win32":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceEx(
                    ctypes.c_wchar_p(os.path.abspath(".")),
                    None, None, ctypes.pointer(free_bytes)
                )
                return free_bytes.value / (1024 ** 3)
            else:
                st = os.statvfs(".")
                return (st.f_bavail * st.f_frsize) / (1024 ** 3)
        except:
            return 10  # Assume OK if can't check
    
    @staticmethod
    def find_conda_installation() -> Optional[str]:
        """Find conda installation even if not in PATH - AGGRESSIVE SEARCH."""
        
        # Windows-specific search
        if sys.platform == "win32":
            # Check all possible Windows locations
            windows_paths = [
                # User directory variations
                os.path.expanduser("~/miniconda3"),
                os.path.expanduser("~/Miniconda3"),
                os.path.expanduser("~/anaconda3"),
                os.path.expanduser("~/Anaconda3"),
                os.path.expanduser("~/miniconda"),
                os.path.expanduser("~/Miniconda"),
                # C: drive variations
                "C:\\miniconda3",
                "C:\\Miniconda3",
                "C:\\anaconda3",
                "C:\\Anaconda3",
                "C:\\miniconda",
                "C:\\Miniconda",
                # Program Files
                "C:\\Program Files\\miniconda3",
                "C:\\Program Files\\Miniconda3",
                "C:\\Program Files\\anaconda3",
                "C:\\Program Files\\Anaconda3",
                "C:\\Program Files (x86)\\miniconda3",
                "C:\\Program Files (x86)\\Miniconda3",
                # Optional
                os.path.expanduser("~/opt/miniconda3"),
                "C:\\Users\\miniconda3",
                # OneDrive and other cloud storage
                os.path.expanduser("~/OneDrive/miniconda3"),
                os.path.expanduser("~/OneDrive/Miniconda3"),
            ]
            
            # Try each path
            for path in windows_paths:
                if os.path.exists(path):
                    conda_exe = os.path.join(path, "condabin", "conda.bat")
                    if os.path.exists(conda_exe):
                        return conda_exe
                    # Also try direct conda.exe in Scripts
                    conda_exe = os.path.join(path, "Scripts", "conda.exe")
                    if os.path.exists(conda_exe):
                        return conda_exe
            
            # Last resort: scan user's home directory for any miniconda/anaconda folder
            home = os.path.expanduser("~")
            try:
                for item in os.listdir(home):
                    if "conda" in item.lower() and os.path.isdir(os.path.join(home, item)):
                        conda_exe = os.path.join(home, item, "condabin", "conda.bat")
                        if os.path.exists(conda_exe):
                            return conda_exe
                        conda_exe = os.path.join(home, item, "Scripts", "conda.exe")
                        if os.path.exists(conda_exe):
                            return conda_exe
            except:
                pass
            
            # Scan all drives
            try:
                for drive in ["D:\\", "E:\\", "F:\\", "G:\\"]:
                    if os.path.exists(drive):
                        for item in ["miniconda3", "Miniconda3", "anaconda3", "Anaconda3", "miniconda", "Miniconda"]:
                            path = os.path.join(drive, item)
                            if os.path.exists(path):
                                conda_exe = os.path.join(path, "condabin", "conda.bat")
                                if os.path.exists(conda_exe):
                                    return conda_exe
            except:
                pass
        else:
            # Linux/Mac search
            linux_mac_paths = [
                os.path.expanduser("~/miniconda3"),
                os.path.expanduser("~/Miniconda3"),
                os.path.expanduser("~/anaconda3"),
                os.path.expanduser("~/Anaconda3"),
                os.path.expanduser("~/opt/miniconda3"),
                "/opt/miniconda3",
                "/usr/local/miniconda3",
                "/opt/anaconda3",
                "/usr/local/anaconda3",
                os.path.expanduser("~/.miniconda3"),
                "/Applications/miniconda3",
                "/Applications/anaconda3",
            ]
            
            for path in linux_mac_paths:
                conda_exe = os.path.join(path, "bin", "conda")
                if os.path.exists(conda_exe):
                    return conda_exe
            
            # Scan home directory
            home = os.path.expanduser("~")
            try:
                for item in os.listdir(home):
                    if "conda" in item.lower() and os.path.isdir(os.path.join(home, item)):
                        conda_exe = os.path.join(home, item, "bin", "conda")
                        if os.path.exists(conda_exe):
                            return conda_exe
            except:
                pass
        
        return None


# ==========================================
# ENVIRONMENT CREATOR
# ==========================================
class EnvironmentCreator:
    """Creates and configures the optimal environment."""
    
    @staticmethod
    def check_conda_path() -> Tuple[bool, Optional[str], str]:
        """Check if conda is in PATH or findable."""
        # Try to find conda in PATH
        conda_exe = shutil.which("conda")
        if conda_exe:
            return True, conda_exe, "Found in PATH"
        
        # Try to find conda in common locations
        conda_path = EnvironmentDetector.find_conda_installation()
        if conda_path:
            return True, conda_path, f"Found at installation"
        
        return False, None, "Not found"
    
    @staticmethod
    def auto_install_miniconda() -> Tuple[bool, str]:
        """Auto-install Miniconda without user prompt."""
        print(f"{Colors.CYAN}🔧 Miniconda not detected, auto-installing...{Colors.RESET}")
        
        try:
            install_dir = os.path.expanduser("~/miniconda3")
            
            if sys.platform == "win32":
                install_dir = "C:\\miniconda3"
                installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
                installer_file = os.path.join(os.environ.get('TEMP', '.'), "Miniconda3-latest-Windows-x86_64.exe")
                
                print(f"{Colors.CYAN}  Downloading Miniconda for Windows...{Colors.RESET}")
                
                # Download
                try:
                    import urllib.request
                    urllib.request.urlretrieve(installer_url, installer_file)
                except Exception as e:
                    print(f"{Colors.YELLOW}  ⚠️  Download failed: {e}{Colors.RESET}")
                    print(f"{Colors.YELLOW}  Please install manually: https://docs.conda.io/en/latest/miniconda.html{Colors.RESET}")
                    return False, "Download failed - install manually"
                
                # Run installer
                print(f"{Colors.CYAN}  Running installer (this may take 2-3 minutes)...{Colors.RESET}")
                result = subprocess.run(
                    [installer_file, "/InstallationType=JustMe", "/AddMinicondaToPath=Yes", f"/D={install_dir}"],
                    timeout=600
                )
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}  ✓ Miniconda installed successfully!{Colors.RESET}")
                    print(f"{Colors.YELLOW}  ⚠️  Please restart your terminal for PATH changes to take effect{Colors.RESET}")
                    return True, "Installed in C:\\miniconda3"
                else:
                    print(f"{Colors.RED}  ✗ Installation failed{Colors.RESET}")
                    return False, "Installation failed"
            
            else:
                # Linux/macOS
                installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
                installer_file = os.path.join("/tmp", "Miniconda3-latest-Linux-x86_64.sh")
                
                print(f"{Colors.CYAN}  Downloading Miniconda for Linux/Mac...{Colors.RESET}")
                
                # Download
                try:
                    import urllib.request
                    urllib.request.urlretrieve(installer_url, installer_file)
                except Exception as e:
                    print(f"{Colors.YELLOW}  ⚠️  Download failed: {e}{Colors.RESET}")
                    print(f"{Colors.YELLOW}  Please install manually: https://docs.conda.io/en/latest/miniconda.html{Colors.RESET}")
                    return False, "Download failed - install manually"
                
                # Make executable and run
                print(f"{Colors.CYAN}  Running installer (this will take 2-3 minutes)...{Colors.RESET}")
                os.chmod(installer_file, 0o755)
                result = subprocess.run(["/bin/bash", installer_file, "-b", "-p", install_dir])
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}  ✓ Miniconda installed successfully!{Colors.RESET}")
                    print(f"{Colors.CYAN}  Running conda init to configure shell...{Colors.RESET}")
                    conda_exe = os.path.join(install_dir, "bin", "conda")
                    subprocess.run([conda_exe, "init"], check=False)
                    print(f"{Colors.YELLOW}  ⚠️  Please restart your terminal for PATH changes to take effect{Colors.RESET}")
                    return True, f"Installed in {install_dir}"
                else:
                    print(f"{Colors.RED}  ✗ Installation failed{Colors.RESET}")
                    return False, "Installation failed"
        
        except Exception as e:
            print(f"{Colors.RED}  ✗ Error during installation: {e}{Colors.RESET}")
            return False, str(e)
    
    @staticmethod
    def fix_conda_path() -> Tuple[bool, str]:
        """Fix conda PATH issues and guide user."""
        print(f"\n{Colors.YELLOW}Conda installation detected but not in PATH{Colors.RESET}")
        print("This happens after installing Miniconda/Anaconda.\n")
        
        # Find what conda path exists
        conda_path = EnvironmentDetector.find_conda_installation()
        if not conda_path:
            return False, "Conda not found in common locations"
        
        conda_base = os.path.dirname(os.path.dirname(conda_path))
        
        print(f"Found Miniconda/Anaconda at: {Colors.CYAN}{conda_base}{Colors.RESET}\n")
        
        if sys.platform == "win32":
            print(f"{Colors.YELLOW}To fix this on Windows:{Colors.RESET}\n")
            print(f"1. Restart your terminal/PowerShell completely")
            print(f"   (Close all PowerShell windows and open a new one)\n")
            print(f"2. Then run this again:")
            print(f"   {Colors.CYAN}python auto_setup.py{Colors.RESET}\n")
            print(f"Why? Installation programs add conda to PATH, but it only takes")
            print(f"effect after restarting your terminal.\n")
            print(f"Alternative fix (manual PATH setup):")
            print(f"  In PowerShell as Admin:")
            print(f"  [Environment]::SetEnvironmentVariable('Path', $env:Path + ';{conda_base}\\condabin', 'User')")
            print(f"  Then restart terminal\n")
            
            return False, f"Please restart terminal to activate conda PATH"
        else:
            print(f"{Colors.YELLOW}To fix this on Linux/Mac:{Colors.RESET}\n")
            print(f"1. Restart your terminal completely\n")
            print(f"2. Or run conda init:")
            print(f"   {Colors.CYAN}{conda_base}/bin/conda init{Colors.RESET}\n")
            print(f"3. Then restart terminal\n")
            print(f"4. Then run this again:")
            print(f"   {Colors.CYAN}python auto_setup.py{Colors.RESET}\n")
            
            return False, "Please restart terminal and run conda init"
    
    @staticmethod
    def create_venv() -> Tuple[bool, str]:
        """Create a virtual environment."""
        venv_path = os.path.join(BASE_DIR, "craftbot-env")
        
        print(f"\n{Colors.CYAN}Creating virtual environment...{Colors.RESET}")
        print(f"Location: {venv_path}")
        
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", venv_path],
                timeout=120,
                check=True
            )
            
            # Get Python executable in venv
            if sys.platform == "win32":
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                activate_cmd = os.path.join(venv_path, "Scripts", "activate.bat")
            else:
                python_exe = os.path.join(venv_path, "bin", "python")
                activate_cmd = os.path.join(venv_path, "bin", "activate")
            
            print(f"{Colors.GREEN}✓ Virtual environment created{Colors.RESET}")
            return True, python_exe
        
        except Exception as e:
            print(f"{Colors.RED}✗ Failed to create venv: {e}{Colors.RESET}")
            return False, ""
    
    @staticmethod
    def fix_corrupted_packages() -> bool:
        """Fix corrupted packages."""
        print(f"\n{Colors.CYAN}Fixing corrupted packages...{Colors.RESET}")
        
        try:
            # Remove corrupted opencv
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", "opencv-python"],
                capture_output=True,
                timeout=30
            )
            
            # Reinstall opencv
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "opencv-python", "--no-cache-dir"],
                capture_output=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ OpenCV fixed{Colors.RESET}")
                return True
            else:
                print(f"{Colors.YELLOW}⚠ OpenCV fix may have issues{Colors.RESET}")
                return False
        
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Error fixing packages: {e}{Colors.RESET}")
            return False
    
    @staticmethod
    def upgrade_lxml() -> bool:
        """Upgrade lxml to compatible version."""
        print(f"\n{Colors.CYAN}Upgrading lxml...{Colors.RESET}")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "lxml>=4.9.3"],
                capture_output=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ lxml upgraded{Colors.RESET}")
                return True
            else:
                print(f"{Colors.YELLOW}⚠ lxml upgrade may have issues{Colors.RESET}")
                return False
        
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Error upgrading lxml: {e}{Colors.RESET}")
            return False
    
    @staticmethod
    def upgrade_greenlet() -> bool:
        """Pre-install greenlet to prevent compilation errors."""
        if sys.version_info < (3, 9) or sys.platform != "win32":
            return True
        
        print(f"\n{Colors.CYAN}Pre-installing greenlet (prevents compilation errors)...{Colors.RESET}")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "--only-binary", ":all:", "greenlet"],
                capture_output=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✓ Greenlet pre-installed{Colors.RESET}")
                return True
            else:
                print(f"{Colors.YELLOW}⚠ Greenlet pre-install skipped{Colors.RESET}")
                return False
        
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Error pre-installing greenlet: {e}{Colors.RESET}")
            return False


# ==========================================
# MAIN AUTO SETUP
# ==========================================
def print_header(title: str):
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE} {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def save_setup_state(venv_path: str, python_exe: str):
    """Save setup configuration for next script."""
    config = {
        "venv_path": venv_path,
        "python_exe": python_exe,
        "setup_complete": True,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "platform": sys.platform,
    }
    
    try:
        with open(SETUP_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass


def load_setup_state() -> Optional[Dict]:
    """Load previous setup configuration."""
    try:
        if os.path.exists(SETUP_CONFIG):
            with open(SETUP_CONFIG, 'r') as f:
                return json.load(f)
    except:
        pass
    return None


def main():
    """Main auto-setup flow."""
    print_header("🚀 CraftBot Automatic Environment Setup v1.0")
    
    # Check if already setup
    existing_setup = load_setup_state()
    if existing_setup and existing_setup.get("setup_complete"):
        print(f"{Colors.GREEN}✓ Setup already completed!{Colors.RESET}")
        print(f"\n{Colors.CYAN}Next step: Run the main installer{Colors.RESET}")
        print(f"\n  If using created venv, activate it first:")
        
        if sys.platform == "win32":
            print(f"    .\\craftbot-env\\Scripts\\activate")
        else:
            print(f"    source craftbot-env/bin/activate")
        
        print(f"\n  Then run:")
        print(f"    python install.py --conda")
        return 0
    
    # Step 1: Detect environment
    print_header("🔍 Detecting Environment")
    
    info = EnvironmentDetector.get_python_info()
    
    print(f"Python Version: {Colors.CYAN}{info['version']}{Colors.RESET}")
    print(f"Executable:     {Colors.CYAN}{info['executable']}{Colors.RESET}")
    print(f"Environment:    {Colors.CYAN}", end="")
    if info["is_conda"]:
        print("Conda/Anaconda", end="")
    elif info["is_venv"]:
        print("Virtual Environment", end="")
    else:
        print("Global Python", end="")
    print(Colors.RESET)
    
    # Step 2: Detect issues
    print_header("⚠️  Checking for Issues")
    
    issues = EnvironmentDetector.detect_issues()
    
    if not issues:
        print(f"{Colors.GREEN}✓ No major issues detected!{Colors.RESET}")
    else:
        for issue in issues:
            icon = "❌" if issue["severity"] == "error" else "⚠️ "
            print(f"{icon} {issue['message']}")
            if issue.get("fix_auto"):
                print(f"   → Auto-fixing: {issue['solution']}")
            else:
                print(f"   → Manual fix: {issue['solution']}")
    
    # Step 2b: Check if conda is installed and available
    print(f"\n{Colors.CYAN}🔍 Checking for Conda...{Colors.RESET}")
    conda_found, conda_path, conda_msg = EnvironmentCreator.check_conda_path()
    
    if conda_found:
        print(f"{Colors.GREEN}✓ Conda found!{Colors.RESET}")
        print(f"  Location: {conda_msg}")
    else:
        # Conda not found anywhere - auto-install it
        print(f"{Colors.YELLOW}⚠️  Conda not found - auto-installing Miniconda...{Colors.RESET}")
        install_success, install_msg = EnvironmentCreator.auto_install_miniconda()
        
        if not install_success:
            print(f"\n{Colors.RED}❌ Miniconda installation failed{Colors.RESET}")
            print(f"{Colors.YELLOW}Please install manually: https://docs.conda.io/en/latest/miniconda.html{Colors.RESET}")
            print(f"\nThen restart your terminal and run this script again.")
            return 1
        else:
            print(f"\n{Colors.GREEN}✓ Miniconda installed: {install_msg}{Colors.RESET}")
            print(f"{Colors.CYAN}IMPORTANT: Please restart your terminal now for the PATH to update!{Colors.RESET}")
            return 1  # Exit so user can restart terminal

    
    # Step 3: Fix auto-fixable issues
    auto_fixable = [i for i in issues if i.get("fix_auto")]
    if auto_fixable:
        print_header("🔧 Auto-Fixing Issues")
        
        for issue in auto_fixable:
            if issue["name"] == "opencv_corrupted":
                EnvironmentCreator.fix_corrupted_packages()
            elif issue["name"] == "lxml_old":
                EnvironmentCreator.upgrade_lxml()
            elif issue["name"] == "conda_python_39_greenlet":
                # Will create fresh venv instead
                pass
    
    # Step 4: Decide environment type
    print_header("🏗️  Setting Up Environment")
    
    blocking_issues = [i for i in issues if i["severity"] == "error" and not i.get("fix_auto")]
    
    if blocking_issues:
        print(f"{Colors.RED}❌ Blocking issues found that require manual fix:{Colors.RESET}")
        for issue in blocking_issues:
            print(f"  • {issue['message']}")
            print(f"    Solution: {issue['solution']}")
        print(f"\n{Colors.YELLOW}Please fix these issues then run this script again.{Colors.RESET}")
        return 1
    
    # Create virtual environment if needed
    should_create_venv = False
    
    # Problem cases that need venv
    if info["version_info"] >= (3, 9) and info["is_conda"]:
        print(f"\n{Colors.YELLOW}Python {info['version']} with Conda detected.{Colors.RESET}")
        print(f"This combination has known greenlet issues.")
        print(f"{Colors.CYAN}Creating clean virtual environment instead...{Colors.RESET}")
        should_create_venv = True
    
    # Ask user if not in venv yet
    if not info["is_venv"] and not should_create_venv:
        print(f"\n{Colors.CYAN}Currently using: {info['executable']}{Colors.RESET}")
        print(f"(Not in a virtual environment)")
        print(f"\n{Colors.YELLOW}Recommendation: Create virtual environment{Colors.RESET}")
        print(f"This isolates CraftBot dependencies from system Python.")
        
        # AUTO-CREATE VENV - NO PROMPT
        print(f"{Colors.CYAN}Auto-creating virtual environment...{Colors.RESET}")
        should_create_venv = True
    
    # Create venv if decided
    if should_create_venv:
        success, venv_python = EnvironmentCreator.create_venv()
        
        if success:
            print(f"\n{Colors.GREEN}✓ Virtual environment ready!{Colors.RESET}")
            print(f"\nActivate it with:")
            if sys.platform == "win32":
                print(f"  {Colors.CYAN}.\\craftbot-env\\Scripts\\activate{Colors.RESET}")
            else:
                print(f"  {Colors.CYAN}source craftbot-env/bin/activate{Colors.RESET}")
            
            # Pre-fix for the venv
            print(f"\n{Colors.CYAN}Pre-installing tools in new environment...{Colors.RESET}")
            EnvironmentCreator.upgrade_greenlet()
            
            save_setup_state("craftbot-env", venv_python)
        else:
            print(f"{Colors.RED}✗ Failed to create virtual environment{Colors.RESET}")
            return 1
    else:
        # Using existing environment
        print(f"\n{Colors.GREEN}✓ Using current Python environment{Colors.RESET}")
        
        # Pre-fix greenlet on Windows Python 3.9+
        if sys.version_info >= (3, 9) and sys.platform == "win32":
            EnvironmentCreator.upgrade_greenlet()
        
        save_setup_state("", sys.executable)
    
    # Step 5: Final instructions
    print_header("✅ Setup Complete!")
    
    print(f"{Colors.BOLD}Next step: Run the main installer{Colors.RESET}\n")
    
    if should_create_venv:
        print(f"1. {Colors.CYAN}Activate the virtual environment:{Colors.RESET}")
        if sys.platform == "win32":
            print(f"   .\\craftbot-env\\Scripts\\activate")
        else:
            print(f"   source craftbot-env/bin/activate")
        print()
    
    print(f"2. {Colors.CYAN}Run the main installer:{Colors.RESET}")
    print(f"   python install.py --conda")
    print()
    
    print(f"3. {Colors.CYAN}Wait for installation to complete (5-10 minutes){Colors.RESET}")
    print()
    
    print(f"4. {Colors.CYAN}Run CraftBot:{Colors.RESET}")
    print(f"   python run.py")
    print()
    
    print(f"{Colors.GREEN}Everything is ready!{Colors.RESET} 🎉\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)
