@echo off
setlocal
cd /d "%~dp0"

echo =======================================================
echo Building galIMVmini Standalone Distribution
echo =======================================================

python build_exe.py %*

pause
