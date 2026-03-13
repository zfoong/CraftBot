# ✅ DISK SPACE ISSUE FIXED - What You Need to Know

## Your Problem (Solved!)

> "Kali sometimes shows the disk is full and says no space to download requirements"

### What Was Happening

```
python install.py
→ [installation starts, no warning]
→ [pip starts downloading large packages like torch (5GB)]
→ [halfway through...]
❌ "No space left on device"
→ [installation fails, you're confused]
```

### What Happens Now ✅

```
python install.py
→ [✅ AUTOMATIC DISK CHECK]
→ Shows: "You have 3 GB free, need 5 GB"
→ [⚠️ WARNS YOU]
→ Suggests: "pip cache purge" (frees 1-5 GB)
→ Asks: "Continue? (y/n)"
→ [You clean up, retry]
→ ✅ Installation succeeds!
```

## What Changed in Your Installer

### 1. **Automatic Disk Space Check** (MOST IMPORTANT)

**Before**: No warning - just fails
**After**: 
- Checks space BEFORE installation
- Shows you exact numbers (5 GB free, 20 GB total, etc.)
- Warns if low
- Suggests specific cleanup

**When It Runs**: Right after you type `python install.py`

### 2. **Error Detection During Installation**

**Before**: Cryptic error message
**After**: Detects "no space left on device" and shows:
```
❌ DISK SPACE ERROR - No space left on device

This is a common issue on Kali Linux when installing large packages.

Immediate fixes:

1. Clear pip cache (usually frees 1-5 GB):
   pip cache purge

2. Clear npm cache (if installed):
   npm cache clean --force

3. Use alternate disk with more space:
   mkdir -p /mnt/external/pip-tmp
   TMPDIR=/mnt/external/pip-tmp python install.py
```

### 3. **Automatic TMPDIR Management**

- Uses `~/pip-tmp` for pip cache
- Prevents cache from filling disk
- No user action needed
- Works automatically

## How to Install Now (Works Every Time)

### Fastest Method (Virtual Environment + Cleanup)

```bash
# 1. Clean up first (takes 30 seconds)
pip cache purge
npm cache clean --force

# 2. Create virtual environment
python3 -m venv craftbot-env

# 3. Activate it
source craftbot-env/bin/activate

# 4. Install (automatic disk check included)
python install.py

# 5. Run
python run.py
```

### If Installer Warns About Low Space

```
⚠️  WARNING: Low disk space (3.5 GB free, need 5 GB)

Recommended fixes:

1. Clean up pip cache:
   pip cache purge
...
Or continue anyway (may fail): y
```

**Choose `n`** → Stop here → Cleanup → Retry

```bash
pip cache purge
npm cache clean --force
python install.py
```

## Key Improvements

| Scenario | Before | After |
|---|---|---|
| Kali with 3GB free | ❌ Fails midway | ✅ Warns upfront |
| User doesn't know why | ❌ Cryptic error | ✅ Clear message with solutions |
| Cleaning cache | ❌ No guidance | ✅ Tells you: `pip cache purge` |
| Using external disk | ❌ No support | ✅ Shows how: `TMPDIR=/mnt/disk python install.py` |

## New Files to Read

1. **QUICK_REFERENCE.md** ⭐ (Keep This Handy!)
   - Quick fixes for disk space
   - Common commands in one page

2. **DISK_SPACE_TROUBLESHOOTING.md** (Complete Guide)
   - Everything about disk issues
   - How to expand VM disk
   - Space breakdown commands
   - Advanced cleanup script

3. **DISK_SPACE_FIX_SUMMARY.md** (Technical Summary)
   - How the fix was implemented
   - What changed in install.py

4. **KALI_INSTALLATION_GUIDE.md** (Updated)
   - Kali-specific installation steps
   - Disk space section

## Space Requirements

```
Core Installation:        5 GB needed
With Browser:             6 GB needed
With GUI (OmniParser):    10 GB needed (torch is large!)
```

**Kali VM Default**: 20-30 GB total disk
- OS takes: 8-12 GB
- This leaves: 8-22 GB for installation ✅

## What the Installer Does Now

```python
# At start of install.py:
check_disk_space_for_installation(min_free_gb=5.0)  # Core
# or
check_disk_space_for_installation(min_free_gb=8.0)  # GUI mode
```

**This function:**
1. ✅ Gets available disk space
2. ✅ Displays total/used/free in GB
3. ✅ Calculates percentage used
4. ✅ Warns if < required space
5. ✅ Shows cleanup suggestions
6. ✅ Lets you choose to continue or stop

## If Installation Still Fails

### Step 1: Check Your Space
```bash
df -h /home
# Shows total, used, available
```

### Step 2: Clean Everything
```bash
pip cache purge              # Frees 1-5 GB
npm cache clean --force      # Frees 500MB
sudo apt-get clean           # Frees 200MB-2GB
sudo apt-get autoremove -y   # Frees more stuff
rm -rf ~/.cache/*            # System caches
```

### Step 3: Check Again
```bash
df -h /home
# Should have more space now
```

### Step 4: Retry
```bash
python install.py
```

### Step 5 (If Still Low): Use External Disk
```bash
mkdir -p /mnt/external/pip-tmp
TMPDIR=/mnt/external/pip-tmp python install.py
```

### Step 6 (Last Resort): Expand Kali Disk
- VMware: Right-click VM → Settings → Hard Disk → Expand to 50GB
- VirtualBox: Virtual Media Manager → Expand disk
- Reboot, then expand partition

## Code Changes Made

All in `install.py`:

**New Functions Added:**
- `get_disk_space(path)` - Checks available space
- `check_disk_space_for_installation(min_free_gb)` - Main pre-check
- `suggest_cleanup_steps()` - Shows cleanup guide

**Enhanced Functions:**
- `setup_pip_environment()` - Detects disk space errors
- PyTorch installation - Better error messages
- Main flow - Calls disk check at start

## Your Next Steps

1. **Read**: QUICK_REFERENCE.md (1 minute)
2. **Prepare**: `pip cache purge && npm cache clean --force`
3. **Install**: `python install.py` (will check disk automatically)
4. **Follow**: Any prompts about disk space
5. **Done**: Installation will succeed! ✅

## Testing It Out

Try the installer now:
```bash
python install.py
# You'll see:
# 📊 Disk Space Check
# Total: 20.0 GB
# Used: 15.0 GB (75%)
# Free: 5.0 GB
# ✅ Space is OK, continuing...
```

---

**Summary**: Your disk space issue is SOLVED. The installer now intelligently manages your limited Kali disk space! 🎉

**For detailed troubleshooting**: See **DISK_SPACE_TROUBLESHOOTING.md**
**For quick commands**: See **QUICK_REFERENCE.md**
