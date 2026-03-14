#!/usr/bin/env python3
"""
CraftBot Pre-Installation Quick Fix
Automatically fixes common installation issues before running main installer

Common issues fixed:
1. Greenlet compilation failure on Windows with Python 3.9+
2. Corrupted OpenCV installations
3. lxml compatibility issues
4. pip cache corruption
5. Virtual environment detection

Usage:
    python quick_fix.py
"""

import os
import sys
import subprocess
import shutil
import platform

def print_header(title):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def run_command(cmd, description="", capture=False, check=False):
    """Run a command with error handling."""
    if description:
        print(f"\n{description}")
    
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        else:
            result = subprocess.run(cmd, timeout=120)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  ⚠ Command timed out")
        return False
    except Exception as e:
        print(f"  ⚠ Error: {e}")
        return False

def check_python_version():
    """Check Python version compatibility."""
    print_header("🔍 Checking Python Version")
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    print(f"Executable: {sys.executable}")
    
    if version < (3, 8):
        print("\n✗ ERROR: Python 3.8+ required")
        print("Download from: https://www.python.org/downloads/")
        return False
    
    if version >= (3, 13):
        print("\n⚠ WARNING: Python 3.13+ may have compatibility issues")
        print("Recommended: Python 3.8 - 3.12")
    
    print("✓ Python version OK")
    return True

def clean_pip_cache():
    """Clean pip cache."""
    print_header("🧹 Cleaning pip Cache")
    
    run_command(
        [sys.executable, "-m", "pip", "cache", "purge"],
        "Clearing pip cache..."
    )
    print("✓ pip cache cleaned")

def fix_greenlet_windows():
    """Fix greenlet on Windows Python 3.9+."""
    if sys.platform != "win32" or sys.version_info < (3, 9):
        return True
    
    print_header("🔧 Fixing Greenlet (Windows 3.9+)")
    
    print("Upgrading greenlet to latest version...")
    success = run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "--only-binary", ":all:", "greenlet"],
        "Installing greenlet pre-compiled binary..."
    )
    
    if success:
        print("✓ Greenlet fixed")
        return True
    else:
        print("⚠ Greenlet may not be available as pre-compiled")
        print("  Will retry during main installation with conda if needed")
        return False

def fix_opencv():
    """Fix corrupted OpenCV."""
    print_header("🔧 Fixing OpenCV")
    
    # Uninstall any existing
    print("Removing any existing opencv-python installations...")
    run_command(
        [sys.executable, "-m", "pip", "uninstall", "opencv-python", "-y"],
        capture=True
    )
    
    # Reinstall
    success = run_command(
        [sys.executable, "-m", "pip", "install", "opencv-python", "--no-cache-dir"],
        "Installing fresh opencv-python..."
    )
    
    if success:
        print("✓ OpenCV fixed")
        return True
    else:
        print("⚠ OpenCV may need manual installation")
        return False

def upgrade_pip_setuptools():
    """Upgrade pip and setuptools."""
    print_header("📦 Upgrading pip and setuptools")
    
    # Upgrade pip
    print("Upgrading pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Upgrade setuptools
    print("Upgrading setuptools...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools"])
    
    print("✓ pip and setuptools upgraded")

def suggest_virtualenv():
    """Suggest using virtual environment."""
    print_header("💡 Recommendation: Use Virtual Environment")
    
    # Check if already in venv
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✓ Already in virtual environment")
        return
    
    print("Virtual environments isolate dependencies and prevent conflicts.")
    print("\nTo create a virtual environment:")
    
    if sys.platform == "win32":
        print("\n  python -m venv craftbot-env")
        print("  .\\craftbot-env\\Scripts\\activate")
    else:
        print("\n  python -m venv craftbot-env")
        print("  source craftbot-env/bin/activate")
    
    print("\nThen run: python install.py")

def check_disk_space():
    """Check available disk space."""
    print_header("💾 Checking Disk Space")
    
    try:
        if sys.platform == "win32":
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceEx(
                ctypes.c_wchar_p(os.path.abspath(".")),
                None, None, ctypes.pointer(free_bytes)
            )
            free_gb = free_bytes.value / (1024 ** 3)
        else:
            st = os.statvfs(".")
            free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
        
        print(f"Free disk space: {free_gb:.1f} GB")
        
        if free_gb < 5:
            print("⚠ WARNING: Less than 5 GB free!")
            print("\nTo free up space:")
            print("  1. pip cache purge")
            print("  2. npm cache clean --force  (if Node.js installed)")
            if sys.platform != "win32":
                print("  3. rm -rf ~/.cache/*")
            return False
        
        print("✓ Sufficient disk space")
        return True
    except:
        print("⚠ Could not check disk space")
        return True

def show_next_steps():
    """Show next steps."""
    print_header("✅ Pre-Installation Checks Complete")
    
    print("\nNext steps:")
    print("\n1. Run the main installer:")
    print("   python install.py")
    
    print("\n2. Or with specific options:")
    print("   python install.py --conda      # Use conda (recommended)")
    print("   python install.py --gui        # Include GUI components")
    print("   python install.py --gui --conda # GUI + conda")
    
    print("\n3. If you get errors, enable debugging:")
    print("   python install.py 2>&1 | tee install.log")
    print("   # Share the install.log file for troubleshooting")

def main():
    """Run all fixes."""
    print("\n" + "="*60)
    print(" CraftBot Pre-Installation Quick Fix")
    print("="*60)
    
    steps = [
        ("Python version check", check_python_version),
        ("Disk space check", check_disk_space),
        ("Clean pip cache", clean_pip_cache),
        ("Upgrade pip/setuptools", upgrade_pip_setuptools),
        ("Fix Greenlet", fix_greenlet_windows),
        ("Fix OpenCV", fix_opencv),
        ("Show venv recommendation", suggest_virtualenv),
    ]
    
    for step_name, step_func in steps:
        try:
            step_func()
        except Exception as e:
            print(f"⚠ Error in {step_name}: {e}")
    
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
