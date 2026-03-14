#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CraftBot - Complete Automatic Setup

ONE COMMAND THAT DOES EVERYTHING:
    python setup_complete.py

Automatically:
1. Finds or installs Miniconda
2. Sets up Python environment
3. Installs all dependencies
4. Ready to launch CraftBot

NO USER PROMPTS!
"""

import os
import sys
import subprocess
import json

# Fix encoding
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_step(msg):
    print(f"\n📌 {msg}")

def print_ok(msg):
    print(f"✓ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def load_conda_config():
    """Load conda configuration if it exists."""
    if os.path.exists("conda_config.json"):
        with open("conda_config.json", "r") as f:
            return json.load(f)
    return None

def run_command(cmd, description=""):
    """Run a command and show description."""
    if description:
        print_step(description)
    try:
        result = subprocess.run(cmd, shell=False)
        return result.returncode == 0
    except Exception as e:
        print_error(f"Command failed: {e}")
        return False

def main():
    """Complete setup: conda -> environment -> install -> done"""
    print("\n" + "="*60)
    print("🚀 CraftBot - Complete Auto-Setup")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    # STEP 1: Find or install Miniconda
    print_step("Finding or installing Miniconda")
    conda_config = load_conda_config()
    
    if not conda_config:
        print("conda_config.json not found - running find_conda.py...")
        if not run_command([sys.executable, "find_conda.py"]):
            print_error("Failed to setup conda")
            return 1
        conda_config = load_conda_config()
        if not conda_config:
            print_error("Could not load conda config after find_conda.py")
            return 1
    
    conda_exe = conda_config.get('conda_exe')
    print_ok(f"Using conda: {conda_exe}")
    
    # STEP 2: Auto-setup environment
    print_step("Auto-setting up Python environment")
    if not run_command([sys.executable, "auto_setup.py"]):
        print("⚠️  auto_setup.py had issues, continuing...")
    
    # STEP 3: Install all packages
    print_step("Installing dependencies (5-15 minutes)")
    if not run_command([sys.executable, "install.py", "--conda"]):
        print("⚠️  Conda install failed, trying pip...")
        if not run_command([sys.executable, "install.py"]):
            print_error("Installation failed")
            return 1
    
    # STEP 4: Done!
    print("\n" + "="*60)
    print("✨ SETUP COMPLETE!")
    print("="*60)
    print("\nYour CraftBot is ready to launch!")
    print("\nNext commands:")
    print("  python run.py              # Launch CraftBot")
    print("  python run_tui.py          # Configure API keys")
    print("\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[CANCELLED] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
