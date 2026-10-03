import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL || 'http://localhost:5000'

export async function POST(request: NextRequest) {
  try {
    const startTime = Date.now()
    const audioBuffer = await request.arrayBuffer()

    // Forward to Flask STT endpoint
    const response = await fetch(`${FLASK_URL}/api/stt`, {
      method: 'POST',
      body: audioBuffer,
      headers: {
        'Content-Type': 'audio/webm',
        'X-Session-Id': request.headers.get('X-Session-Id') || 'unknown',
      },
    })

    if (!response.ok) {
      throw new Error(`Flask error: ${response.status}`)
    }

    const data = await response.json()
    const latency = Date.now() - startTime

    return NextResponse.json({
      transcript: data.transcript || '',
      latency,
      confidence: data.confidence || 0,
    })
  } catch (error) {
    console.error('STT error:', error)
    return NextResponse.json(
      { error: 'Failed to transcribe audio' },
      { status: 500 }
    )
  }
}
