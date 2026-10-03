import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL || 'http://localhost:5000'
const N8N_WEBHOOK_URL = process.env.NEXT_PUBLIC_N8N_WEBHOOK_URL || 'http://localhost:5678/webhook/supervisor'

export async function POST(request: NextRequest) {
  try {
    const startTime = Date.now()
    const body = await request.json()
    const sessionId = request.headers.get('X-Session-Id') || body.sessionId || 'unknown'

    // Try routing via Python backend first (which preserves Supabase call logging)
    let response: Response
    try {
      response = await fetch(`${FLASK_URL}/api/supervisor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': sessionId,
        },
        body: JSON.stringify({
          text: body.text,
          sessionId: sessionId,
        }),
      })
    } catch {
      // Fallback: direct to n8n supervisor webhook
      response = await fetch(N8N_WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': sessionId,
        },
        body: JSON.stringify({
          message: body.text,
          channel: 'voice',
          sessionId: sessionId,
        }),
      })
    }

    if (!response.ok) {
      throw new Error(`Supervisor endpoint error: ${response.status}`)
    }

    const data = await response.json()
    const latency = Date.now() - startTime

    const payload = Array.isArray(data) ? data[0] : data
    let responseText = payload.response || payload.answer || payload.text || payload.output

    if (!responseText) {
      if (payload.status === 'confirmed' && payload.date) {
        const party = payload.party_size || 2
        responseText = `Your reservation is confirmed! A table for ${party} guests has been booked for ${payload.date} at ${payload.time || 'your requested time'}. We look forward to hosting you!`
      } else if (payload.status === 'need_more_info') {
        responseText = (payload.message && !payload.message.toLowerCase().includes('all'))
          ? payload.message
          : "I'd be glad to help you book a table! Could you please let me know:\n• What date would you like to book for?\n• What time?\n• How many guests will be in your party?"
      } else if (payload.ticket_id) {
        responseText = `Your inquiry has been escalated to our customer support team (Ticket #${payload.ticket_id}). A representative will assist you shortly.`
      } else if (payload.message && payload.message.trim().toLowerCase() !== (body.text || '').trim().toLowerCase()) {
        if (payload.message.toLowerCase().includes('please provide: all')) {
          responseText = "I'd be happy to help you book a table! Could you please let me know what date, time, and how many guests you would like to reserve for?"
        } else {
          responseText = payload.message
        }
      } else {
        responseText = "I'm sorry, I didn't quite catch that. Could you please rephrase or let me know if you would like to reserve a table, check your booking status, or inquire about our hours and policies?"
      }
    }

    return NextResponse.json({
      response: responseText,
      agent: payload.agent || 'supervisor',
      latency,
    })
  } catch (error) {
    console.error('Supervisor error:', error)
    return NextResponse.json(
      {
        response: 'Unable to communicate with the supervisor service. Please ensure n8n or the backend server is running.',
        agent: 'system_fallback',
        latency: 0,
      },
      { status: 200 }
    )
  }
}

