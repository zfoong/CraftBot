# CraftBot Installation Guide for Kali Linux

This guide helps you install CraftBot on Kali Linux, which has some unique considerations due to PEP 668 (externally-managed-environment restrictions) and disk space limitations.

## The Disk Space Problem 🛑

**Common Error on Kali:**
```
❌ DISK SPACE ERROR - No space left on device
pip._internal.utils.packaging.get_file_hash: No space left on device
```

**Why This Happens:**
- Kali Linux VMs often have limited disk space (20-30GB)
- Large packages like PyTorch (torch) are 5GB+ each
- pip cache can grow to 2-5GB
- OmniParser GUI mode needs even more space

**What the Fixed Installer Does:**
1. Checks available disk space BEFORE installation
2. Shows you exactly how much space you have
3. Warns if space is low
4. Provides cleaning steps if needed
5. Uses TMPDIR to manage cache more efficiently

## Quick Start (Recommended)

The easiest and cleanest way is to use a **virtual environment**:

```bash
# Step 1: Create a virtual environment
python3 -m venv craftbot-env

# Step 2: Activate the environment
source craftbot-env/bin/activate

# Step 3: Run the installer
python install.py

# Step 4: Start CraftBot
python run.py
```

## Why Use a Virtual Environment?

- ✓ No system package conflicts
- ✓ No need for `--break-system-packages` flag
- ✓ Easily portable (can delete `craftbot-env` to uninstall)
- ✓ Best practice for Python projects
- ✓ Works on any Linux distribution

## Alternative Methods

### Option 2: Conda Environment (Recommended for GPU/ML Features)

If you have conda installed:

```bash
python install.py --conda
```

Conda is especially recommended if you plan to use the GUI mode (OmniParser):

```bash
python install.py --gui --conda
```

### Option 3: System-Wide Installation (Less Recommended)

The installer will automatically handle this if you run it directly:

```bash
python install.py
```

If you encounter the "externally-managed-environment" error, the installer will:
1. Show you the 3 options above
2. Automatically retry with `--break-system-packages` if you choose Option 3

This works but modifies system Python and is less clean than virtual environments.

## Disk Space Pre-Check (New Feature! 🎉)

### What the Installer Does Now

**Before Installation Starts:**
1. ✅ Checks available disk space automatically
2. ✅ Shows you total/used/free space
3. ✅ Warns if space is low (< 5GB for core, < 8GB for GUI)
4. ✅ Suggests cleanup steps
5. ✅ Lets you choose to continue or clean up first

**Example Output:**
```
============================================================
 📊 Disk Space Check
============================================================
Home directory: /home/user
Total space:   40.0 GB
Used space:    32.5 GB (81.3%)
Free space:    7.5 GB

⚠️  WARNING: Low disk space (7.5 GB free, need 8.0 GB)

Recommended fixes:

1. Clean up pip cache:
   pip cache purge

2. Clean up npm cache (if Node.js installed):
   npm cache clean --force

3. Remove old files/packages:
   rm -rf ~/.cache/*

4. Use a different disk with more space:
   mkdir -p /mnt/large-disk/pip-tmp
   TMPDIR=/mnt/large-disk/pip-tmp python install.py

5. Or continue anyway (may fail): y
```

### How to Respond

- **If space is OK**: Installation proceeds automatically
- **If space is low**: 
  - Choose `y` to continue anyway (may fail) → clean up if it fails
  - Choose `n` to cancel → free up space first

### Automatic TMPDIR Management

The installer automatically:
- Creates `~/pip-tmp` directory
- Uses it for pip cache management
- Prevents cache from filling your disk
- No extra steps needed from you!

## Handling Common Errors

### Error: "No space left on device" or "Disk Full"

**New in Fixed Installer:**
- Automatically detects this error
- Shows cleanup suggestions immediately
- No more cryptic error messages

**What to do:**

**Option 1: Free Up Space (Fastest)**
```bash
# Clear pip cache (usually frees 1-5 GB!)
pip cache purge

# Clear npm cache (if Node.js installed)
npm cache clean --force

# Clear system cache (be careful with sudo)
sudo apt-get clean        # Apt package cache
sudo apt-get autoclean    # Remove old package files
sudo apt-get autoremove   # Remove unused packages
```

Then retry:
```bash
python install.py
```

**Option 2: Use External/Larger Disk**

If you have more space on another disk:

```bash
# On Linux - mount point like /mnt, /media, or external drive
mkdir -p /mnt/external/pip-tmp
TMPDIR=/mnt/external/pip-tmp python install.py

# Or let installer prompt you during installation
```

**Option 3: Use Conda (More Efficient with Space)**

Conda is better at managing large package dependencies:

```bash
python install.py --conda
```

Conda usually handles space better than pip.

**Option 4: Expand VM Disk (If Using Virtual Machine)**

If on VMware/VirtualBox:
1. Shut down the VM
2. Expand the disk in VM settings
3. Resize the partition in Linux
4. Try installation again

**Check Your Disk Space:**

```bash
# See overall disk usage
df -h

# See detailed breakdown of home directory
du -sh ~/*

# See top space consumers
du -sh ~/* | sort -rh | head -10
```

### Error: "externally-managed-environment" or "externally managed"

**Solution:** Use a virtual environment (see Quick Start above) or conda.

### Error: PyTorch Installation Fails

Common on Kali. Fix:

```bash
# Option 1: Use CPU-only PyTorch
python install.py --gui --cpu-only

# Option 2: Use conda (more reliable)
python install.py --gui --conda

# Option 3: Clear pip cache first
pip cache purge
python install.py --gui
```

### Error: "No space left on device" or Pip Cache Issues

```bash
# Clear pip cache
pip cache purge

# Or use a different temporary directory with more space
mkdir -p ~/large-disk/pip-tmp
TMPDIR=~/large-disk/pip-tmp python install.py

# Check disk space
df -h
```

### Error: OmniParser/Torch Installation Fails

OmniParser (GUI mode) requires PyTorch. If it fails:

```bash
# Skip GUI mode for now
python install.py

# Try GUI mode later with conda
python install.py --gui --conda
```

Or just use TUI mode (doesn't need GUI components):

```bash
python run.py --tui
```

## Post-Installation

### Using the Virtual Environment

After you've installed with a virtual environment, **always activate it** before running CraftBot:

```bash
# Activate virtual environment
source craftbot-env/bin/activate

# Run CraftBot
python run.py
```

### Creating a Shortcut (Optional)

Create a script `craftbot.sh` in your home directory:

```bash
#!/bin/bash
cd /path/to/craftbot
source craftbot-env/bin/activate
python run.py
```

Then make it executable:

```bash
chmod +x ./craftbot.sh
./craftbot.sh  # Run it anytime
```

## Troubleshooting Checklist

- [ ] Python version is 3.10+: `python --version`
- [ ] Virtual environment activated: You should see `(craftbot-env)` in your terminal
- [ ] All dependencies installed: `pip list | grep torch` should show torch
- [ ] Can import modules: `python -c "import torch; print(torch.__version__)"`

## Getting More Help

1. **Check INSTALLATION_FIX.md** for general installation issues
2. **Run in verbose mode**: `pip install -v requirements.txt` (shows more details)
3. **GitHub Issues**: Report problems to the CraftBot repository
4. **Python/Pip Docs**: https://docs.python.org/3/

## Quick Commands Reference

```bash
# List all available installation options
python install.py --help

# Installation with virtual environment (recommended)
python3 -m venv craftbot-env
source craftbot-env/bin/activate
python install.py

# Installation with conda
python install.py --conda

# Installation with GUI (requires torch)
python install.py --gui

# GUI with CPU-only PyTorch
python install.py --gui --cpu-only

# Run browser interface (default)
python run.py

# Run terminal interface (no Node.js needed)
python run.py --tui

# Clear pip cache if disk is full
pip cache purge
```

## Notes for Kali Users

- Kali Linux comes with a system Python that's managed by PEP 668
- Virtual environments completely bypass this limitation
- Conda is also a good alternative, especially for data science projects
- GPU support (CUDA) may need additional configuration (see your GPU vendor)
- PyTorch `torch-cuda==12.1` might not work on older GPUs; use `--cpu-only` instead

---

**TL;DR:** Use a virtual environment, it's the cleanest solution:
```bash
python3 -m venv craftbot-env
source craftbot-env/bin/activate
python install.py
python run.py
```
