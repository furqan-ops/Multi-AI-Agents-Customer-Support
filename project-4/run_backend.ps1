Write-Host "Starting Voice Agent Backend Server on port 5000..." -ForegroundColor Cyan
& "$PSScriptRoot\.venv\Scripts\python.exe" -m app.server
