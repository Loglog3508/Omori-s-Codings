@echo off
chcp 65001 >nul
echo Starting DeepVision Local Server...

REM Try python command
python --version >nul 2>&1
if %errorlevel% equ 0 (
    cd /d "%~dp0"
    python start_server.py
    goto end
)

REM Try E:\python
if exist "E:\python\python.exe" (
    cd /d "%~dp0"
    "E:\python\python.exe" start_server.py
    goto end
)

echo Error: Python not found.
echo Please install Python and add it to PATH.
echo Or update the Python path in this script.

:end
pause
