@echo off
setlocal EnableExtensions
set "BOOTSTRAP_DIR=%~dp0"
for %%I in ("%BOOTSTRAP_DIR%..") do set "PROJECT_ROOT=%%~fI"

if "%PROJECT_ROOT:~0,2%"=="\\" (
    echo.
    echo Test in a Box bootstrap cannot run directly from a UNC path:
    echo   %PROJECT_ROOT%
    echo.
    echo Copy the project to a local drive or map the network location to a
    echo drive letter, then run bootstrap.bat again.
    echo.
    pause
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

echo.
echo Test in a Box Bootstrap
echo =======================
echo Project: %PROJECT_ROOT%
echo.

where powershell.exe >nul 2>nul
if errorlevel 1 (
    echo ERROR: Windows PowerShell is required for bootstrap.
    echo.
    pause
    exit /b 1
)

call :run_step "Portable Python" "%BOOTSTRAP_DIR%bootstrap_winpython.ps1"
if errorlevel 1 goto :failed

call :run_step "Project folders" "%BOOTSTRAP_DIR%bootstrap_folders.ps1"
if errorlevel 1 goto :failed

call :run_step "Python dependencies" "%BOOTSTRAP_DIR%bootstrap_dependencies.ps1"
if errorlevel 1 goto :failed

call :run_step "Optional vendor components" "%BOOTSTRAP_DIR%bootstrap_vendor.ps1"
if errorlevel 1 goto :failed

call :run_step "Installation verification" "%BOOTSTRAP_DIR%bootstrap_verify.ps1"
if errorlevel 1 goto :failed

echo.
echo Bootstrap completed successfully.
echo.
echo Start Test in a Box with:
echo   2_start_app.bat
echo.
set /p "LAUNCH=Launch Test in a Box now? [Y/N]: "
if /I "%LAUNCH%"=="Y" start "" "%PROJECT_ROOT%\2_start_app.bat"
exit /b 0

:run_step
echo.
echo ------------------------------------------------------------
echo %~1
echo ------------------------------------------------------------
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass ^
    -File "%~2" -ProjectRoot "%PROJECT_ROOT%"
exit /b %ERRORLEVEL%

:failed
echo.
echo Bootstrap failed. Review the error above.
echo.
pause
exit /b 1
