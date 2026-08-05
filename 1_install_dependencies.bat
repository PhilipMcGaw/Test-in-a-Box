@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"

echo.
echo 1_install_dependencies.bat is retained for compatibility.
echo The supported setup entry point is now bootstrap.bat.
echo.

call "%SCRIPT_DIR%bootstrap.bat"
exit /b %ERRORLEVEL%
