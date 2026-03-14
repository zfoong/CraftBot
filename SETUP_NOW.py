#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CraftBot - SIMPLE Automatic Setup
Just download Miniconda and have user run it
"""

import os
import sys
import subprocess
import urllib.request
import platform
import webbrowser
import io

# Fix encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print("\n" + "="*70)
    print("  CraftBot - Automatic Installation Setup")
    print("="*70 + "\n")
    
    # Check if conda exists
    print("[1] Checking if Miniconda is installed...")
    result = subprocess.run(["where" if sys.platform == "win32" else "which", "conda"],
                          capture_output=True)
    
    if result.returncode == 0:
        print("    ✓ Miniconda is already installed!")
        print("\n[2] Running environment setup...")
        os.system("python auto_setup.py")
        return 0
    
    print("    ⚠ Miniconda not found\n")
    
    # Download Miniconda
    print("[2] Downloading Miniconda installer...")
    
    if sys.platform == "win32":
        url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
        file_path = os.path.expanduser("~/Downloads/Miniconda3-Windows.exe")
        install_cmd = f'start "" "{file_path}"'
    elif sys.platform == "darwin":
        url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
        file_path = "/tmp/Miniconda3-MacOS.sh"
        install_cmd = f"open {file_path}"
    else:
        url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
        file_path = "/tmp/Miniconda3-Linux.sh"
        install_cmd = f"bash {file_path}"
    
    try:
        print(f"    Downloading from: {url}\n")
        urllib.request.urlretrieve(url, file_path)
        print(f"    ✓ Downloaded to: {file_path}\n")
    except Exception as e:
        print(f"    ✗ Download failed: {e}\n")
        print("    Please download manually from:")
        print("    https://docs.conda.io/en/latest/miniconda.html\n")
        webbrowser.open("https://docs.conda.io/en/latest/miniconda.html")
        return 1
    
    # Instructions
    print("="*70)
    print("\n[3] IMPORTANT: Install Miniconda manually\n")
    
    if sys.platform == "win32":
        print("    The installer file was saved to:")
        print(f"    {file_path}\n")
        print("    ✓ Double-click the file to start the installer")
        print("    ✓ When prompted, choose these options:")
        print("      • 'Just Me' (not for all users)")
        print("      • Add Miniconda to PATH ✓ (CHECK THIS BOX)")
        print("      • Register Python ✓ (CHECK THIS BOX)\n")
        print("    Opening installer automatically...")
        os.system(install_cmd)
    
    elif sys.platform == "darwin":
        print("    To install on macOS:")
        print(f"    bash {file_path}\n")
        print("    Or open Finder and run the .pkg file\n")
    else:
        print("    To install on Linux:")
        print(f"    bash {file_path}\n")
        print("    OR download the graphical installer from:")
        print("    https://docs.conda.io/en/latest/miniconda.html\n")
    
    print("="*70)
    print("\n[NEXT STEPS]\n")
    print("    1. Install Miniconda using steps above")
    print("    2. CLOSE THIS TERMINAL COMPLETELY")
    print("    3. OPEN A NEW TERMINAL")
    print("    4. Run: python auto_setup.py")
    print("    5. Run: python install.py --conda") 
    print("    6. Run: python run.py\n")
    print("="*70 + "\n")
    
    input("Press ENTER once you've completed the installation...")
    
    # Try to continue
    print("\n[4] Checking if Miniconda is now available...")
    result = subprocess.run(["where" if sys.platform == "win32" else "which", "conda"],
                          capture_output=True)
    
    if result.returncode == 0:
        print("    ✓ Miniconda installed successfully!")
        print("\n[5] Running environment setup...")
        os.system("python auto_setup.py")
    else:
        print("    ⚠ Conda still not in PATH")
        print("\n    [SOLUTION 1] Restart your terminal completely and try again")
        print("    [SOLUTION 2] Manually add Miniconda to PATH:")
        if sys.platform == "win32":
            print("      • Open: Settings → System → About → Advanced system settings")
            print("      • Click: Environment Variables")
            print("      • Add: C:\\miniconda3\\condabin to PATH")
        else:
            print("      • Edit: ~/.bashrc or ~/.zshrc")
            print("      • Add: export PATH=~/miniconda3/bin:$PATH")
            print("      • Run: source ~/.bashrc")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
