import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL || 'http://localhost:5000'

export async function POST(request: NextRequest) {
  try {
    const startTime = Date.now()
    const body = await request.json()

    // Forward to Flask TTS endpoint
    const response = await fetch(`${FLASK_URL}/api/tts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: body.text,
      }),
    })

    if (!response.ok) {
      throw new Error(`Flask error: ${response.status}`)
    }

    // Get audio as buffer
    const audioBuffer = await response.arrayBuffer()
    const latency = Date.now() - startTime

    return new NextResponse(audioBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'audio/mpeg',
        'X-Latency': latency.toString(),
      },
    })
  } catch (error) {
    console.error('TTS error:', error)
    return NextResponse.json(
      { error: 'Failed to synthesize speech' },
      { status: 500 }
    )
  }
}
