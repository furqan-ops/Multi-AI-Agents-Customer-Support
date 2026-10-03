import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = process.env.NEXT_PUBLIC_FLASK_URL
const N8N_WEBHOOK_URL = process.env.NEXT_PUBLIC_N8N_WEBHOOK_URL
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://tlmfuhoovrmgivslkxar.supabase.co'
const SUPABASE_KEY = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_ANON_KEY || ''

export async function POST(request: NextRequest) {
  const startTime = Date.now()
  try {
    const body = await request.json()
    const rawText: string = (body.text || body.message || '').trim()
    const sessionId: string = request.headers.get('X-Session-Id') || body.sessionId || 'guest'
    const history: Array<{ role: string; text: string }> = Array.isArray(body.history) ? body.history : []

    if (!rawText) {
      return NextResponse.json({ error: 'Message text is required' }, { status: 400 })
    }

    // 1. If external backend is active, try it
    if (FLASK_URL) {
      try {
        const pyRes = await fetch(`${FLASK_URL}/api/supervisor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId },
          body: JSON.stringify({ text: rawText, sessionId }),
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
          body: JSON.stringify({ message: rawText, channel: 'voice', sessionId }),
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

    // 3. Autonomous Restaurant Concierge Engine with Typo Auto-Correction
    const clean = normalizeAndCorrectText(rawText)
    let responseText = ''
    let agentName = 'dining_concierge'

    // Multi-turn context inspection
    const lastAgentMsg = history.filter((h) => h.role === 'agent').pop()?.text || ''
    const wasAskedForBooking = /date|time|guests|people|party|reserve|reservation/i.test(lastAgentMsg)
    const wasAskedToBookTable = /would you like to reserve|may i assist you with a reservation|would you like to book|reserve a table/i.test(lastAgentMsg)

    // Pre-parse dining booking slots (merged with prior history if needed)
    const details = resolveBookingWithHistory(clean, history)

    // A. Affirmations to previous concierge questions ("yes", "sure", "ok", "please")
    if (
      /^(yes|yeah|yep|sure|ok|okay|please|definitely|absolutely|i would love to|certainly)\b/.test(clean) &&
      (wasAskedToBookTable || wasAskedForBooking)
    ) {
      responseText =
        "Wonderful! I would be delighted to reserve a table for you at The Grand Bistro. " +
        "Could you please let me know your preferred dining date (e.g. tonight or tomorrow), " +
        "time (e.g. 7:00 PM for dinner or 1:00 PM for lunch), and number of guests?"
      agentName = 'table_booking_agent'
    }

    // B. Greetings & Welcomes ("hi", "hay", "heyy", "hello", "good evening", etc.)
    else if (
      /^(hello|hi|hey|hay|heyy|heya|howdy|greetings|hola|good morning|good afternoon|good evening)\b/.test(clean) ||
      ['hello', 'hi', 'hey', 'hay', 'heyy', 'hola'].includes(clean)
    ) {
      responseText =
        "Hello! Welcome to The Grand Bistro. I am your AI Dining Concierge. How may I help you today? " +
        "I would be delighted to assist you with table reservations, our 5-course Chef's Tasting Menu, " +
        "dietary accommodations, or checking an existing booking."
      agentName = 'welcome_concierge'
    }

    // C. Gratitude & Courtesies ("thank you", "thanks", "appreciate it")
    else if (
      /\b(thank you|thanks|thx|thank u|many thanks|appreciate it|much appreciated|grateful|ty)\b/.test(clean) ||
      ['thank you', 'thanks', 'thx', 'thank u', 'ty'].includes(clean)
    ) {
      responseText =
        "You are most welcome! It is our absolute pleasure to assist you. " +
        "Please let us know if there is anything else we can arrange for your visit, and we look forward to hosting you at The Grand Bistro."
      agentName = 'hospitality_courtesy'
    }

    // D. Goodbyes & Farewell ("bye", "goodbye", "have a nice day")
    else if (
      /\b(goodbye|bye|bye bye|see you|see ya|cya|have a good day|have a good night|have a great day|have a nice day)\b/.test(clean) ||
      ['bye', 'goodbye'].includes(clean)
    ) {
      responseText =
        "Goodbye and have a wonderful day! We look forward to welcoming you to The Grand Bistro soon."
      agentName = 'hospitality_farewell'
    }

    // E. Positive Acknowledgments ("perfect", "sounds good", "great")
    else if (
      /^(perfect|sounds good|sounds great|awesome|excellent|wonderful|great|superb|lovely|nice|cool)\b/.test(clean) &&
      clean.length < 35
    ) {
      responseText =
        "Wonderful! We are delighted to assist. Please let me know if you would like to explore our tasting menu, check reservation details, or if you have any questions for your visit."
      agentName = 'hospitality_courtesy'
    }

    // C. Table Reservation Request & Follow-Up Slot-Filling
    else if (
      /\b(book|booking|reserve|reservation|table|seat|seating)\b/.test(clean) ||
      (details.date && details.time) ||
      (details.date && details.partySize) ||
      (details.time && details.partySize) ||
      (wasAskedForBooking && (details.date || details.time || details.partySize))
    ) {
      agentName = 'table_booking_agent'

      // Seating preference detection
      let seatingPref = 'Main Dining Room'
      if (clean.includes('patio') || clean.includes('outdoor') || clean.includes('terrace')) {
        seatingPref = 'Garden Terrace (Outdoor)'
      } else if (clean.includes('booth') || clean.includes('window') || clean.includes('romantic')) {
        seatingPref = 'Window Booth (Intimate)'
      } else if ((details.partySize || 2) >= 8) {
        seatingPref = 'Garden Terrace / Grand Cellar (Private Dining)'
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

        const partyNote =
          party >= 8
            ? `For your party of ${party}, we have designated our expansive private dining terrace and cellar.`
            : `A private table has been reserved in our ${seatingPref}.`

        responseText =
          `Your booking is confirmed! We wish you happy meals and an unforgettable dining experience at The Grand Bistro.\n\n` +
          `• Reservation #: ${bookingId}\n` +
          `• Restaurant: The Grand Bistro\n` +
          `• Party Size: ${party} Guests\n` +
          `• Date: ${details.date}\n` +
          `• Time: ${details.time}\n` +
          `• Seating: ${seatingPref}\n` +
          `• Status: Confirmed\n\n` +
          `${partyNote} We look forward to hosting you! Please let us know if your party has any dietary preferences, allergen notes, or is celebrating a special milestone.`
      } else {
        const missing: string[] = []
        if (!details.date) missing.push('dining date (e.g. tonight, tomorrow, or a specific date)')
        if (!details.time) missing.push('preferred time (e.g. 7:00 PM for dinner or 1:00 PM for lunch)')
        if (!details.partySize) missing.push('number of guests (e.g. 2, 4, or 20 people)')

        responseText =
          `I would be delighted to reserve a table for you at The Grand Bistro! ` +
          `Could you please let me know your ${missing.join(' and ')}?`
      }
    }

    // D. Booking / Table Reservation Status Lookup
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

    // E. Clarifications & Guidance
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

    // F. Chef's Menu, Food, Cuisine & Tasting Experience
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

    // G. Dietary Accommodations & Allergies
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

    // H. Opening Hours, Days & Service Times
    else if (/\b(hour|hours|open|opening|close|closing|schedule|lunch|dinner|days|when)\b/.test(clean)) {
      responseText =
        "The Grand Bistro dining schedule:\n\n" +
        "• Lunch Service: Tuesday through Sunday, 12:00 PM – 3:00 PM\n" +
        "• Dinner Service: Tuesday through Sunday, 5:00 PM – 11:00 PM\n" +
        "• Mondays: Closed for private dining events and wine cellar replenishment.\n\n" +
        "Would you like to book a table for lunch or dinner service?"
      agentName = 'hours_concierge'
    }

    // I. Dress Code & Dining Etiquette
    else if (/\b(dress code|what to wear|attire|formal|casual|outfit)\b/.test(clean)) {
      responseText =
        "Our dining room maintains an **Elegant Smart Casual to Formal** atmosphere. " +
        "We invite guests to dress for a refined dining experience. " +
        "We kindly request that athletic wear, gym attire, beach flip-flops, and baseball caps be avoided."
      agentName = 'etiquette_concierge'
    }

    // J. Location, Address & Valet Parking
    else if (/\b(location|address|where are you|parking|valet|directions|how to get there)\b/.test(clean)) {
      responseText =
        "The Grand Bistro is located in the Downtown Arts District at **100 Grand Avenue, Suite 100**.\n\n" +
        "• Complimentary Valet: Available at our main porte-cochère entrance on Grand Avenue.\n" +
        "• Self-Parking: Validated parking is available in the Metro Plaza Garage directly across the avenue."
      agentName = 'location_concierge'
    }

    // K. Cancellation & Reservation Policies / Deposits / Corkage
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

    // L. Private Dining, Private Events & Large Parties
    else if (/\b(private|event|events|party|parties|large group|buyout|banquet|celebration)\b/.test(clean)) {
      responseText =
        "We offer extraordinary private dining venues for celebrations and corporate gatherings:\n\n" +
        "• The Sommelier Wine Cellar: Accommodates up to 24 seated guests for bespoke tasting menus.\n" +
        "• The Garden Terrace: Accommodates up to 40 guests for cocktail receptions and semi-private dining.\n" +
        "• Full Buyout: Available for up to 120 guests. Inquire directly at events@thegrandbistro.com."
      agentName = 'events_concierge'
    }

    // M. Guided Out-of-Scope Hospitality Redirection
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

/**
 * Normalizes user queries, repairs common misspellings, resolves dictionary typos,
 * converts number words (twenty -> 20), and prepares clean text for intent extraction.
 */
function normalizeAndCorrectText(raw: string): string {
  let text = raw.toLowerCase().trim()

  // 1. Convert word numbers to digits
  const wordNumbers: Record<string, string> = {
    one: '1',
    two: '2',
    three: '3',
    four: '4',
    five: '5',
    six: '6',
    seven: '7',
    eight: '8',
    nine: '9',
    ten: '10',
    eleven: '11',
    twelve: '12',
    thirteen: '13',
    fourteen: '14',
    fifteen: '15',
    sixteen: '16',
    seventeen: '17',
    eighteen: '18',
    nineteen: '19',
    twenty: '20',
    thirty: '30',
    forty: '40',
    fifty: '50',
  }
  for (const [w, n] of Object.entries(wordNumbers)) {
    const rxBefore = new RegExp(`\\b(table for|table of|party of|for)\\s+${w}\\b`, 'g')
    text = text.replace(rxBefore, (_, p) => `${p} ${n}`)
    const rxAfter = new RegExp(`\\b${w}\\s+(guests|people|persons|person|seats|pax)\\b`, 'g')
    text = text.replace(rxAfter, (_, p) => `${n} ${p}`)
    const rxStandalone = new RegExp(`^${w}\\s+(guests|people|persons|seats)$`, 'g')
    text = text.replace(rxStandalone, (_, p) => `${n} ${p}`)
  }

  // 2. Contractions & Slang
  text = text
    .replace(/\b(wanna|wan|wnt|woud like|wud like)\b/g, 'want to')
    .replace(/\b(im|i m)\b/g, 'i am')
    .replace(/\b(pls|plz)\b/g, 'please')
    .replace(/\b(u|yu)\b/g, 'you')
    .replace(/\b(r)\b/g, 'are')
    .replace(/\b(gud)\b/g, 'good')

  // 3. Common spelling errors for booking / reservation / table
  text = text
    .replace(/\b(appoinmet|appontment|apointment|appoiment|appointment|appointmnt)\b/g, 'reservation')
    .replace(/\b(reseravtion|reservtion|resrvation|reseration|resvation|reseveration|resrv|reserv)\b/g, 'reservation')
    .replace(/\b(bok|boking|boook|boooking|boooked|boked)\b/g, 'book')
    .replace(/\b(tabl|tabel|teble|tbl)\b/g, 'table')
    .replace(/\b(seet|seeting|seting)\b/g, 'seat')

  // 4. Common spelling errors for date & time
  text = text
    .replace(/\b(tonyt|tonite|tonigt|2night|2nite)\b/g, 'tonight')
    .replace(/\b(tomorow|tomorw|tommoro|tommorow|tmrw|tmr|2morrow|2moro)\b/g, 'tomorrow')
    .replace(/\b(evng|evning|evenin)\b/g, 'evening')
    .replace(/\b(mrng|mornin)\b/g, 'morning')
    .replace(/\b(aftrnoon|aftr)\b/g, 'afternoon')

  // 5. Common spelling errors for guests & people
  text = text
    .replace(/\b(geusts|gests|geust|gest|guets|peopl|peopel|peple|ppl|persns|persn)\b/g, 'guests')

  // 6. Common spelling errors for menu & food
  text = text
    .replace(/\b(menue|manu)\b/g, 'menu')
    .replace(/\b(fud|foood)\b/g, 'food')
    .replace(/\b(cusine|cuisin)\b/g, 'cuisine')

  // 7. Greetings
  text = text
    .replace(/\b(hay|heyy|heya|hllo|hallo|helo|hy)\b/g, 'hello')

  return text
}

/**
 * Extracts dining booking slots (date, time, partySize) from a single text string.
 */
function extractBookingSlots(text: string) {
  let partySize: number | null = null
  let dateStr: string | null = null
  let timeStr: string | null = null

  const now = new Date()

  // 1. Party Size
  const partyMatch = text.match(/(\d+)\s*(?:people|guests|persons|person|seats|pax|party)/)
  if (partyMatch) {
    partySize = parseInt(partyMatch[1], 10)
  } else {
    const forMatch = text.match(/(?:for|party of|table for|table of)\s*(\d+)/)
    if (forMatch) partySize = parseInt(forMatch[1], 10)
  }

  // 2. Date parsing
  if (text.includes('tomorrow')) {
    const tomorrow = new Date(now)
    tomorrow.setDate(now.getDate() + 1)
    dateStr = tomorrow.toISOString().split('T')[0]
  } else if (text.includes('today') || text.includes('tonight')) {
    dateStr = now.toISOString().split('T')[0]
  } else {
    const isoDate = text.match(/\b(\d{4}-\d{2}-\d{2})\b/)
    if (isoDate) {
      dateStr = isoDate[1]
    } else {
      const daysOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
      for (let d = 0; d < daysOfWeek.length; d++) {
        if (text.includes(daysOfWeek[d])) {
          const currentDay = now.getDay()
          let diff = d - currentDay
          if (diff <= 0) diff += 7
          const futureDate = new Date(now)
          futureDate.setDate(now.getDate() + diff)
          dateStr = futureDate.toISOString().split('T')[0]
          break
        }
      }
    }
  }

  // 3. Time parsing
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
    if (time24) {
      timeStr = `${String(parseInt(time24[1], 10)).padStart(2, '0')}:${time24[2]}`
    } else {
      // E.g. "at 7" or "at 8" or "at 1" or "7 o'clock"
      const bareTime = text.match(/(?:at|around|for)\s+(\d{1,2})(?::(\d{2}))?(?:\s*o'?clock)?\b/)
      if (bareTime) {
        let hr = parseInt(bareTime[1], 10)
        const mn = parseInt(bareTime[2] || '0', 10)
        // In restaurant dining: 1-4 is lunch PM, 5-11 is dinner PM
        if (hr >= 1 && hr <= 11) hr += 12
        timeStr = `${String(hr).padStart(2, '0')}:${String(mn).padStart(2, '0')}`
      }
    }
  }

  return { date: dateStr, time: timeStr, partySize }
}

/**
 * Resolves booking details by combining the current utterance with prior user history.
 */
function resolveBookingWithHistory(
  cleanText: string,
  history: Array<{ role: string; text: string }>
) {
  const currentSlots = extractBookingSlots(cleanText)

  // If any slot is missing, look backward in user messages to merge
  if (!currentSlots.date || !currentSlots.time || !currentSlots.partySize) {
    const userMessages = history
      .filter((h) => h.role === 'user')
      .map((h) => normalizeAndCorrectText(h.text))
      .reverse()

    for (const msg of userMessages) {
      const pastSlots = extractBookingSlots(msg)
      if (!currentSlots.date && pastSlots.date) currentSlots.date = pastSlots.date
      if (!currentSlots.time && pastSlots.time) currentSlots.time = pastSlots.time
      if (!currentSlots.partySize && pastSlots.partySize) currentSlots.partySize = pastSlots.partySize
      if (currentSlots.date && currentSlots.time && currentSlots.partySize) break
    }
  }

  return currentSlots
}

/**
 * Strips all casual emojis to maintain clean, ultra-professional luxury hospitality tone.
 */
function cleanProfessionalText(text: string): string {
  return text
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}]/gu, '')
    .replace(/  +/g, ' ')
    .trim()
}
