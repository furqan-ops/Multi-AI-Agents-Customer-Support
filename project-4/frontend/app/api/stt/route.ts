import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL
const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY

export async function POST(request: NextRequest) {
  const startTime = Date.now()
  try {
    const audioBuffer = await request.arrayBuffer()
    const contentType = request.headers.get('content-type') || 'audio/webm'

    // 1. If Deepgram API key is present in environment variables, transcribe directly
    if (DEEPGRAM_API_KEY) {
      const dgRes = await fetch('https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true', {
        method: 'POST',
        headers: {
          Authorization: `Token ${DEEPGRAM_API_KEY}`,
          'Content-Type': contentType.split(';')[0].trim(),
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

    return NextResponse.json(
      { error: 'Speech-to-text service not configured' },
      { status: 500 }
    )
  } catch (error) {
    console.error('STT error:', error)
    return NextResponse.json(
      { error: 'Failed to transcribe audio' },
      { status: 500 }
    )
  }
}
