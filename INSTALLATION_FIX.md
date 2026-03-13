# CraftBot Installation Fix - Updated Installer Scripts

## What Was Fixed

The installation scripts have been updated to provide better error handling and clearer guidance. Here are the key improvements:

### 1. **Kali Linux & PEP 668 Support** (NEW)
**Problem:** On Kali Linux and other systems with externally-managed Python environments, pip installation fails with "externally-managed-environment" error.

**Solution:**
- Detects PEP 668 errors automatically
- First attempts installation with `--break-system-packages` flag
- Provides clear guidance on using virtual environments or conda
- Shows helpful error messages with actionable solutions

**If you encounter this error:**
```bash
# Option 1: Use a virtual environment (RECOMMENDED)
python3 -m venv craftbot-env
source craftbot-env/bin/activate  # Linux/macOS
# OR on Windows: .\craftbot-env\Scripts\activate
python install.py

# Option 2: Use conda environment
python install.py --conda

# Option 3: Allow system package installation (last resort)
python install.py  # Will auto-retry with --break-system-packages
```

### 2. **Pip Cache & TMPDIR Issues** (NEW)
**Problem:** Large pip installations (especially torch) fail due to pip cache size limits or disk space issues.

**Solution:**
- Automatically sets TMPDIR to ~/pip-tmp for pip operations
- Creates temporary directory if it doesn't exist
- Bypasses common cache-related issues
- Applies to both core dependencies and OmniParser/torch installation

**If you still have disk space issues:**
```bash
# Clear pip cache
pip cache purge

# Or run with custom tmp directory
TMPDIR=/path/to/large/disk python install.py
```

### 3. **PyTorch Installation** (IMPROVED)
**Problem:** PyTorch installation fails with unclear error messages, especially on Kali.

**Solution:**
- Better error detection and reporting
- Automatic fallback from GPU to CPU-only PyTorch
- Identifies disk space and PEP 668 specific errors
- Clear troubleshooting guidance for PyTorch issues

**If torch installation fails:**
```bash
# Try CPU-only mode
python install.py --gui --cpu-only

# Or use conda (recommended for data science)
python install.py --gui --conda

# Clear pip cache first
pip cache purge
python install.py --gui --cpu-only
```

### 4. **Playwright Browser Installation** (RESTORED)
**Problem:** Playwright chromium installation was failing silently with unclear error messages.

**Solution:** 
- Better error handling that catches and reports failures clearly
- Installation continues even if Playwright fails (it's not critical for browser mode)
- Clear guidance on how to manually install Playwright if needed
- Shows first 300 chars of actual error for debugging

### 5. **Browser Frontend Setup** (IMPROVED)
**Problem:** npm dependency installation had no feedback and failed with generic messages.

**Solution:**
- Checks if Node.js/npm is installed BEFORE trying to use it
- Detects if `node_modules` already exists to skip redundant installations
- Provides step-by-step installation instructions if npm is missing
- Better progress messages with clear troubleshooting steps

## How to Fix Your Current Issue

### Option 1: Re-run the Installer (Recommended)
The updated installer should now handle everything:

```bash
python install.py
```

This will:
1. ✓ Check/install core Python dependencies
2. ✓ Check if Node.js is available
3. ✓ Install frontend npm packages (if Node.js is found)
4. ✓ Attempt Playwright installation (but won't fail if it doesn't work)
5. ✓ Start CraftBot automatically

### Manual Setup (If Automatic Installation Doesn't Work)

If automatic installation still doesn't work, manually install dependencies:

1. **Install Node.js** (required for browser interface)
   - Download from: https://nodejs.org/
   - Choose LTS (Long-Term Support) version
   - Install and restart your terminal

2. **Verify Installation**
   ```bash
   node --version
   npm --version
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd app/ui_layer/browser/frontend
   npm install
   ```

4. **Run CraftBot**
   ```bash
   python run.py
   ```

### Option 3: Skip Browser Mode (TUI Mode)

If you can't or don't want to use the browser interface:

```bash
python run.py --tui
```

This launches CraftBot in Terminal UI mode without needing Node.js/npm.

## Playwright Chromium Note

Playwright chromium is only needed for WhatsApp Web integration. It's optional for basic CraftBot functionality.

If you need it later, install manually:
```bash
playwright install chromium
```

## Key Improvements in Updated Scripts

### `install.py` improvements:
- ✓ Playwright installation errors are handled gracefully
- ✓ Non-critical failures don't stop the installation
- ✓ npm installation checks for Node.js availability first
- ✓ Better error messages guide users to solutions
- ✓ Skip npm install if node_modules already exists

### `run.py` improvements:
- ✓ Frontend startup checks all dependencies before attempting launch
- ✓ Detailed troubleshooting guide when frontend fails
- ✓ Clear instructions for installing Node.js
- ✓ Better error messages with actionable steps

## Still Having Issues?

### Kali Linux Specific Issues

If you're running on Kali Linux and encounter "externally-managed-environment" errors:

**Method 1: Virtual Environment (Recommended)**
```bash
# Create virtual environment
python3 -m venv craftbot-env

# Activate it
source craftbot-env/bin/activate

# Now run installation
python install.py
```

**Method 2: Conda Environment**
```bash
python install.py --conda
```

**Method 3: Allow System Packages (Less Recommended)**
The installer will automatically retry with `--break-system-packages` if enabled. This modifies system Python but is less clean than virtual environments.

### Torch/GPU Installation Issues

If torch installation fails on Kali or other systems:

```bash
# First, clear pip cache to free disk space
pip cache purge

# Try CPU-only installation
python install.py --gui --cpu-only

# If using GUI mode, conda is more reliable for torch
python install.py --gui --conda
```

### Disk Space Issues

If pip installation fails due to disk space:

```bash
# Clear npm cache (if installed)
npm cache clean --force

# Clear pip cache  
pip cache purge

# Use a different temporary directory with more space
mkdir -p /mnt/large-disk/pip-tmp  # Or any path with more disk space
TMPDIR=/mnt/large-disk/pip-tmp python install.py

# Check available disk space
df -h
```

### General Troubleshooting

1. **Check Python version**: `python --version` (need 3.10+)
2. **Check Node.js**: `node --version` (if using browser mode)
3. **Check npm**: `npm --version` (if using browser mode)
4. **Clear and reinstall frontend**:
   ```bash
   cd app/ui_layer/browser/frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **Try TUI mode as fallback**:
   ```bash
   python run.py --tui
   ```

## Summary of Command Changes

- **Full installation with browser**: `python install.py`
- **Run browser mode**: `python run.py` (default)
- **Run TUI mode** (no browser needed): `python run.py --tui`
- **With conda** (if installed): `python install.py --conda`
- **With GUI mode**: `python install.py --gui` (requires additional setup)

The updated scripts will now guide you through any missing dependencies with clear, actionable instructions.
