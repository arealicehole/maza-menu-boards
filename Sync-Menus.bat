@echo off
title Restaurant Menu Sync
echo ======================================================
echo Starting Restaurant Menu Sync...
echo ======================================================
echo.

:: Run the PowerShell script bypassing the execution policy
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync-menus.ps1"

echo.
echo ======================================================
echo Finished! Press any key to close this window.
echo ======================================================
pause > nul
