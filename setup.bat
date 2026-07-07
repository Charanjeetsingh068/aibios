@echo off
rem ==============================================================================
rem AI-BOS Enterprise Local Setup Script Wrapper (Windows Batch)
rem ==============================================================================

echo Launching AI-BOS Local Setup using PowerShell...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if %ERRORLEVEL% neq 0 (
    echo Setup failed with error code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)
