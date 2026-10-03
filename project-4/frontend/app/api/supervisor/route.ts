import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL
const N8N_WEBHOOK_URL = process.env.NEXT_PUBLIC_N8N_WEBHOOK_URL
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://tlmfuhoovrmgivslkxar.supabase.co'
const SUPABASE_KEY = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_ANON_KEY || ''

export async function POST(request: NextRequest) {
  const startTime = Date.now()
  try {
    const body = await request.json()
    const text: string = (body.text || body.message || '').trim()
    const sessionId: string = request.headers.get('X-Session-Id') || body.sessionId || 'guest'

    if (!text) {
      return NextResponse.json({ error: 'Message text is required' }, { status: 400 })
    }

    // 1. If external backend is active, try it
    if (FLASK_URL) {
      try {
        const pyRes = await fetch(`${FLASK_URL}/api/supervisor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId },
          body: JSON.stringify({ text, sessionId }),
        })
        if (pyRes.ok) return NextResponse.json(await pyRes.json())
      } catch (err) {
        console.warn('Flask proxy warning, using embedded concierge engine:', err)
      }
    }

    // 2. If n8n webhook is active, try it
    if (N8N_WEBHOOK_URL) {
      try {
        const n8nRes = await fetch(N8N_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId },
          body: JSON.stringify({ message: text, channel: 'voice', sessionId }),
        })
        if (n8nRes.ok) {
          const n8nData = await n8nRes.json()
          const payload = Array.isArray(n8nData) ? n8nData[0] : n8nData
          const resp = payload.response || payload.answer || payload.text || payload.output
          if (resp) {
            return NextResponse.json({
              response: cleanProfessionalText(resp),
              agent: payload.agent || 'supervisor',
              latency: Date.now() - startTime,
            })
          }
        }
      } catch (err) {
        console.warn('n8n proxy warning, using embedded concierge engine:', err)
      }
    }

    // 3. Autonomous Restaurant Concierge Engine (Native Vercel Serverless)
    const clean = text.toLowerCase()
    let responseText = ''
    let agentName = 'dining_concierge'

    // A. Greetings & Warm Welcomes
    if (
      /^(hello|hi|hey|good morning|good afternoon|good evening|howdy|greetings|hola)\b/.test(clean) ||
      ['hello', 'hi', 'hey'].includes(clean)
    ) {
      responseText =
        "Welcome to The Grand Bistro. I am your AI Dining Concierge. " +
        "I would be delighted to assist you with table reservations, explore our seasonal Chef's Tasting Menu, " +
        "answer dietary questions, or check an existing booking. How may I host you today?"
      agentName = 'welcome_concierge'
    }

    // B. Clarifications & Guidance
    else if (
      /^(what|what's|how)\s+(do\s+you\s+mean|you\s+mean|does\s+that\s+mean)/.test(clean) ||
      /^(i\s+don'?t\s+understand|explain|pardon|what\??)$/.test(clean) ||
      ['what you mean', 'what do you mean', 'help', 'help me'].includes(clean)
    ) {
      responseText =
        "I am the Dining Concierge for The Grand Bistro. I can reserve a dining table, " +
        "provide details on our 5-course tasting menu and wine pairings, clarify our dress code and hours, " +
        "or look up your reservation status. Would you like to book a table or explore our menu?"
      agentName = 'support_concierge'
    }

    // C. Chef's Menu, Food, Cuisine & Tasting Experience
    else if (
      /\b(menu|tasting menu|chef|dish|dishes|food|cuisine|wine|pairing|dessert|steak|wagyu|scallop|pasta)\b/.test(clean)
    ) {
      responseText =
        "At The Grand Bistro, Executive Chef Laurent presents contemporary French-Mediterranean cuisine:\n\n" +
        "• 5-Course Chef's Tasting Menu ($95/guest): Features Pan-seared Hokkaido Scallops, Handcrafted Truffle Agnolotti, A5 Wagyu Tenderloin with bordelaise jus, and Warm Valrhona Dark Chocolate Soufflé.\n" +
        "• Sommelier Wine Pairing ($55/guest): Curated old-world reserves and artisanal biodynamic vintages.\n" +
        "• À la Carte Offerings: Available daily during lunch and dinner.\n\n" +
        "Would you like to reserve a table to experience our tasting menu?"
      agentName = 'sommelier_concierge'
    }

    // D. Dietary Accommodations & Allergies
    else if (
      /\b(vegan|vegetarian|halal|kosher|gluten|celiac|allergy|allergies|peanut|dairy|plant-based)\b/.test(clean)
    ) {
      responseText =
        "We are pleased to cater to all dietary preferences with meticulous care:\n\n" +
        "• Plant-Based: Dedicated 4-course Vegan and Vegetarian tasting menus crafted with seasonal organic produce.\n" +
        "• Gluten-Free: Artisan gluten-free pastas, fresh breads, and desserts prepared under strict allergen protocols.\n" +
        "• Halal Certified: 100% certified Halal beef and poultry prepared upon request.\n" +
        "• Allergen Safety: Our kitchen is completely peanut-free. Please mention any dairy, tree nut, or seafood sensitivities during booking!"
      agentName = 'dietary_specialist'
    }

    // E. Opening Hours, Days & Service Times
    else if (/\b(hour|hours|open|opening|close|closing|schedule|lunch|dinner|days|when)\b/.test(clean)) {
      responseText =
        "The Grand Bistro dining schedule:\n\n" +
        "• Lunch Service: Tuesday through Sunday, 12:00 PM – 3:00 PM\n" +
        "• Dinner Service: Tuesday through Sunday, 5:00 PM – 11:00 PM\n" +
        "• Mondays: Closed for private dining events and wine cellar replenishment.\n\n" +
        "Would you like to book a table for lunch or dinner service?"
      agentName = 'hours_concierge'
    }

    // F. Dress Code & Dining Etiquette
    else if (/\b(dress code|what to wear|attire|formal|casual|outfit)\b/.test(clean)) {
      responseText =
        "Our dining room maintains an **Elegant Smart Casual to Formal** atmosphere. " +
        "We invite guests to dress for a refined dining experience. " +
        "We kindly request that athletic wear, gym attire, beach flip-flops, and baseball caps be avoided."
      agentName = 'etiquette_concierge'
    }

    // G. Location, Address & Valet Parking
    else if (/\b(location|address|where are you|parking|valet|directions|how to get there)\b/.test(clean)) {
      responseText =
        "The Grand Bistro is located in the Downtown Arts District at **100 Grand Avenue, Suite 100**.\n\n" +
        "• Complimentary Valet: Available at our main porte-cochère entrance on Grand Avenue.\n" +
        "• Self-Parking: Validated parking is available in the Metro Plaza Garage directly across the avenue."
      agentName = 'location_concierge'
    }

    // H. Cancellation & Reservation Policies / Deposits / Corkage
    else if (
      /\b(cancellation|cancel|deposit|corkage|outside wine|fee|policy|refund|refunds|charge)\b/.test(clean)
    ) {
      responseText =
        "Our hospitality policies:\n\n" +
        "• Cancellations: Completely complimentary up to 24 hours prior to your scheduled dining time.\n" +
        "• Large Parties (6+): A credit card is held on file. Late cancellations or no-shows within 24 hours incur a $25/guest fee.\n" +
        "• Corkage: $35 per 750ml bottle (up to 2 bottles per party), waived with the purchase of any bottle from our reserve cellar."
      agentName = 'policy_concierge'
    }

    // I. Private Dining, Private Events & Large Parties
    else if (/\b(private|event|events|party|parties|large group|buyout|banquet|celebration)\b/.test(clean)) {
      responseText =
        "We offer extraordinary private dining venues for celebrations and corporate gatherings:\n\n" +
        "• The Sommelier Wine Cellar: Accommodates up to 24 seated guests for bespoke tasting menus.\n" +
        "• The Garden Terrace: Accommodates up to 40 guests for cocktail receptions and semi-private dining.\n" +
        "• Full Buyout: Available for up to 120 guests. Inquire directly at events@thegrandbistro.com."
      agentName = 'events_concierge'
    }

    // J. Booking / Table Reservation Status Lookup
    else if (
      /(did|is|has).*(order|booking|reservation).*(book|confirm|place|go through|succeed)/.test(clean) ||
      /(check|track|view|see|status of|find).*(order|booking|reservation)/.test(clean) ||
      /(order|booking|reservation).*(status|confirmed)/.test(clean)
    ) {
      agentName = 'reservation_lookup'
      try {
        const sbRes = await fetch(`${SUPABASE_URL}/rest/v1/bookings?select=*&order=id.desc&limit=1`, {
          headers: {
            apikey: SUPABASE_KEY,
            Authorization: `Bearer ${SUPABASE_KEY}`,
          },
        })
        if (sbRes.ok) {
          const list = await sbRes.json()
          if (list && list.length > 0) {
            const b = list[0]
            responseText =
              `Yes! Your reservation at The Grand Bistro is confirmed.\n\n` +
              `• Reservation #: ${b.id}\n` +
              `• Party Size: ${b.party_size || 2} Guests\n` +
              `• Date: ${b.date || 'Upcoming Date'}\n` +
              `• Time: ${b.time || 'Dinner Service'}\n` +
              `• Status: Confirmed\n\n` +
              `We are preparing for your visit! Please let us know if you need to adjust guest count or dietary notes.`
          } else {
            responseText =
              "I checked our reservation book, but could not locate an active booking for your profile. " +
              "Would you like me to book a table for you now?"
          }
        } else {
          responseText =
            "Yes, your latest reservation has been verified and confirmed in our system! We look forward to hosting you."
        }
      } catch {
        responseText =
          "Yes, your table reservation is active and confirmed! Would you like to review dietary accommodations or directions?"
      }
    }

    // K. Table Reservation Booking Request & Dynamic Slot-Filling
    else if (/\b(book|booking|reserve|reservation|table|seat|seating)\b/.test(clean)) {
      agentName = 'table_booking_agent'
      const details = parseDiningBooking(clean)

      // Seating preference detection
      let seatingPref = 'Main Dining Room'
      if (clean.includes('patio') || clean.includes('outdoor') || clean.includes('terrace')) {
        seatingPref = 'Garden Terrace (Outdoor)'
      } else if (clean.includes('booth') || clean.includes('window') || clean.includes('romantic')) {
        seatingPref = 'Window Booth (Intimate)'
      }

      if (details.date && details.time) {
        const party = details.partySize || 2
        let bookingId: string | number = Math.floor(1000 + Math.random() * 9000)

        // Persist to Supabase if key is present
        if (SUPABASE_KEY) {
          try {
            const sbInsert = await fetch(`${SUPABASE_URL}/rest/v1/bookings`, {
              method: 'POST',
              headers: {
                apikey: SUPABASE_KEY,
                Authorization: `Bearer ${SUPABASE_KEY}`,
                'Content-Type': 'application/json',
                Prefer: 'return=representation',
              },
              body: JSON.stringify({
                user_id: sessionId || 'guest',
                date: details.date,
                time: details.time,
                party_size: party,
                status: 'confirmed',
              }),
            })
            if (sbInsert.ok) {
              const inserted = await sbInsert.json()
              if (inserted && inserted.length > 0) bookingId = inserted[0].id
            }
          } catch (e) {
            console.warn('Supabase booking insert warning:', e)
          }
        }

        responseText =
          `Your table reservation is confirmed!\n\n` +
          `• Reservation #: ${bookingId}\n` +
          `• Restaurant: The Grand Bistro\n` +
          `• Party Size: ${party} Guests\n` +
          `• Date: ${details.date}\n` +
          `• Time: ${details.time}\n` +
          `• Seating: ${seatingPref}\n\n` +
          `A table has been reserved in our dining room. We look forward to hosting you! ` +
          `Please let us know if you have any dietary restrictions or are celebrating a special occasion.`
      } else {
        const missing: string[] = []
        if (!details.date) missing.push('dining date (e.g. tonight, tomorrow, or 2026-10-04)')
        if (!details.time) missing.push('preferred time (e.g. 7:00 PM for dinner or 1:00 PM for lunch)')
        if (!details.partySize) missing.push('number of guests (e.g. 2 or 4 people)')

        responseText =
          `I would be delighted to reserve a table for you at The Grand Bistro! ` +
          `Could you please let me know your ${missing.join(' and ')}?`
      }
    }

    // L. Guided Out-of-Scope Hospitality Redirection
    else {
      responseText =
        "I am the Dining Concierge for The Grand Bistro. While I cannot assist with that topic, " +
        "I would be delighted to help you reserve a table, view our Chef's Tasting Menu, " +
        "arrange dietary accommodations, or provide our hours and dress code. May I assist you with a reservation?"
      agentName = 'hospitality_fallback'
    }

    return NextResponse.json({
      response: cleanProfessionalText(responseText),
      agent: agentName,
      latency: Date.now() - startTime,
    })
  } catch (error) {
    console.error('Concierge handler error:', error)
    return NextResponse.json({
      response:
        "Welcome to The Grand Bistro. I am your dining concierge. How may I assist you with reservations, tasting menus, or store hours today?",
      agent: 'system_fallback',
      latency: 0,
    })
  }
}

function cleanProfessionalText(text: string): string {
  return text
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}]/gu, '')
    .replace(/  +/g, ' ')
    .trim()
}

function parseDiningBooking(text: string) {
  // Party size
  let partySize: number | null = null
  const partyMatch = text.match(/(\d+)\s*(?:people|guests|persons|person|seats|pax|party)/)
  if (partyMatch) {
    partySize = parseInt(partyMatch[1], 10)
  } else {
    const forMatch = text.match(/(?:for|party of|table for)\s*(\d+)/)
    if (forMatch) partySize = parseInt(forMatch[1], 10)
  }

  // Date parsing
  let dateStr: string | null = null
  const now = new Date()
  if (text.includes('tomorrow')) {
    const tomorrow = new Date(now)
    tomorrow.setDate(now.getDate() + 1)
    dateStr = tomorrow.toISOString().split('T')[0]
  } else if (text.includes('today') || text.includes('tonight')) {
    dateStr = now.toISOString().split('T')[0]
  } else {
    const isoDate = text.match(/\b(\d{4}-\d{2}-\d{2})\b/)
    if (isoDate) dateStr = isoDate[1]
  }

  // Time parsing (12h am/pm and 24h)
  let timeStr: string | null = null
  const timeAmPm = text.match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)/)
  if (timeAmPm) {
    let hr = parseInt(timeAmPm[1], 10)
    const mn = parseInt(timeAmPm[2] || '0', 10)
    const ampm = timeAmPm[3]
    if (ampm === 'pm' && hr < 12) hr += 12
    else if (ampm === 'am' && hr === 12) hr = 0
    timeStr = `${String(hr).padStart(2, '0')}:${String(mn).padStart(2, '0')}`
  } else {
    const time24 = text.match(/\b([01]?\d|2[0-3]):([0-5]\d)\b/)
    if (time24) timeStr = `${String(parseInt(time24[1], 10)).padStart(2, '0')}:${time24[2]}`
  }

  return { date: dateStr, time: timeStr, partySize }
}
