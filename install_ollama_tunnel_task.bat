@echo off
set SCRIPT_DIR=%~dp0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install_ollama_tunnel_task.ps1"
pause
