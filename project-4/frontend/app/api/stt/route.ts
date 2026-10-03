import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL
const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY || process.env.NEXT_PUBLIC_DEEPGRAM_API_KEY

export async function POST(request: NextRequest) {
  const startTime = Date.now()
  try {
    const audioBuffer = await request.arrayBuffer()
    const contentType = request.headers.get('content-type') || 'audio/webm'

    if (!audioBuffer || audioBuffer.byteLength === 0) {
      return NextResponse.json({ transcript: '', error: 'Empty audio payload' }, { status: 200 })
    }

    // 1. If Deepgram API key is present in environment variables, transcribe directly
    if (DEEPGRAM_API_KEY) {
      try {
        const cleanMime = contentType.split(';')[0].trim() || 'audio/webm'
        const dgRes = await fetch('https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true', {
          method: 'POST',
          headers: {
            Authorization: `Token ${DEEPGRAM_API_KEY}`,
            'Content-Type': cleanMime,
          },
          body: audioBuffer,
        })

        if (dgRes.ok) {
          const dgData = await dgRes.json()
          const transcript =
            dgData?.results?.channels?.[0]?.alternatives?.[0]?.transcript?.trim() || ''
          return NextResponse.json({
            transcript,
            latency: Date.now() - startTime,
            confidence: dgData?.results?.channels?.[0]?.alternatives?.[0]?.confidence || 0.95,
          })
        } else {
          const errBody = await dgRes.text()
          console.warn('Deepgram API response status:', dgRes.status, errBody)
        }
      } catch (dgErr) {
        console.warn('Deepgram fetch error:', dgErr)
      }
    }

    // 2. If Python backend URL is provided, proxy to it
    if (FLASK_URL) {
      try {
        const pyRes = await fetch(`${FLASK_URL}/api/stt`, {
          method: 'POST',
          body: audioBuffer,
          headers: {
            'Content-Type': contentType,
            'X-Session-Id': request.headers.get('X-Session-Id') || 'unknown',
          },
        })
        if (pyRes.ok) {
          const data = await pyRes.json()
          return NextResponse.json({
            transcript: data.transcript || '',
            latency: Date.now() - startTime,
            confidence: data.confidence || 0,
          })
        }
      } catch (err) {
        console.warn('Backend STT proxy error:', err)
      }
    }

    // 3. Graceful fallback rather than breaking 500 error
    return NextResponse.json(
      {
        transcript: '',
        error: 'Microphone transcription requires DEEPGRAM_API_KEY in Vercel settings, or use Chrome/Edge speech recognition.',
      },
      { status: 200 }
    )
  } catch (error) {
    console.error('STT error:', error)
    return NextResponse.json(
      { transcript: '', error: 'Failed to transcribe audio' },
      { status: 200 }
    )
  }
}
