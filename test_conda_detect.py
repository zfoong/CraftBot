#!/usr/bin/env python3
"""Quick test of conda detection"""
import sys
import os

# Test 1: Check conda at known location
conda_path = r"C:\Users\ganiy\miniconda3\Scripts\conda.exe"
print(f"✓ Test 1: Conda at known path exists: {os.path.exists(conda_path)}")
if os.path.exists(conda_path):
    print(f"  Path: {conda_path}")

# Test 2: Import and test conda detection from install.py
sys.path.insert(0, '.')
try:
    from install import is_conda_installed, get_conda_command
    
    print(f"\n✓ Test 2: is_conda_installed() function")
    result = is_conda_installed()
    print(f"  Result: {result}")
    
    print(f"\n✓ Test 3: get_conda_command() function")
    cmd = get_conda_command()
    print(f"  Command: {cmd}")
    print(f"  Exists: {os.path.exists(cmd) if cmd else 'No command'}")
except Exception as e:
    print(f"✗ Error importing functions: {e}")
    import traceback
    traceback.print_exc()
