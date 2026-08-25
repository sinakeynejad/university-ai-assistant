@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set BACKEND_DIR=backend
set VENV_DIR=%BACKEND_DIR%\venv

echo [1/4] Setting up backend with Python 3.12...

:: Try to locate Python 3.12
set PYTHON_CMD=
where py >nul 2>nul
if %errorlevel%==0 (
    for /f "delims=" %%i in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set PYTHON_CMD=%%i
)
if not defined PYTHON_CMD (
    echo WARNING: Python 3.12 not found via py -3.12, falling back to 'python'.
    set PYTHON_CMD=python
)

echo Using Python: %PYTHON_CMD%

:: Create venv if missing
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment with Python 3.12...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

:: Always install requirements
echo Installing backend requirements...
call "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
call "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
    echo ERROR: Failed to install requirements. Check requirements.txt.
    pause
    exit /b 1
)

:: Copy .env if missing
if not exist "%BACKEND_DIR%\.env" (
    echo Copying .env.example to .env...
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env"
)

:: Start servers
echo [2/4] Starting backend server...
start "Backend Server" /D "%BACKEND_DIR%" "%VENV_DIR%\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000

echo [3/4] Starting frontend server...
start "Frontend Server" python -m http.server 5500 --directory frontend

echo [4/4] Done.
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5500
pause