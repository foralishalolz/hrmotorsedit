@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto run_py
where python >nul 2>nul
if not errorlevel 1 goto run_python
echo Python 3.10 or newer is required. Install Python from https://www.python.org/downloads/
echo Enable Add Python to PATH during installation, then run this file again.
goto finish
:run_py
py -3 server.py --open
goto finish
:run_python
python server.py --open
:finish
pause
