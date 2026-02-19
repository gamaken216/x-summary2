@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo   X List Auto-Summary System - Uninstall
echo ==================================================
echo.
echo This will:
echo   1. Remove pip libraries (twikit, google-genai, flask)
echo   2. Remove Task Scheduler entry
echo   3. Guide folder deletion
echo.
choice /c YN /m "Continue? [Y] Yes  [N] No"
if %ERRORLEVEL% EQU 2 (
    echo.
    echo Uninstall cancelled.
    pause
    exit /b 0
)
echo.

:: 1. pip uninstall
echo [1/3] Removing libraries...
pip uninstall twikit -y >nul 2>&1
if %ERRORLEVEL% EQU 0 (echo    [OK] twikit removed) else (echo    [--] twikit not installed)
pip uninstall google-genai -y >nul 2>&1
if %ERRORLEVEL% EQU 0 (echo    [OK] google-genai removed) else (echo    [--] google-genai not installed)
pip uninstall flask -y >nul 2>&1
if %ERRORLEVEL% EQU 0 (echo    [OK] flask removed) else (echo    [--] flask not installed)
echo.

:: 2. Task Scheduler
echo [2/3] Checking Task Scheduler...
schtasks /Query /TN "X-AutoSummary" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    Task "X-AutoSummary" found. Removing...
    schtasks /Delete /TN "X-AutoSummary" /F >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    [OK] Task removed
    ) else (
        echo    [WARN] Could not remove automatically.
        echo           Please remove it manually in Task Scheduler.
    )
) else (
    echo    [--] No task found in Task Scheduler
)
echo.

:: 3. Folder
echo [3/3] Folder deletion...
echo    Delete this folder to complete uninstall:
echo    %~dp0
echo.
choice /c YN /m "   [Y] Delete folder now  [N] Delete manually later"
if %ERRORLEVEL% EQU 1 (
    echo.
    echo ==================================================
    echo [OK] Uninstall complete!
    echo    Folder will be deleted in a few seconds.
    echo ==================================================
    echo.
    pause
    start /b cmd /c "timeout /t 2 /nobreak >nul & rd /s /q "%~dp0""
    exit /b 0
) else (
    echo.
    echo ==================================================
    echo [OK] Libraries and task removed.
    echo    Please delete the folder manually:
    echo    %~dp0
    echo ==================================================
    echo.
    pause
    exit /b 0
)
