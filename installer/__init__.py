"""Installer-only modules used by craftbot.py.

Split out of the root namespace so the project root only contains the
user-facing entry points (`craftbot.py`, `run.py`, `main.py`). Everything
in here is implementation detail of the installer/wizard flow:

  - helpers: detached-Popen flag soup + per-platform dispatcher
  - metadata: JSON read/write for install.json
  - payload: agent zip download + extract
  - wizard: Tkinter UI launched when CraftBotInstaller.exe is double-clicked
"""
