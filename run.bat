@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  Chạy backend từ thư mục gốc D:\Code\DA
REM  Lệnh đúng: uvicorn backend.app.main:app  (không phải app.main:app)
REM ─────────────────────────────────────────────────────────────────────────────
echo Starting Skin Lesion AI backend...
echo.
echo Starting Ollama tunnel watchdog...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -WindowStyle Hidden -FilePath powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','%~dp0start_ollama_tunnel_watchdog.ps1'"
echo.
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
