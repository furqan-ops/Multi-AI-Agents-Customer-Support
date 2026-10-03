# Modern AI Voice Agent UI (Next.js)

Modern 2026-style voice agent customer support UI built with Next.js + React + Tailwind CSS.

## Quick Start

### 1. Create Next.js Project
```bash
npx create-next-app@latest voice-agent --typescript --tailwind
cd voice-agent
```

### 2. Copy Files
Copy all files from this folder into your Next.js project:
- `app/` → `src/app/` or `app/` (depending on your setup)
- `components/` → `src/components/` or `components/`
- `tailwind.config.ts` → overwrite existing
- `package.json` → merge dependencies

### 3. Install Dependencies
```bash
npm install
```

### 4. Setup Environment Variables
Rename `.env.local.example` to `.env.local` and update:
```
NEXT_PUBLIC_FLASK_URL=http://your-flask-url:5000
NEXT_PUBLIC_N8N_WEBHOOK_URL=http://your-n8n:5678/webhook/voice-agent
```

### 5. Run Dev Server
```bash
npm run dev
```

Visit `http://localhost:3000`

## File Structure

```
app/
├── api/
│   ├── stt/route.ts          (proxy to Flask STT)
│   ├── tts/route.ts          (proxy to Flask TTS)
│   └── supervisor/route.ts   (proxy to n8n)
├── layout.tsx                 (root layout)
├── page.tsx                   (main voice chat page)
├── globals.css                (tailwind styles)

components/
├── Sidebar.tsx                (metrics display)
├── ChatHistory.tsx            (message display)
└── VoiceRecorder.tsx          (audio recording)
```

## How It Works

1. **Recording**: Click mic button → browser captures audio via Web Audio API
2. **STT**: Audio sent to `/api/stt` → forwarded to Flask → Deepgram transcribes
3. **Supervisor**: Transcript sent to `/api/supervisor` → forwarded to n8n → agents process
4. **TTS**: Response sent to `/api/tts` → forwarded to Flask → Deepgram synthesizes → audio plays

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_FLASK_URL` | Your Flask backend URL |
| `NEXT_PUBLIC_N8N_WEBHOOK_URL` | Your n8n supervisor webhook |

## Deployment to Vercel

```bash
# Push to GitHub
git push origin main

# Connect to Vercel
vercel

# Add environment variables in Vercel dashboard
NEXT_PUBLIC_FLASK_URL=...
NEXT_PUBLIC_N8N_WEBHOOK_URL=...

# Deploy
vercel --prod
```

## Features

- ✅ Modern dark mode UI (2026 style)
- ✅ Real-time voice recording
- ✅ Chat history with timestamps
- ✅ Session metrics (uptime, turns, latency)
- ✅ Audio playback of agent responses
- ✅ Mobile responsive
- ✅ Vercel-ready

## API Routes

### POST `/api/stt`
Transcribes audio to text via Deepgram.
- Request: WAV/WebM audio blob
- Response: `{ transcript, latency, confidence }`

### POST `/api/supervisor`
Sends transcript to n8n supervisor agents.
- Request: `{ text, sessionId }`
- Response: `{ response, agent, latency }`

### POST `/api/tts`
Synthesizes response to audio via Deepgram.
- Request: `{ text }`
- Response: MP3 audio bytes

## Notes

- All backend calls go through Next.js API routes (no CORS issues)
- Session ID is auto-generated and persisted in localStorage
- Metrics update in real-time in the sidebar
- Chat history is stored in React state (persists per session)

## TODO

- [ ] Add localStorage persistence for chat history
- [ ] Add error retry logic
- [ ] Add volume visualization during recording
- [ ] Add typing indicators
- [ ] Add export chat history feature
