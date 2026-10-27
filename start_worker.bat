@echo off
<<<<<<< HEAD
setlocal
cd /d "%~dp0"

echo ========================================
echo LM Studio Agent - Scheduled Worker
echo Project: %CD%
echo ========================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment was not found: .venv\Scripts\python.exe
    echo Create it and install dependencies first:
    echo   py -3.11 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install --upgrade pip
    echo   .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    pause
    exit /b 1
)

if not exist ".env" (
    echo [WARNING] .env was not found. Copy .env.example to .env and configure providers as needed.
)

echo [INFO] Starting the scheduled worker. Keep this window open while scheduled tasks should run.
".venv\Scripts\python.exe" -u worker.py
set "APP_EXIT_CODE=%ERRORLEVEL%"
if not "%APP_EXIT_CODE%"=="0" (
    echo [ERROR] The scheduled worker exited with code %APP_EXIT_CODE%.
    echo Review the error output above and check README.md / docs/installation.md.
) else (
    echo [INFO] The scheduled worker process has stopped.
)
pause
exit /b %APP_EXIT_CODE%
=======
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing virtual environment. See README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" worker.py
pause
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
