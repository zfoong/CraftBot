@echo off
REM ======================================
REM CraftBot - Automatic Setup
REM ======================================
REM This script sets up everything automatically
REM No prompts, no questions - just works!

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  CraftBot Automatic Installation Setup
echo ============================================================
echo.

REM Step 1: Check if Miniconda is already installed
echo Checking for Miniconda...
where conda >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Miniconda found in PATH
    call conda --version
    goto conda_found
)

echo [SEARCHING] Miniconda not in PATH, searching common locations...

REM Check common installation paths
set conda_found=0
if exist "C:\miniconda3\condabin\conda.bat" set conda_found=1 & set conda_path=C:\miniconda3
if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" set conda_found=1 & set conda_path=%USERPROFILE%\miniconda3

if !conda_found! EQU 1 (
    echo [OK] Found at: !conda_path!
    call !conda_path!\condabin\conda.bat --version
    REM Add to PATH temporarily
    set "PATH=!conda_path!\condabin;!PATH!"
    goto conda_found
)

REM Step 2: Install Miniconda if not found
echo [INSTALLING] Miniconda not found - downloading and installing...
echo.

REM Download location
set download_dir=%USERPROFILE%\Downloads
set installer=%download_dir%\Miniconda3-latest-Windows-x86_64.exe
set install_dir=C:\miniconda3

if not exist "%download_dir%" mkdir "%download_dir%"

echo Downloading Miniconda (this may take 1-2 minutes)...
powershell -Command "& { [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe', '%installer%') }"

if not exist "%installer%" (
    echo [ERROR] Failed to download Miniconda
    echo Please install manually from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo.
echo Installing Miniconda to %install_dir% ...
echo (This will take 2-3 minutes, please wait...)
"%installer%" /InstallationType=JustMe /AddMinicondaToPath=Yes /D=%install_dir%

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Miniconda installation failed
    echo Please try installing manually from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo.
echo [OK] Miniconda installed successfully!
set "PATH=%install_dir%\condabin;%PATH%"

:conda_found
echo.
echo ============================================================
echo  Checking Python environment...
echo ============================================================
echo.

REM Run the Python auto_setup
python auto_setup.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python setup failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Run: python install.py --conda
echo   2. Wait for installation to complete (5-10 minutes)
echo   3. Run: python run.py
echo.
echo Opening... (press any key to continue)
pause

exit /b 0
