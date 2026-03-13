# Installation Script Fixes - Summary of Changes

## Overview

The CraftBot installation script has been enhanced to handle common issues, especially on Kali Linux. The fixes focus on:

1. PEP 668 errors (externally-managed-environment)
2. Pip cache size issues
3. PyTorch installation failures
4. Better error reporting and user guidance

## Files Modified

### 1. `install.py` - Main Installation Script

#### Change 1: Enhanced `setup_pip_environment()` Function
**Location**: Around line 530
**What Changed**:
- Added automatic detection of PEP 668 errors
- Sets `TMPDIR` environment variable to bypass pip cache issues
- Automatically creates `~/pip-tmp` directory for temporary files
- Implements fallback strategy: standard install → `--break-system-packages` → helpful guidance
- Provides 3 clear options for users encountering PEP 668 errors

**Why**:
- Kali Linux and other distributions use PEP 668 to prevent system package modifications
- Large packages like torch need significant cache space; TMPDIR helps manage this
- Fallback strategy ensures installation completes if possible, while guiding users to best practices

#### Change 2: Improved `run_omni_cmd()` Function in `setup_omniparser()`
**Location**: Around line 625
**What Changed**:
- Added TMPDIR environment variable to OmniParser environment commands
- Ensures torch installation uses the custom temp directory
- Creates temp directory automatically

**Why**:
- OmniParser requires torch, which is large and cache-intensive
- Same TMPDIR strategy prevents cache issues during torch installation
- Consistent behavior across core and GUI installation

#### Change 3: Enhanced PyTorch Installation Error Handling
**Location**: Around line 700
**What Changed**:
- Detects specific error conditions (disk space, PEP 668 errors)
- Provides targeted troubleshooting for each error type
- Better error messages with links to PyTorch documentation
- Added recommendations to use conda for GPU installation

**Why**:
- PyTorch is the most problematic package to install
- Different errors require different solutions (disk space vs. permissions)
- Conda handles PyTorch dependencies more reliably

#### Change 4: Improved Dependencies Installation
**Location**: Around line 720
**What Changed**:
- Passes TMPDIR environment variable to all pip install commands
- Adds minimal error reporting (hides PEP 668 errors during reporting)
- Continues installation even if some dependencies fail

**Why**:
- Consistent cache management across all pip operations
- Some dependencies are optional and shouldn't block installation
- Reduces noise in error output

### 2. `INSTALLATION_FIX.md` - Installation Documentation

#### What Changed**:
- Added comprehensive section on PEP 668 errors
- Added section on pip cache and TMPDIR management
- Added specific section for Kali Linux
- Added section on PyTorch installation troubleshooting
- Reorganized structure for better clarity

**Why**:
- Users need clear documentation on new features
- Kali users need specific guidance
- Multiple installation methods need to be documented

### 3. `KALI_INSTALLATION_GUIDE.md` - New File (This File)

#### What Added**:
- Dedicated guide for Kali Linux users
- Step-by-step instructions for virtual environments
- Troubleshooting guide specific to Kali issues
- Quick reference commands
- Explanation of why certain approaches are recommended

**Why**:
- Kali users face unique challenges (system-managed Python)
- Dedicated guide reduces confusion
- Virtual environment approach is the best practice

## Key Features of the Fixes

### 1. Automatic TMPDIR Management
```python
tmp_dir = os.path.expanduser("~/pip-tmp")
os.makedirs(tmp_dir, exist_ok=True)
# Passed to all pip install commands
env_extras={"TMPDIR": tmp_dir}
```

**Benefits**:
- Bypasses pip cache size limits
- Creates directory automatically if missing
- Consistent across all installations
- No manual steps needed

### 2. PEP 668 Error Detection and Handling
```python
if "externally-managed-environment" in error_output:
    # Show 3 options to user
    # Retry with --break-system-packages as fallback
```

**Benefits**:
- Automatically detects the specific error
- Provides clear options to user
- Attempts to recover if user chooses
- Guides to best practices (virtual environment, conda)

### 3. Better Error Reporting
- Shows relevant error details only
- Provides specific troubleshooting for different errors
- Links to external documentation when needed
- Avoids overwhelming users with technical jargon

## Installation Flows

### Before Fixes
1. Run `python install.py`
2. Fails with cryptic "externally-managed-environment" error
3. User frustrated, unsure what to do
4. Torch installation might fail silently

### After Fixes

#### Path 1: Virtual Environment (Recommended)
```bash
python3 -m venv craftbot-env
source craftbot-env/bin/activate
python install.py  # ✓ Works smoothly
```

#### Path 2: Auto-Retry with --break-system-packages  
```bash
python install.py
# Shows error, explains options
# User can choose Option 3 to auto-retry
# ✓ Completes if system allows
```

#### Path 3: Conda Environment
```bash
python install.py --conda  # ✓ Cleaner for conda users
```

## Technical Details

### TMPDIR Environment Variable
- **Purpose**: Specifies temporary directory for pip operations
- **Default Value** (after fix): `~/pip-tmp`
- **Why Used**: 
  - Avoids pip cache size limits
  - Helps when /tmp is full or restricted
  - Common workaround on systems with limited disk space

### PEP 668 (Python Externally-Managed Environment)
- **What It Is**: Python 3.11+ security feature for system package managers
- **Where It Affects**: Kali Linux, Ubuntu (with external package management), others
- **Solutions**:
  1. Virtual environment (cleanest)
  2. Conda environment (good for ML)
  3. `--break-system-packages` (least recommended)

### Why PyTorch is Special
- **Size**: ~5+ GB including all dependencies
- **Complexity**: Requires specific CUDA version for GPU support
- **Sensitivity**: Needs careful cache management, CPU fallback, etc.
- **Status**: Only needed for GUI mode (OmniParser)

## Testing the Fixes

To verify fixes work:

```bash
# Test 1: Virtual environment path
python3 -m venv test-env
source test-env/bin/activate
python install.py

# Test 2: Conda path (if conda available)
python install.py --conda

# Test 3: Direct system install (will show PEP 668 handling)
python install.py  # On Kali, will show options

# Test 4: GUI mode with CPU-only torch
python install.py --gui --cpu-only

# Test 5: GUI mode with conda (most reliable)
python install.py --gui --conda
```

## Backward Compatibility

All changes are backward compatible:
- Existing users won't see any changes (transparent improvement)
- Virtual environment users benefit from TMPDIR management
- Non-Kali systems work exactly as before (no PEP 668 errors)
- Conda users get improved error handling
- Failures are handled gracefully with helpful messages

## Future Improvements

Potential enhancements:
1. Add pre-flight checks (Python version, disk space, etc.)
2. Interactive configuration wizard
3. Automatic virtual environment creation
4. Progress bar for large downloads
5. Retry logic with exponential backoff
6. Offline installation support

---

**Version**: 1.0
**Date**: 2026-03-13
**Scope**: Core installation and OmniParser/GPU mode setup
