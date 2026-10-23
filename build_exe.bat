@echo off
setlocal EnableDelayedExpansion
title NextBoot - Standalone Executable Builder
cd /d "%~dp0"

echo ===================================================
echo   NextBoot - Standalone Executable Builder
echo ===================================================
echo.

:: 1. Check if cached in python_path.cfg
if not defined PYTHON_EXE (
    if exist "%~dp0python_path.cfg" (
        set /p CFG_PATH=<"%~dp0python_path.cfg"
        if exist "!CFG_PATH!" set "PYTHON_EXE=!CFG_PATH!"
    )
)

:: 2. Look up python via 'where python' (ignoring WindowsApps dummy stubs)
if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where python 2^>nul') do (
        echo %%I | findstr /i /c:"WindowsApps" >nul
        if errorlevel 1 (
            if not defined PYTHON_EXE if exist "%%I" set "PYTHON_EXE=%%I"
        )
    )
)

:: 3. Search common installation directories
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

:: Validate Python
if not defined PYTHON_EXE goto :no_python
if not exist "!PYTHON_EXE!" goto :no_python

echo [1/3] Using Python: "!PYTHON_EXE!"
"!PYTHON_EXE!" --version
if errorlevel 1 goto :python_error
echo.

:: 4. Check / Install PyInstaller
echo [2/3] Checking PyInstaller...
"!PYTHON_EXE!" -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing PyInstaller via pip...
    "!PYTHON_EXE!" -m pip install pyinstaller
    if errorlevel 1 goto :install_error
) else (
    echo PyInstaller is already installed.
)
echo.

:: 5. Build Standalone Single-File Executable
echo [3/3] Compiling standalone NextBoot.exe...
echo Please wait, this may take 30-60 seconds...
echo.

"!PYTHON_EXE!" -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --name "NextBoot" ^
    --add-data "%~dp0core;core" ^
    --add-data "%~dp0ui;ui" ^
    "%~dp0main.py"

if errorlevel 1 goto :build_error

:: Copy to root directory for easy access
if exist "%~dp0dist\NextBoot.exe" (
    copy /y "%~dp0dist\NextBoot.exe" "%~dp0NextBoot.exe" >nul
)

echo.
echo ===================================================
echo   [SUCCESS] Build completed successfully!
echo   Standalone executable created at:
echo   - %~dp0NextBoot.exe
echo   - %~dp0dist\NextBoot.exe
echo.
echo   You can now double-click NextBoot.exe directly!
echo ===================================================
pause
exit /b 0

:no_python
echo =========================================================
echo [ERROR] Python was not found on your system.
echo Please make sure Python 3.8+ is installed, or specify its
echo full path in: %~dp0python_path.cfg
echo =========================================================
pause
exit /b 1

:python_error
echo [ERROR] Failed to run Python executable: "!PYTHON_EXE!"
pause
exit /b 1

:install_error
echo =========================================================
echo [ERROR] Failed to install PyInstaller via pip.
echo Please ensure you are connected to the Internet and try:
echo   "!PYTHON_EXE!" -m pip install pyinstaller
echo =========================================================
pause
exit /b 1

:build_error
echo.
echo =========================================================
echo [ERROR] PyInstaller compilation failed.
echo Check the console output above for details.
echo =========================================================
pause
exit /b 1
