@echo off
setlocal EnableExtensions
set "PROJECT_ROOT=%~dp0"
set "CHANNEL=%~1"

if "%PROJECT_ROOT:~0,2%"=="\\" (
    echo.
    echo The updater cannot run directly from a UNC path:
    echo   %PROJECT_ROOT%
    echo.
    echo Map the location to a drive letter, then run update.bat again.
    echo.
    pause
    exit /b 1
)

if not defined CHANNEL (
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

    if errorlevel 3 exit /b 0
    if errorlevel 2 set "CHANNEL=development"
    if errorlevel 1 set "CHANNEL=stable"
)

if /I not "%CHANNEL%"=="stable" if /I not "%CHANNEL%"=="development" (
    echo.
    echo ERROR: Unknown update channel "%CHANNEL%".
    echo Use:
    echo   update.bat stable
    echo   update.bat development
    echo.
    pause
    exit /b 1
)

where powershell.exe >nul 2>nul
if errorlevel 1 (
    echo ERROR: Windows PowerShell is required by the updater.
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
