@echo off
REM =============================================================================
REM build.bat - PyDebFlow Build Script for Windows
REM =============================================================================
REM Builds a standalone executable using PyInstaller.
REM
REM Usage:
REM   scripts\build.bat
REM   scripts\build.bat --clean
REM =============================================================================

setlocal enabledelayedexpansion

REM Get project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

REM Activate virtual environment if it exists
if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
)

echo ========================================================================
echo               PyDebFlow - Build Script (Windows)
echo ========================================================================
echo.

if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="--clean" goto :clean

goto :build

:show_help
echo Usage: scripts\build.bat [OPTIONS]
echo.
echo Options:
echo   --clean         Clean build artifacts before building
echo   --help, -h      Show this help message
echo.
echo Output will be in: dist\
goto :eof

:clean
echo [INFO] Cleaning build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"
echo       [OK] Clean complete
echo.
if "%~2"=="" goto :eof

:build
echo [1/3] Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo       Installing PyInstaller...
    pip install pyinstaller
)
echo       [OK] PyInstaller ready
echo.

echo [2/3] Building executable...
if exist "build_script.py" (
    python build_script.py
) else (
    python -m PyInstaller --name=PyDebFlow --onefile ^
        --add-data "src;src" ^
        --hidden-import=numpy ^
        --hidden-import=PyQt6 ^
        --hidden-import=pyvista ^
        main.py
)
echo.

echo [3/3] Build complete!
echo.
echo ========================================================================
echo [SUCCESS] Build successful!
echo ========================================================================
echo.
echo Output location:
echo   dist\PyDebFlow.exe
echo.

endlocal
