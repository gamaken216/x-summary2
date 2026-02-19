@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo   X List Auto-Summary System - Setup
echo ==================================================
echo.

:: 1. Python check
echo [1/3] Checking Python...

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Python not found.
    echo.
    echo    Please install Python 3.10 or later.
    echo    Opening download page now...
    echo.
    echo    *** IMPORTANT ***
    echo    Check "Add Python to PATH" during installation!
    echo.
    start https://www.python.org/downloads/
    echo    After installation, run this setup.bat again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo    [OK] Python %PYVER% found
echo.

:: 2. pip upgrade
echo [2/3] Updating pip...
python -m pip install --upgrade pip >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    [WARN] pip update failed, continuing...
) else (
    echo    [OK] pip updated
)
echo.

:: 3. Install libraries
echo [3/3] Installing libraries...
echo    This may take a few minutes on first run.
echo.

cd /d "%~dp0"

set FAIL=0

echo    - twikit ...
pip install twikit >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo      [FAIL] twikit
    set FAIL=1
) else (
    echo      [OK] twikit
)

echo    - google-genai ...
pip install google-genai >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo      [FAIL] google-genai
    set FAIL=1
) else (
    echo      [OK] google-genai
)

echo    - flask ...
pip install flask >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo      [FAIL] flask
    set FAIL=1
) else (
    echo      [OK] flask
)
echo.

:: Result
if %FAIL% EQU 1 (
    echo ==================================================
    echo [WARN] Some installations failed.
    echo    Try manually: pip install -r requirements.txt
    echo ==================================================
) else (
    echo ==================================================
    echo [OK] Setup complete!
    echo ==================================================
    echo.
    echo Next steps:
    echo   1. Double-click "settings.bat"
    echo   2. Enter settings in browser and save
    echo   3. Click "Test" to verify
    echo.
    echo See the Setup Guide in the settings page for details.
)

echo.
pause
