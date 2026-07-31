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

echo Installing required packages using:
echo   %PYTHON%
echo.
"%PYTHON%" -m pip install --no-warn-script-location -r requirements.txt

echo.
echo Done. If you saw errors above about "connection" or "timeout", your
echo network may be blocking access to pypi.org / files.pythonhosted.org -
echo ask IT to allow these, or install from a USB drive instead.
pause
