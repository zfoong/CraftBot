# Quick Reference - Kali Disk Space Installation Guide

## If You Get "No Space Left on Device" Error

### Quickest Fix (30 seconds)
```bash
pip cache purge
python install.py
```

### Complete Cleanup (5 minutes)
```bash
pip cache purge
npm cache clean --force
sudo apt-get clean
python install.py
```

### Check Your Disk Space
```bash
df -h /home          # Overall space
du -sh ~/*           # What's taking space
```

## Installation with Virtual Environment (RECOMMENDED)

```bash
python3 -m venv craftbot-env
source craftbot-env/bin/activate
python install.py
python run.py
```

## Installation with Conda (Better Space Management)

```bash
python install.py --conda
python run.py
```

## If Virtual Disk is Full

### Option 1: Expand VM Disk
- VMware: Right-click VM → Settings → Hard Disk → Expand to 50GB
- VirtualBox: Virtual Media Manager → Expand to 50GB
- Reboot and expand partition after expanding disk size

### Option 2: Use External USB Drive
```bash
# Mount external disk first, then:
mkdir -p /mnt/external/pip-tmp
TMPDIR=/mnt/external/pip-tmp python install.py
```

### Option 3: Use Different Partition
```bash
mkdir -p /var/larger-partition/pip-tmp
TMPDIR=/var/larger-partition/pip-tmp python install.py
```

## Minimum Space Requirements

| Mode | Space Needed |
|---|---|
| Core only | 5 GB |
| Core + Browser | 6 GB |
| Full + GUI | 10 GB |

## What Installer Does Now

✅ Checks disk space BEFORE installing
✅ Warns if space is low
✅ Suggests cleanup if needed
✅ Detects "no space" errors during installation
✅ Shows specific solutions

## Cleanup Commands Explained

| Command | Frees | Time |
|---|---|---|
| `pip cache purge` | 1-5 GB | 5s |
| `npm cache clean --force` | 500MB | 2s |
| `sudo apt-get clean` | 200MB-2GB | 10s |
| `sudo apt-get autoremove` | 100MB-500MB | 20s |

## Documentation Files for YOUR Issue

- **DISK_SPACE_TROUBLESHOOTING.md** ← Read this!
  - Full troubleshooting guide
  - Space breakdown commands
  - How to expand disk
  - Advanced cleanup script

- **KALI_INSTALLATION_GUIDE.md**
  - Step-by-step for Kali
  - Multiple installation methods
  - Error handling

- **DISK_SPACE_FIX_SUMMARY.md**
  - Complete summary of the fix

## Installer Workflow

```
1. Run: python install.py
   ↓
2. Installer checks disk space automatically
   ↓
3a. Space OK? → Continue installation ✅
3b. Space low? → Show warning & cleanup options
   ↓
4. If you choose to continue anyway:
   → Installation proceeds
   → If fails with "no space", shows specific fixes
```

## Most Common Solutions (In Order)

1. **`pip cache purge`** - Fixes most issues (1-5 GB freed)
2. **`npm cache clean --force`** - Second step (500MB freed)
3. **`python install.py --conda`** - Better at managing space
4. **Expand VM disk** - If VM and persistent issue
5. **Use external USB drive** - If can't expand disk

## Example Session

```bash
# 1. Get disk info
df -h /home
# Shows: 2 GB free (DANGER! Too low)

# 2. Clean up
pip cache purge
# Frees 3 GB

# 3. Check again
df -h /home
# Shows: 5 GB free (OK! Can install)

# 4. Install
python install.py
# ✅ Success!
```

## Red Flags & Solutions

| Error | Solution |
|---|---|
| `No space left on device` | `pip cache purge` + `npm cache clean --force` |
| Installation hangs | Kill (Ctrl+C) → cleanup → retry |
| "externally-managed-environment" | Use venv: `python3 -m venv env` |
| PyTorch fails | `python install.py --gui --cpu-only` or `python install.py --gui --conda` |
| VM keeps filling up | Expand disk: 20GB → 50GB+ |

## Keep This Handy!

Save these commands:
```bash
# Quick cleanup
pip cache purge && npm cache clean --force && sudo apt-get clean

# Check space
df -h /home && echo "---" && du -sh ~/* | sort -rh | head -5

# Safe install
python3 -m venv craftbot-env && source craftbot-env/bin/activate && python install.py
```

---

**Status**: ✅ Fixed - Installer now handles disk space intelligently
**For more details**: See DISK_SPACE_TROUBLESHOOTING.md
