@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
if not exist ".venv\Scripts\python.exe" (
 echo First run SETUP_WINDOWS.bat once.
 pause
 exit /b 1
)
echo Starting AgriVision at http://localhost:8000
echo Stop recording in the browser first. Then press Ctrl+C here to shut down.
".venv\Scripts\python.exe" scripts\run_local.py
if errorlevel 1 pause
