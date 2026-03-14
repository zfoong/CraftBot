#!/usr/bin/env python3
"""
Smart Conda Finder & Auto-Installer
====================================

This script:
1. Searches your system for conda
2. If found, returns the FULL PATH (doesn't rely on PATH env var)
3. If not found, AUTO-INSTALLS Miniconda
4. Updates PATH automatically
5. NO USER PROMPTS - just works

Usage:
    python find_conda.py
    
Output:
    Prints the full path to conda executable
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from pathlib import Path


class CondaFinder:
    """Find or install conda automatically."""
    
    def __init__(self):
        self.system = platform.system()
        self.conda_exe = None
        self.conda_dir = None
        self.is_windows = self.system == "Windows"
    
    def search_common_locations(self):
        """Search common conda installation locations."""
        print("🔍 Searching for Miniconda installation...", flush=True)
        
        # Common locations to search
        if self.is_windows:
            search_paths = [
                r"C:\miniconda3",
                r"C:\Miniconda3",
                r"C:\anaconda3",
                r"C:\Anaconda3",
                r"C:\Program Files\miniconda3",
                r"C:\Program Files\Miniconda3",
                r"C:\Program Files (x86)\miniconda3",
                os.path.expanduser(r"~\miniconda3"),
                os.path.expanduser(r"~\Miniconda3"),
                os.path.expanduser(r"~\anaconda3"),
                os.path.expanduser(r"~\Anaconda3"),
            ]
            exe_name = "conda.exe"
        else:
            search_paths = [
                os.path.expanduser("~/miniconda3"),
                os.path.expanduser("~/Miniconda3"),
                os.path.expanduser("~/anaconda3"),
                os.path.expanduser("~/Anaconda3"),
                "/opt/miniconda3",
                "/opt/anaconda3",
                "/usr/local/miniconda3",
                "/usr/local/anaconda3",
            ]
            exe_name = "conda"
        
        for path in search_paths:
            if self.is_windows:
                conda_path = os.path.join(path, "Scripts", exe_name)
            else:
                conda_path = os.path.join(path, "bin", exe_name)
            
            if os.path.exists(conda_path):
                self.conda_exe = conda_path
                self.conda_dir = path
                print(f"✓ Found at: {path}", flush=True)
                return True
        
        return False
    
    def search_in_path(self):
        """Try to find conda in system PATH."""
        if self.is_windows:
            result = subprocess.run(
                ["where", "conda.exe"],
                capture_output=True,
                text=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ["which", "conda"],
                capture_output=True,
                text=True,
                timeout=5
            )
        
        if result.returncode == 0:
            self.conda_exe = result.stdout.strip()
            self.conda_dir = os.path.dirname(os.path.dirname(self.conda_exe))
            print(f"✓ Found in PATH: {self.conda_dir}", flush=True)
            return True
        
        return False
    
    def verify_conda(self):
        """Verify conda works by getting version."""
        if not self.conda_exe:
            return False
        
        try:
            result = subprocess.run(
                [self.conda_exe, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ Version: {result.stdout.strip()}", flush=True)
                return True
        except Exception as e:
            print(f"⚠️  Could not verify conda: {e}", flush=True)
        
        return False
    
    def auto_install_miniconda(self):
        """Auto-install Miniconda without user interaction."""
        print("\n⚠️  Conda not found - Auto-installing Miniconda...", flush=True)
        
        # Install location - use user home directory to avoid permission issues
        if self.is_windows:
            install_path = os.path.expanduser(r"~\miniconda3")
            installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
            installer_file = "Miniconda3-latest-Windows-x86_64.exe"
        else:
            install_path = os.path.expanduser("~/miniconda3")
            if self.system == "Darwin":
                installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
                installer_file = "Miniconda3-latest-MacOSX-x86_64.sh"
            else:
                installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
                installer_file = "Miniconda3-latest-Linux-x86_64.sh"
        
        print(f"📥 Download location: {installer_url}", flush=True)
        print(f"📁 Installation path: {install_path}", flush=True)
        
        try:
            # Download installer
            print("📥 Downloading Miniconda installer...", flush=True)
            import urllib.request
            urllib.request.urlretrieve(installer_url, installer_file)
            print(f"✓ Downloaded: {installer_file}", flush=True)
            
            # Install Miniconda
            print("⚙️  Installing Miniconda...", flush=True)
            
            if self.is_windows:
                # Silent install on Windows
                cmd = [
                    installer_file,
                    "/InstallationType=JustMe",
                    "/AddMinicondaToPath=1",
                    "/S",  # Silent
                    f"/D={install_path}"
                ]
                subprocess.run(cmd, check=True)
            else:
                # Silent install on Linux/Mac
                os.chmod(installer_file, 0o755)
                cmd = [
                    "bash",
                    installer_file,
                    "-b",  # Batch mode
                    "-p",  # Prefix
                    install_path
                ]
                subprocess.run(cmd, check=True)
            
            print("✓ Miniconda installed!", flush=True)
            
            # Clean up installer
            try:
                os.remove(installer_file)
            except:
                pass
            
            # Set conda path
            self.conda_dir = install_path
            if self.is_windows:
                self.conda_exe = os.path.join(install_path, "Scripts", "conda.exe")
            else:
                self.conda_exe = os.path.join(install_path, "bin", "conda")
            
            return True
        
        except Exception as e:
            print(f"❌ Installation failed: {e}", flush=True)
            return False
    
    def add_to_path(self):
        """Add conda to system PATH."""
        if not self.conda_dir:
            return False
        
        if self.is_windows:
            scripts_dir = os.path.join(self.conda_dir, "Scripts")
            bin_dir = os.path.join(self.conda_dir, "Library", "bin")
        else:
            scripts_dir = os.path.join(self.conda_dir, "bin")
            bin_dir = None
        
        # Add to current process PATH
        if scripts_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = scripts_dir + os.pathsep + os.environ.get("PATH", "")
            print(f"✓ Added to PATH: {scripts_dir}", flush=True)
        
        if bin_dir and bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            print(f"✓ Added to PATH: {bin_dir}", flush=True)
        
        return True
    
    def save_config(self):
        """Save conda location to config file for other scripts."""
        config = {
            "conda_exe": self.conda_exe,
            "conda_dir": self.conda_dir,
            "system": self.system
        }
        
        with open("conda_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Config saved: conda_config.json", flush=True)


def main():
    """Find or install conda."""
    finder = CondaFinder()
    
    # Step 1: Search in PATH
    if finder.search_in_path():
        if finder.verify_conda():
            print("\n✨ Conda found and verified!", flush=True)
            print(f"Full path: {finder.conda_exe}", flush=True)
            finder.add_to_path()
            finder.save_config()
            return 0
    
    # Step 2: Search common locations
    if finder.search_common_locations():
        if finder.verify_conda():
            print("\n✨ Conda found and verified!", flush=True)
            print(f"Full path: {finder.conda_exe}", flush=True)
            finder.add_to_path()
            finder.save_config()
            return 0
    
    # Step 3: Auto-install
    print("\n" + "="*60)
    if finder.auto_install_miniconda():
        if finder.verify_conda():
            print("\n✨ Miniconda installed and verified!", flush=True)
            print(f"Full path: {finder.conda_exe}", flush=True)
            finder.add_to_path()
            finder.save_config()
            return 0
    
    print("\n❌ Could not find or install Miniconda", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
