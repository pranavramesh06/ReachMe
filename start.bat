@echo off
echo Starting ReachMe Healthcare Platform...
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" run.py
) else if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe" (
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe" run.py
) else (
    python run.py
)
pause
