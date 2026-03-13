# Disk Space Troubleshooting for Kali Linux 🛑

## The Problem

Installing CraftBot on Kali Linux fails with:
```
❌ DISK SPACE ERROR - No space left on device
error: No space left on device
pip._internal.utils.packaging.get_file_hash: No space left on device
```

**Why It Happens:**
1. Kali VMs often come with limited disk (20-30 GB)
2. Base system takes 8-12 GB
3. PyTorch alone is 5+ GB
4. pip cache grows quickly (1-5 GB)
5. Installation leaves little room for the actual packages

## Quick Fixes (Try These First)

### Fix 1: Clear Pip Cache (Fastest - Frees 1-5 GB) ⚡

```bash
pip cache purge
```

Then retry:
```bash
python install.py
```

**Time**: 30 seconds
**Space freed**: 1-5 GB
**Success rate**: 90%

### Fix 2: Clear npm Cache (If Node.js Installed)

```bash
npm cache clean --force
```

**Space freed**: 100-500 MB

### Fix 3: Clean System Packages

```bash
# Remove old apt packages
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y
```

**Space freed**: 200 MB - 2 GB

Combined with Fix 1, this often frees 3-5 GB.

### Fix 4: Check and Clear Large Cache Directories

```bash
# Show biggest directories in home
du -sh ~/* | sort -rh | head -10

# Clear cache directories safely
rm -rf ~/.cache/*
rm -rf ~/.local/share/cache/*
```

**Space freed**: 500 MB - 3 GB (varies)

## If You Still Don't Have Enough Space

### Solution A: Expand Your Disk (If VM)

**For VMware:**
1. Power off VM
2. Right-click VM → Settings
3. Click Hard Disk → Expand
4. Add more GB (e.g., change 20GB to 40GB)
5. Boot up and resize partition

**For VirtualBox:**
1. Power off VM
2. File → Virtual Media Manager
3. Right-click disk → Properties
4. Expand size
5. Boot and resize partition

**For Physical Machine:**
Install a larger SSD or expand partition with GParted.

### Solution B: Use External Drive/Large Partition

If you have another disk with more space:

```bash
# Create temp directories on external disk
mkdir -p /mnt/external/pip-tmp
mkdir -p /mnt/external/npm-cache

# Install CraftBot using the external disk
TMPDIR=/mnt/external/pip-tmp npm_config_cache=/mnt/external/npm-cache python install.py
```

### Solution C: Use Conda (More Space-Efficient)

Conda handles large packages better than pip:

```bash
python install.py --conda
```

Conda pre-downloads to a cache but manages it better.

### Solution D: CPU-Only Mode (Smaller Requirements)

If you're not using GUI mode, skip the large torch package:

```bash
python install.py
```

This avoids the `--gui` flag which adds PyTorch (~5GB).

### Solution E: Skip Browser Mode

TUI mode doesn't need npm:

```bash
python install.py
python run.py --tui
```

This avoids Node.js and npm, but gives non-browser interface.

## Space Requirements

| Installation Type | Minimum Space | Recommended |
|---|---|---|
| Core only | 3 GB | 5 GB |
| Core + Browser | 4 GB | 6 GB |
| Full + GUI | 6 GB | 10 GB |
| Core + Conda | 5 GB | 8 GB |

## Understanding Your Disk Usage

### Check Available Space

```bash
# Simple overview
df -h /home

# Detailed view including system
df -h

# Size of home directory
du -sh ~

# Breakdown by subdirectory
du -sh ~/* | sort -rh
```

### Common Large Directories on Kali

```bash
# pip cache
~/.cache/pip/       # Can be 1-5 GB

# npm cache  
~/.npm/             # Can be 500 MB - 1 GB

# venv/conda
~/.*env/            # Virtual environments (1-2 GB each)

# Package manager cache
/var/cache/apt/     # Apt packages cache (500 MB - 2 GB)

# Snap cache (if installed)
/var/lib/snapd/     # Can be very large

# Docker images (if installed)
/var/lib/docker/    # Can be many GB
```

## The New Automatic Fix 🎉

**CraftBot Installer Now:**
1. ✅ Checks your disk space before installing
2. ✅ Shows you exactly how much space you have
3. ✅ Warns if space is critically low
4. ✅ Suggests cleanup if needed
5. ✅ Uses TMPDIR to manage cache

**You'll see:**
```
============================================================
 📊 Disk Space Check
============================================================
Home directory: /home/user
Total space:   20.0 GB
Used space:    18.5 GB (92.5%)
Free space:    1.5 GB

⚠️  WARNING: Low disk space (1.5 GB free, need 5.0 GB)

Recommended fixes:

1. Clean up pip cache:
   pip cache purge

2. Clear npm cache (if Node.js installed):
   npm cache clean --force

... [more options] ...

5. Or continue anyway (may fail): n
```

**Choose:**
- `y` to continue (will likely fail)
- `n` to stop and clean up first

## Full Cleanup Procedure

If you're really stuck, here's the advanced cleanup:

```bash
#!/bin/bash
# Safe cleanup script (use with caution!)

echo "🧹 Cleaning up space..."

# 1. Clear pip cache
echo "Clearing pip cache..."
pip cache purge

# 2. Clear npm cache
echo "Clearing npm cache..."
npm cache clean --force 2>/dev/null || true

# 3. APT cleanup
echo "Cleaning APT cache..."
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y

# 4. User cache
echo "Cleaning user cache..."
rm -rf ~/.cache/*
rm -rf ~/.local/share/cache/*

# 5. Temporary files
echo "Cleaning temp files..."
rm -rf ~/.tmp/*
rm -rf /tmp/* 2>/dev/null || sudo rm -rf /tmp/*

# 6. Check results
echo "✅ Cleanup complete. Space freed:"
df -h /home
```

Save this as `cleanup.sh` and run:
```bash
chmod +x cleanup.sh
./cleanup.sh
```

## Advanced: Manual Installation with Space Management

If you want maximum control:

```bash
# 1. Clear everything first
pip cache purge
npm cache clean --force
sudo apt-get clean

# 2. Create separate tmp directory
mkdir -p ~/disk-tmp
export TMPDIR=~/disk-tmp

# 3. Install in smaller steps
pip install requests pyyaml loguru nest-asyncio pymongo
# ... install other packages in groups

# 4. Or use conda (single step, better management)
python install.py --conda
```

## Permanent Solutions

For future installations:

1. **Expand Kali VM disk** to 50+ GB
2. **Use conda** instead of pip
3. **Install on external SSD** with more space
4. **Create dedicated large partition** for Python packages
5. **Use container** (Docker) with pre-built image

## Still Stuck?

If none of this works:

1. Check actual VS VM limitations
2. Try completely fresh Kali install with larger disk
3. Use cloud VM (AWS, Google Cloud) with more space
4. Use Docker container with pre-built image
5. Report detailed issue with output of:
   ```bash
   df -h
   pip cache info
   python --version
   ```

---

**Remember:** The new installer will catch disk space issues and guide you through fixes. No more mysterious errors! 🎉
