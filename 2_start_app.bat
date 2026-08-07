@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"

if "%SCRIPT_DIR:~0,2%"=="\\" (
    echo.
    echo This app can't be started from a network path like:
    echo   %SCRIPT_DIR%
    echo.
    echo Please either:
    echo   1. Copy this whole folder to a local drive on this PC ^(e.g. C:\...^), or
    echo   2. Map this network location to a drive letter first.
    echo.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass ^
    -File "%SCRIPT_DIR%support\launcher.ps1" ^
    -ProjectRoot "%SCRIPT_DIR%"

set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Test in a Box stopped with exit code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
