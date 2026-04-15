@echo off
REM Double-clickable shim for Windows Explorer. Locates a Python 3 interpreter
REM and forwards to launch.py, which handles the actual bootstrap (.venv,
REM pip install, launching the GUI). In VS Code you can just open launch.py
REM and click "Run Python File" — this shim exists because File Explorer
REM reliably double-clicks .bat files.

setlocal
cd /d "%~dp0"
set "PROJECT_DIR=%CD%"

echo.
echo === EMG launcher (Windows shim) ===
echo Project: %PROJECT_DIR%
echo.

set "PYTHON_BIN="

where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_BIN=py -3"
        goto :have_python
    )
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_BIN=python"
        goto :have_python
    )
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_BIN=python3"
        goto :have_python
    )
)

echo ERROR: Python 3 is not installed or not on PATH.
echo.
echo Install from https://www.python.org/downloads/
echo IMPORTANT: check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:have_python
echo Found Python:
%PYTHON_BIN% --version
echo.

%PYTHON_BIN% "%PROJECT_DIR%\launch.py"
set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo launch.py exited with code %EXIT_CODE%.
    pause
)

endlocal
exit /b %EXIT_CODE%
