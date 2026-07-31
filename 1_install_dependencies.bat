@echo off
cd /d %~dp0
set PYTHON=%~dp0python\python.exe

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
