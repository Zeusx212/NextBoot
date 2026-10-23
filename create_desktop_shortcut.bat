@echo off
setlocal
cd /d "%~dp0"

echo Creating Desktop Shortcut for NextBoot...

powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$shortcut = $ws.CreateShortcut(\"$desktop\NextBoot - OS Switcher.lnk\"); " ^
  "$shortcut.TargetPath = '%~dp0NextBoot.bat'; " ^
  "$shortcut.WorkingDirectory = '%~dp0'; " ^
  "$shortcut.Description = 'NextBoot - Switch and boot directly into secondary operating systems'; " ^
  "$shortcut.Save()"

if %errorlevel% == 0 (
    echo [SUCCESS] Desktop shortcut created successfully!
) else (
    echo [ERROR] Failed to create shortcut.
)
pause
