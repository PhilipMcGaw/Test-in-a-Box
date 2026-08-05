@echo off
setlocal EnableExtensions
set "PROJECT_ROOT=%~dp0"
set "CHANNEL=%~1"

if defined CHANNEL goto :normalise_channel

:menu
echo.
echo Test in a Box Updater
echo =====================
echo.
echo   [S] Stable
echo       Latest published release, falling back to the newest tag.
echo.
echo   [D] Development
echo       Latest contents of the main branch.
echo.
echo   [Q] Quit
echo.
choice /C SDQ /N /M "Select update channel [S/D/Q]: "

if errorlevel 3 goto :quit
if errorlevel 2 set "CHANNEL=development"
if errorlevel 2 goto :run_updater
set "CHANNEL=stable"
goto :run_updater

:normalise_channel
if /I "%CHANNEL%"=="S" set "CHANNEL=stable"
if /I "%CHANNEL%"=="D" set "CHANNEL=development"
if /I "%CHANNEL%"=="stable" goto :run_updater
if /I "%CHANNEL%"=="development" goto :run_updater

echo.
echo ERROR: Unknown update channel "%CHANNEL%".
echo.
echo Use one of:
echo   update.bat S
echo   update.bat D
echo   update.bat stable
echo   update.bat development
echo.
pause
exit /b 1

:run_updater
echo.
echo Selected update channel: %CHANNEL%
echo.

if not exist "%PROJECT_ROOT%updater\update.ps1" (
    echo ERROR: Updater script not found:
    echo   %PROJECT_ROOT%updater\update.ps1
    echo.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%updater\update.ps1" ^
    -ProjectRoot "%PROJECT_ROOT%" ^
    -Channel "%CHANNEL%"

set "RESULT=%ERRORLEVEL%"

if not "%RESULT%"=="0" (
    echo.
    echo Update failed. Review the messages above.
    echo.
    pause
    exit /b %RESULT%
)

echo.
pause
exit /b 0

:quit
exit /b 0
