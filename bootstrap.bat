@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%bootstrap\bootstrap.bat"
exit /b %ERRORLEVEL%
