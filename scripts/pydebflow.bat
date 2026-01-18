@echo off
REM =============================================================================
REM pydebflow.bat - CLI Wrapper for Windows
REM =============================================================================
REM Add this script's directory to PATH for global access.
REM
REM Usage:
REM   pydebflow simulate --synthetic
REM   pydebflow gui
REM   pydebflow info
REM =============================================================================

setlocal

REM Get project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Activate venv if exists
if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
)

REM Run the CLI
cd /d "%PROJECT_ROOT%"
python pydebflow.py %*

endlocal
