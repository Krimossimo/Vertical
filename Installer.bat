@echo off
chcp 65001 >nul
title Installation de Vertical
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1" -NoPause %*
echo.
pause
