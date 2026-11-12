@echo off
chcp 65001 >nul
title Vertical (console)
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Vertical n'est pas installe. Lance d'abord Installer.bat
  pause
  exit /b 1
)
rem Dossier deplace ? On repare le chemin Python du venv.
powershell -NoProfile -Command "$d=Get-ChildItem '%~dp0tools\python' -Directory -Filter 'cpython-*' | Where-Object { -not $_.Attributes.HasFlag([IO.FileAttributes]::ReparsePoint) -and (Test-Path (Join-Path $_.FullName 'python.exe')) } | Select-Object -First 1; if($d){ $f='%~dp0.venv\pyvenv.cfg'; (Get-Content $f) -replace '^home = .*',('home = '+$d.FullName) | Set-Content $f }" >nul 2>&1
set "PATH=%~dp0tools\ffmpeg\bin;%PATH%"
".venv\Scripts\python.exe" -m vertical %*
if errorlevel 1 pause
