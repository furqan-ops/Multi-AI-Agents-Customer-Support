# Project 4: AI Voice Agent

A modern voice agent customer support application connecting voice input/output to the multi-agent supervisor system.

## Architecture

```text
Browser (Web Audio API / MediaRecorder)
          │
          ▼
Next.js Frontend (project-4/frontend)
          │
          ▼
Python ASGI Server (project-4/app/server.py on :5000)
    ├── STT: Deepgram Nova-2 (voice_io.py)
    ├── TTS: Edge-TTS AriaNeural (voice_io.py)
    ├── Supervisor: n8n Supervisor Webhook (voice_io.py)
    └── Observability: Supabase `voice_calls` (logger.py)
```

---

## Quickstart

### 1. Start the Python Backend Server
From the `project-4` folder, you can run any of the following:

**Option A (Direct - Recommended):**
```powershell
.\.venv\Scripts\python.exe -m app.server
```

**Option B (Helper Script):**
```powershell
.\run_backend.bat
# or in PowerShell: .\run_backend.ps1
```

**Option C (Activate venv first):**
```powershell
.\.venv\Scripts\Activate.ps1
python -m app.server
```
The backend API server will run at `http://localhost:5000`.

### 2. Start the Modern Next.js UI
In a separate terminal:
```powershell
cd project-4\frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Features
- **Modern 2026 Dark UI**: Glowing pulse orb, glassmorphic layout, animated transitions.
- **Real-Time Voice Capture**: Browser-native HTML5 MediaRecorder.
- **Multi-Agent Routing**: Direct connection to n8n multi-agent supervisor system.
- **Fast Neural TTS**: Response speech synthesized via edge-tts with instant auto-playback.
- **Observability**: Live metrics tracking (latency, turns, uptime) and Supabase database logging.
