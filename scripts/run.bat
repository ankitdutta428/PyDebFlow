@echo off
REM =============================================================================
REM run.bat - PyDebFlow Runner Script for Windows
REM =============================================================================
REM Quick launcher for simulations with common presets.
REM
REM Usage:
REM   scripts\run.bat --synthetic-test
REM   scripts\run.bat --dem terrain.tif
REM   scripts\run.bat --gui
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

REM Parse arguments
if "%~1"=="" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="--gui" goto :run_gui
if "%~1"=="--synthetic-test" goto :run_synthetic
if "%~1"=="--dem" goto :run_dem

REM Pass all arguments to run_simulation.py
python run_simulation.py %*
goto :eof

:show_help
echo PyDebFlow - Mass Flow Simulation Tool
echo.
echo Usage: scripts\run.bat [OPTIONS]
echo.
echo Quick Commands:
echo   --synthetic-test    Run quick demo with synthetic terrain
echo   --gui               Launch the graphical interface
echo   --dem FILE          Run simulation on a DEM file
echo   --help              Show this help message
echo.
echo Examples:
echo   scripts\run.bat --synthetic-test
echo   scripts\run.bat --dem samples\sample_dem.asc --t-end 60 --animate-3d
echo   scripts\run.bat --gui
echo.
echo All other arguments are passed to run_simulation.py
goto :eof

:run_gui
echo Launching PyDebFlow GUI...
python main.py
goto :eof

:run_synthetic
echo Running synthetic test simulation...
set ARGS=%*
set ARGS=!ARGS:--synthetic-test=!
python run_simulation.py --synthetic-test !ARGS!
goto :eof

:run_dem
if "%~2"=="" (
    echo Error: --dem requires a file path
    exit /b 1
)
echo Running DEM simulation: %~2
set ARGS=%*
set ARGS=!ARGS:--dem=--dem-file!
python run_simulation.py !ARGS!
goto :eof

endlocal
