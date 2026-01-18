@echo off
REM =============================================================================
REM test.bat - PyDebFlow Test Runner Script for Windows
REM =============================================================================
REM Runs all tests or specific test modules.
REM
REM Usage:
REM   scripts\test.bat              # Run all tests
REM   scripts\test.bat --coverage   # Run with coverage report
REM   scripts\test.bat --unit       # Run unit tests only
REM   scripts\test.bat --module rheology  # Run specific module test
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
echo                PyDebFlow - Test Runner
echo ========================================================================
echo.

if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="--coverage" goto :run_coverage
if "%~1"=="-c" goto :run_coverage
if "%~1"=="--component" goto :run_component
if "%~1"=="--module" goto :run_module
if "%~1"=="--unit" goto :run_unit

REM Default: run all pytest tests
goto :run_all

:show_help
echo Usage: scripts\test.bat [OPTIONS]
echo.
echo Options:
echo   --all, -a          Run all tests (default)
echo   --unit             Run pytest unit tests only
echo   --component        Run built-in component tests
echo   --coverage, -c     Run with coverage report
echo   --module NAME      Run specific test module (rheology, solver, integration)
echo   --help, -h         Show this help message
echo.
echo Examples:
echo   scripts\test.bat
echo   scripts\test.bat --coverage
echo   scripts\test.bat --module rheology
echo   scripts\test.bat --component
goto :eof

:run_all
echo [INFO] Running all pytest tests...
echo.
python -m pytest tests/ -v
echo.
echo [SUCCESS] All tests completed!
goto :eof

:run_unit
echo [INFO] Running pytest unit tests...
echo.
python -m pytest tests/ -v
echo.
echo [SUCCESS] Unit tests completed!
goto :eof

:run_coverage
echo [INFO] Running tests with coverage...
echo.
python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term
echo.
echo [INFO] Coverage report generated: htmlcov\index.html
echo [SUCCESS] Tests with coverage completed!
goto :eof

:run_component
echo [INFO] Running built-in component tests...
echo.
python run_simulation.py --test-all
echo.
echo [SUCCESS] Component tests completed!
goto :eof

:run_module
if "%~2"=="" (
    echo [ERROR] --module requires a module name
    echo Usage: scripts\test.bat --module rheology
    exit /b 1
)
echo [INFO] Running tests for module: %~2
echo.
python -m pytest tests/test_%~2.py -v
echo.
echo [SUCCESS] Module tests completed!
goto :eof

endlocal
