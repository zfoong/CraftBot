#!/usr/bin/env python3
"""
Fix Conda PATH Issue

If you get "Conda not found" after installing Miniconda/Anaconda,
this script helps you add conda to your system PATH.

Usage:
    python fix_conda_path.py
"""

import os
import sys
import shutil
from pathlib import Path

def find_conda() -> str:
    """Find conda installation."""
    common_paths = [
        os.path.expanduser("~/miniconda3"),
        os.path.expanduser("~/Miniconda3"),
        os.path.expanduser("~/anaconda3"),
        os.path.expanduser("~/Anaconda3"),
        "C:\\miniconda3",
        "C:\\Miniconda3",
        "C:\\anaconda3",
        "C:\\Anaconda3",
        os.path.expanduser("~/opt/miniconda3"),
        "/opt/miniconda3",
        "/usr/local/miniconda3",
    ]
    
    for path in common_paths:
        if sys.platform == "win32":
            conda_exe = os.path.join(path, "condabin", "conda.bat")
        else:
            conda_exe = os.path.join(path, "bin", "conda")
        
        if os.path.exists(conda_exe):
            return path
    
    return None

def main():
    print("\n" + "="*60)
    print(" 🔧 Conda PATH Fix")
    print("="*60 + "\n")
    
    conda_path = find_conda()
    
    if not conda_path:
        print("❌ Conda not found in common locations")
        print("\nManual installation location:")
        print("  If you installed Miniconda/Anaconda to a custom location,")
        print("  please add that location to your PATH manually.\n")
        print("  On Windows: Start > Environment Variables > Edit PATH")
        print("  On Linux/Mac: Edit ~/.bashrc or ~/.zshrc\n")
        return 1
    
    print(f"✓ Found conda at: {conda_path}\n")
    
    if sys.platform == "win32":
        conda_bin = os.path.join(conda_path, "condabin")
        print("📋 To fix this on Windows:\n")
        print("Option 1 (Easiest): Restart your terminal")
        print("  1. Close ALL PowerShell/Command Prompt windows")
        print("  2. Open a NEW PowerShell window")
        print("  3. Run: python auto_setup.py\n")
        
        print("Option 2 (Permanent fix): Add conda to PATH manually")
        print(f"  1. Copy this path: {conda_bin}")
        print("  2. Press: Win + X → System")
        print("  3. Click: 'Advanced system settings'")
        print("  4. Click: 'Environment Variables...'")
        print("  5. Click: 'Edit' in Path (User variables)")
        print("  6. Click: 'New'")
        print(f"  7. Paste: {conda_bin}")
        print("  8. Click OK three times")
        print("  9. Close ALL terminals and open a new one")
        print("  10. Run: python auto_setup.py\n")
        
        print("Option 3 (PowerShell automatic):")
        print("  Run as Administrator:")
        print(f"  [Environment]::SetEnvironmentVariable('Path',")
        print(f"    $env:Path + ';{conda_bin}', 'User')")
        print("  Then close and reopen terminal\n")
        
    else:
        conda_bin = os.path.join(conda_path, "bin")
        print("📋 To fix this on Linux/Mac:\n")
        print("Option 1 (Easiest): Restart your terminal")
        print("  1. Close all terminal windows")
        print("  2. Open a new terminal")
        print("  3. Run: python auto_setup.py\n")
        
        print("Option 2 (Initialize conda):")
        print(f"  Run: {conda_path}/bin/conda init")
        print("  Then restart your terminal\n")
        
        print("Option 3 (Manual PATH setup):")
        print(f"  Add to ~/.bashrc or ~/.zshrc:")
        print(f"  export PATH=\"{conda_bin}:$PATH\"")
        print("  Then run: source ~/.bashrc")
        print("  Or restart terminal\n")
    
    print("="*60)
    print("After completing any of the above options:")
    print("  1. Run: python auto_setup.py")
    print("  2. Follow the instructions it gives")
    print("  3. Installation should work smoothly!\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
