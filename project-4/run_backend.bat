@echo off
cd /d "%~dp0"
echo Starting Voice Agent Backend Server on port 5000...
".\.venv\Scripts\python.exe" -m app.server
pause
