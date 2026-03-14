@echo off
REM CraftBot launcher - suppresses warnings and runs cleanly
setlocal enabledelayedexpansion

REM Set Python to ignore warnings
set PYTHONWARNINGS=ignore

REM Run conda with craftbot environment
C:\Users\ganiy\miniconda3\Scripts\conda.exe run -n craftbot python run.py %*

endlocal
