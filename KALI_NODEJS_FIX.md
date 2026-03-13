# Kali Linux Browser UI Installation Fix

## Problem
On Kali Linux, CraftBot installation was completing but the browser UI would never open. The error showed:
```
Error: Failed to start browser frontend.
Warning: npm not found in PATH
Browser interface requires Node.js and npm.
```

## Root Cause
The browser frontend requires Node.js and npm to run, but the installation script was not automatically installing Node.js on Linux systems. It only warned users to download and install manually.

## Solution
Added automatic Node.js installation to both `install.py` and `run.py` scripts:

### What Changed

#### 1. **install.py**
- **New function `install_nodejs_linux()`**: Automatically detects and installs Node.js on Linux systems
  - Supports: apt-get, apt, dnf, yum, pacman, zypper
  - Works with Debian, Ubuntu, Kali, RedHat, Fedora, Arch, openSUSE, etc.
  - Checks if Node.js is already installed before attempting installation
  - Verifies successful installation and shows version info

- **Modified `install_browser_frontend()`**: 
  - Now calls `install_nodejs_linux()` before checking for npm
  - Provides fallback manual installation instructions if auto-install fails
  - Continues with npm package installation after Node.js is ready

#### 2. **run.py**
- **New function `_try_install_nodejs_linux()`**: Same Node.js auto-installation logic
  - Used when starting the browser interface if npm is missing
  - Allows recovery if Node.js wasn't properly installed during `install.py`

- **Fixed `launch_frontend()` function**:
  - Removed unreachable duplicate code
  - Added auto-install attempt before failing
  - Attempts to auto-install Node.js on Linux before throwing an error

## How to Test (Kali Linux)

### Step 1: Run Fresh Installation
```bash
cd /path/to/CraftBot
python install.py
```

Expected output:
```
🔧 Installing Node.js...
   Found apt, installing Node.js...
✓ Node.js installed successfully
   Node.js v18.x.x (or higher)
   npm x.x.x

🔧 Installing browser frontend dependencies...
✓ Browser frontend dependencies installed
```

### Step 2: Verify Browser Starts
After installation completes, CraftBot should automatically open browser UI at `http://localhost:3001`

### Step 3: Manual Testing (if needed)
```bash
# Verify Node.js is installed
node --version
npm --version

# Start CraftBot manually
python run.py

# Should show "Browser Interface ready at http://localhost:3001"
# And automatically open the browser
```

## For Existing Installations

If you already ran `install.py` before this fix and it failed:

### Option 1: Re-run Installation (Recommended)
```bash
python install.py
```

### Option 2: Manual Node.js Installation
```bash
# For Kali/Debian/Ubuntu
sudo apt update
sudo apt install -y nodejs npm

# Verify installation
node --version
npm --version

# Then run
python install.py
```

### Option 3: Use NodeSource Repository (Recommended for Kali)
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version
npm --version

# Then run
python install.py
```

## Troubleshooting

### Issue: Sudo Password Required
The auto-install uses `sudo` for package manager commands. You may be prompted for your password.
- Solution: Enter your Kali user password when prompted

### Issue: "Failed to start browser frontend" Still Appears
This might mean the installation is cached. Try:
```bash
# Clear npm cache
npm cache clean --force

# Clear node_modules in frontend
rm -rf app/ui_layer/browser/frontend/node_modules

# Re-run installation
python install.py
```

### Issue: Browser UI Opens but Shows Error
- Check that the backend (app) is running properly
- Verify all dependencies were installed: `pip list | grep -i craftbot`
- Check logs in terminal for specific errors

### Issue: "npm: command not found" in run.py
Path might not be updated. Try:
```bash
# Option 1: Restart terminal/session
exit
# Then re-login and run: python run.py

# Option 2: Manual install
cd app/ui_layer/browser/frontend
npm install
npm run dev

# Option 3: Check npm path
which npm
```

## Files Modified

1. **install.py**
   - Added `install_nodejs_linux()` function (lines 561-624)
   - Modified `install_browser_frontend()` function (lines 653-694)

2. **run.py**
   - Added `_try_install_nodejs_linux()` function (lines 178-222)
   - Fixed duplicate code in `launch_frontend()` (removed lines 236-258)
   - Modified npm check in `launch_frontend()` (lines 213-220)

## Notes for Different Kali Setups

### Kali in VMware/VirtualBox/Docker
- Should work with built-in apt package manager
- May require internet access for downloading Node.js packages
- Ensure VM has sufficient disk space (>500MB for Node.js + npm packages)

### Kali on Bare Metal / WSL
- Should work with apt package manager
- If WSL, may need to configure WSL2 networking

### Kali in SSH/Remote Terminal
- Auto-browser opening will not work (script detects this and shows URL)
- Manual installation via `sudo apt install nodejs npm` recommended before running
- Browser must be opened manually on your local machine

## Support

If browser still won't open after trying these fixes:
1. Check that Node.js installed: `node --version`
2. Check that npm installed: `npm --version`
3. Check frontend exists: `ls app/ui_layer/browser/frontend`
4. Check node_modules: `ls app/ui_layer/browser/frontend/node_modules`
5. Run manually: `cd app/ui_layer/browser/frontend && npm run dev`
6. Look for specific error messages in the terminal output

---

**Version**: March 2026
**Status**: Fixed and tested
**Related Issues**: Browser UI not starting on Kali Linux
