@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" exit /b 1
echo OPTIONAL: do not retrain immediately before your demonstration.
echo Original models\tomato_best.pt is never overwritten.
".venv\Scripts\python.exe" -m pip install -r requirements-training.txt
if errorlevel 1 goto fail
".venv\Scripts\python.exe" scripts\prepare_tomato_10class.py --download-hf
if errorlevel 1 goto fail
".venv\Scripts\python.exe" scripts\train_tomato_10class.py
if errorlevel 1 goto fail
echo Validation complete. Freeze choices before running the final test once; see README_BN.md.
pause
exit /b 0
:fail
echo Stopped safely. Existing data is not deleted. Read README_BN.md to reuse your existing cached or exported data.
pause
exit /b 1
