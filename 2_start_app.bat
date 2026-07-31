@echo off
setlocal
set SCRIPT_DIR=%~dp0

if "%SCRIPT_DIR:~0,2%"=="\\" (
    echo.
    echo This app can't be started from a network path like:
    echo   %SCRIPT_DIR%
    echo.
    echo Please either:
    echo   1. Copy this whole folder to a local drive on this PC ^(e.g. C:\...^), or
    echo   2. Map this network location to a drive letter first - in File
    echo      Explorer, right-click the network folder and choose
    echo      "Map network drive...", then run this .bat file from there.
    echo.
    pause
    exit /b 1
)

cd /d "%SCRIPT_DIR%"
set PYTHON=%SCRIPT_DIR%python\python.exe

if not exist "%PYTHON%" (
    echo Could not find python.exe at:
    echo   %PYTHON%
    echo.
    echo Check SETUP_INSTRUCTIONS.md - the portable Python folder needs to
    echo be renamed to "python" and placed next to this .bat file.
    pause
    exit /b 1
)

echo Starting Hardware Test Builder...
echo Keep this window open while you're using the app.
echo Close this window to stop the app.
echo.

start "" http://127.0.0.1:8765

"%PYTHON%" -m webapp.server

pause
