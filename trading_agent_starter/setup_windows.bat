@echo off
setlocal
cd /d "%~dp0"
py -3.13 --version >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.13 x64 from python.org with the Python launcher.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe py -3.13 -m venv .venv
if errorlevel 1 exit /b 1
if not exist config\ibkr.local.json copy config\ibkr.example.json config\ibkr.local.json >nul
.venv\Scripts\python.exe -m unittest discover -s tests -v
if errorlevel 1 (
  pause
  exit /b 1
)
echo Setup complete. Offline demo requires no packages or broker account.
pause
