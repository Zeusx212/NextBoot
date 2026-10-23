@echo off
setlocal EnableDelayedExpansion
title NextBoot - OS Switcher
cd /d "%~dp0"

:: 1. Check if python path was passed via parameter
if "%~1"=="--python-path" (
    set "PYTHON_EXE=%~2"
    shift
    shift
)

:: 2. Check if cached in python_path.cfg
if not defined PYTHON_EXE (
    if exist "%~dp0python_path.cfg" (
        set /p CFG_PATH=<"%~dp0python_path.cfg"
        if exist "!CFG_PATH!" set "PYTHON_EXE=!CFG_PATH!"
    )
)

:: 3. Look up python via 'where python' (ignoring WindowsApps dummy stubs)
if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where python 2^>nul') do (
        echo %%I | findstr /i /c:"WindowsApps" >nul
        if errorlevel 1 (
            if not defined PYTHON_EXE if exist "%%I" set "PYTHON_EXE=%%I"
        )
    )
)

:: 4. Search common installation directories
if not defined PYTHON_EXE (
    if exist "C:\Users\gaura\AppData\Local\Programs\Python\Python311\python.exe" set "PYTHON_EXE=C:\Users\gaura\AppData\Local\Programs\Python\Python311\python.exe"
)
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)
if not defined PYTHON_EXE (
    if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"
)

:: Cache discovered python path for future sessions
if defined PYTHON_EXE (
    echo !PYTHON_EXE!>"%~dp0python_path.cfg"
) else (
    goto :no_python
)

:: 5. Check for Administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 goto :need_elevation

:: 6. Elevated execution (already running as Administrator)
"!PYTHON_EXE!" "%~dp0main.py" %*
set "EXIT_CODE=%errorlevel%"
if %EXIT_CODE% neq 0 (
    echo.
    echo Application exited with code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%

:need_elevation
echo ===================================================
echo   NextBoot requires Administrator privileges.
echo   Requesting User Account Control elevation...
echo ===================================================
powershell -NoProfile -Command "Start-Process -FilePath '!PYTHON_EXE!' -ArgumentList '\"%~dp0main.py\" %*' -WorkingDirectory '%~dp0' -Verb RunAs"
exit /b 0

:no_python
echo =========================================================
echo [ERROR] Python was not found on your system.
echo Please install Python 3.8+ from https://www.python.org/
echo or specify its full path in: %~dp0python_path.cfg
echo =========================================================
pause
exit /b 9009
