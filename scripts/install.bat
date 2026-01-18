@echo off
REM =============================================================================
REM install.bat - PyDebFlow Installation Script for Windows
REM =============================================================================
REM This script creates a virtual environment and installs all dependencies.
REM
REM Usage:
REM   scripts\install.bat
REM =============================================================================

setlocal enabledelayedexpansion

echo ========================================================================
echo            PyDebFlow - Installation Script (Windows)
echo ========================================================================
echo.

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

echo [INFO] Project root: %CD%
echo.

REM Check Python version
echo [1/4] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10, 3.11, or 3.12
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       Found: Python %PYTHON_VERSION%

python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.10 or higher is required
    exit /b 1
)
echo       [OK] Python version is compatible
echo.

REM Create virtual environment
echo [2/4] Creating virtual environment...
set "VENV_DIR=%PROJECT_ROOT%\venv"

if exist "%VENV_DIR%" (
    echo       Virtual environment already exists at %VENV_DIR%
    set /p RECREATE="       Do you want to recreate it? (y/N): "
    if /i "!RECREATE!"=="y" (
        rmdir /s /q "%VENV_DIR%"
        python -m venv "%VENV_DIR%"
        echo       [OK] Virtual environment recreated
    ) else (
        echo       Using existing virtual environment
    )
) else (
    python -m venv "%VENV_DIR%"
    echo       [OK] Virtual environment created
)
echo.

REM Activate virtual environment
echo [3/4] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
echo       [OK] Virtual environment activated
echo.

REM Upgrade pip
pip install --upgrade pip --quiet

REM Install dependencies
echo [4/4] Installing dependencies...
if exist "%PROJECT_ROOT%\requirements.txt" (
    pip install -r "%PROJECT_ROOT%\requirements.txt"
    echo       [OK] Dependencies installed
) else (
    echo       [ERROR] requirements.txt not found
    exit /b 1
)
echo.

REM Verify installation
echo ========================================================================
echo [SUCCESS] Installation complete!
echo ========================================================================
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate
echo.
echo To run PyDebFlow:
echo   scripts\run.bat --synthetic-test
echo   python main.py  (for GUI)
echo.
echo To run tests:
echo   scripts\test.bat
echo.

endlocal
