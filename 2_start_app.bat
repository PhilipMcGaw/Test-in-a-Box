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

echo Starting Hardware Test Builder...
echo Keep this window open while you're using the app.
echo Close this window to stop the app.
echo.

start "" http://127.0.0.1:8765

"%PYTHON%" -m webapp.server

pause
