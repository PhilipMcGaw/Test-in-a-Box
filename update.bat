@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"
set "ACTION=%~1"

if not defined ACTION goto :menu
if /I "%ACTION%"=="S" set "ACTION=stable"
if /I "%ACTION%"=="D" set "ACTION=development"

if /I "%ACTION%"=="stable" goto :run
if /I "%ACTION%"=="development" goto :run
if /I "%ACTION%"=="rollback" goto :run

echo ERROR: use update.bat stable, development, or rollback
pause
exit /b 1

:menu
echo.
echo Test in a Box Updater V2
echo ========================
echo.
echo   [S] Stable
echo   [D] Development
echo   [R] Roll back
echo   [Q] Quit
echo.
choice /C SDRQ /N /M "Select [S/D/R/Q]: "
if errorlevel 4 exit /b 0
if errorlevel 3 set "ACTION=rollback"
if errorlevel 3 goto :run
if errorlevel 2 set "ACTION=development"
if errorlevel 2 goto :run
set "ACTION=stable"

:run
if not exist "%PROJECT_ROOT%\updater\updater.ps1" (
    echo ERROR: updater\updater.ps1 is missing.
    pause
    exit /b 1
)

set "TIAB_UPDATE_ACTION=%ACTION%"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\updater\updater.ps1" -ProjectRoot "%PROJECT_ROOT%"
set "RESULT=%ERRORLEVEL%"
set "TIAB_UPDATE_ACTION="

if not "%RESULT%"=="0" (
    echo.
    echo Updater V2 failed.
    pause
    exit /b %RESULT%
)

exit /b 0
