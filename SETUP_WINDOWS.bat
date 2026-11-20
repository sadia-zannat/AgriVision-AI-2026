@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
where py >nul 2>nul
if errorlevel 1 goto nopy
py -3.12 -c "import sys; assert sys.version_info[:2]==(3,12)" >nul 2>nul
if errorlevel 1 goto nopy
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist ".env" copy ".env.example" ".env" >nul
".venv\Scripts\python.exe" scripts\doctor.py
if errorlevel 1 goto fail
echo.
echo Setup complete. Run RUN_AGRIVISION_WINDOWS.bat. CPU mode works without CUDA.
echo Existing .env, models and evidence were preserved.
pause
exit /b 0
:nopy
echo Install Python 3.12 64-bit from python.org with the py launcher, then run again.
pause
exit /b 1
:fail
echo Setup failed. Read the error above. Check internet and free disk space, then retry.
pause
exit /b 1
