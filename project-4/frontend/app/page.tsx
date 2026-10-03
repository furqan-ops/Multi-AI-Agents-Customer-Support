'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import ChatHistory, { Message } from '@/components/ChatHistory'
import VoiceRecorder, { VoiceRecorderHandle } from '@/components/VoiceRecorder'
import ChatInput from '@/components/ChatInput'

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [audioRepliesEnabled, setAudioRepliesEnabled] = useState<boolean>(true)
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')

  const recorderRef = useRef<VoiceRecorderHandle>(null)

  useEffect(() => {
    setSessionId(generateUUID())
    const savedTheme = (localStorage.getItem('theme') as 'dark' | 'light') || 'dark'
    setTheme(savedTheme)
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark')
      document.documentElement.classList.remove('light')
    } else {
      document.documentElement.classList.remove('dark')
      document.documentElement.classList.add('light')
    }
  }, [])

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    localStorage.setItem('theme', nextTheme)
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark')
      document.documentElement.classList.remove('light')
    } else {
      document.documentElement.classList.remove('dark')
      document.documentElement.classList.add('light')
    }
  }

  // Unified message sender (handles typed text and transcribed voice)
  const sendUserQuery = useCallback(
    async (text: string, audioBlob?: Blob) => {
      if (!text.trim() || isProcessing) return
      setIsProcessing(true)

      const startTime = Date.now()

      // Add user message
      const userMessage: Message = {
        id: generateUUID(),
        role: 'user',
        text: text.trim(),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])

      let agentResponseText = 'No response received.'

      try {
        const supervisorResponse = await fetch('/api/supervisor', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Id': sessionId || 'client',
          },
          body: JSON.stringify({
            text: text.trim(),
            sessionId: sessionId || 'client',
          }),
        })

        const supervisorData = await supervisorResponse.json()
        agentResponseText = supervisorData.response || agentResponseText
      } catch (supErr) {
        console.warn('Supervisor request warning:', supErr)
        agentResponseText =
          'Unable to reach the supervisor agent. Please check that the backend server is active.'
      }

      // Synthesize audio speech if audio replies enabled
      let audioUrl: string | undefined = undefined
      if (audioRepliesEnabled) {
        try {
          const ttsResponse = await fetch('/api/tts', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              text: agentResponseText,
            }),
          })

          if (ttsResponse.ok) {
            const audioBuffer = await ttsResponse.arrayBuffer()
            const audioBlob = new Blob([audioBuffer], { type: 'audio/mpeg' })
            audioUrl = URL.createObjectURL(audioBlob)
          }
        } catch (ttsErr) {
          console.warn('TTS synthesis warning:', ttsErr)
        }
      }

      // Add agent reply
      const agentMessage: Message = {
        id: generateUUID(),
        role: 'agent',
        text: agentResponseText,
        timestamp: new Date(),
        audioUrl,
      }
      setMessages((prev) => [...prev, agentMessage])

      // Auto-play audio response if enabled
      if (audioRepliesEnabled) {
        if (audioUrl) {
          try {
            const audio = new Audio(audioUrl)
            await audio.play()
          } catch (playErr) {
            console.warn('Audio auto-play prevented:', playErr)
          }
        } else if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
          try {
            window.speechSynthesis.cancel()
            const utterance = new SpeechSynthesisUtterance(agentResponseText)
            utterance.rate = 1.0
            utterance.pitch = 1.0
            window.speechSynthesis.speak(utterance)
          } catch (synthErr) {
            console.warn('Speech synthesis error:', synthErr)
          }
        }
      }

      setIsProcessing(false)
    },
    [isProcessing, sessionId, audioRepliesEnabled]
  )

  const handleRecordingStart = () => {
    setIsRecording(true)
    setIsProcessing(false)
  }

  const handleRecordingStop = () => {
    setIsRecording(false)
    setIsProcessing(true)
  }

  const handleRecordingCancel = () => {
    setIsRecording(false)
    setIsProcessing(false)
  }

  const handleRecordingError = () => {
    setIsRecording(false)
    setIsProcessing(false)
  }

  const handleRecordingComplete = async (audioBlob: Blob, transcript: string) => {
    setIsRecording(false)
    await sendUserQuery(transcript, audioBlob)
  }

  const handleToggleVoice = () => {
    if (isProcessing) return
    if (isRecording) {
      recorderRef.current?.stopRecording()
    } else {
      recorderRef.current?.startRecording()
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  const quickPrompts = [
    {
      title: 'Book a Table',
      category: 'Reservation',
      query: 'I would like to book a table for 2 people tomorrow at 7 PM',
      badgeClass: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20',
      hoverClass: 'hover:border-emerald-500/50 hover:bg-emerald-500/[0.03]',
      iconColor: 'text-emerald-500',
    },
    {
      title: 'Check Booking Status',
      category: 'Status',
      query: 'Did my order or booking get confirmed?',
      badgeClass: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20',
      hoverClass: 'hover:border-sky-500/50 hover:bg-sky-500/[0.03]',
      iconColor: 'text-sky-500',
    },
    {
      title: 'Opening Hours',
      category: 'Hours',
      query: 'What are your opening hours and support schedule?',
      badgeClass: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20',
      hoverClass: 'hover:border-amber-500/50 hover:bg-amber-500/[0.03]',
      iconColor: 'text-amber-500',
    },
    {
      title: 'Refund Policy',
      category: 'Policy',
      query: 'What is your refund policy?',
      badgeClass: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20',
      hoverClass: 'hover:border-purple-500/50 hover:bg-purple-500/[0.03]',
      iconColor: 'text-purple-500',
    },
  ]

  return (
    <div className="flex flex-col h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 overflow-hidden font-sans transition-colors duration-200">
      {/* Clean Top Navigation Bar (Claude / ChatGPT style) */}
      <header className="w-full border-b border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90 backdrop-blur px-6 py-3 flex items-center justify-between z-10 transition-colors">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/25 ring-2 ring-indigo-500/20">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.75}
                d="M18.375 12.739l-7.648 7.648a4.5 4.5 0 01-6.364-6.364l7.648-7.648a3 3 0 014.243 4.243L8.606 18.266a1.5 1.5 0 01-2.121-2.121l7.648-7.648"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">
              Customer Support &amp; Booking Agent
            </h1>
            <div className="flex items-center gap-1.5 text-[11px] text-zinc-500 dark:text-zinc-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span>Online &bull; Ready to assist</span>
            </div>
          </div>
        </div>

        {/* Header Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Dark / Light Mode Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="flex items-center justify-center w-8 h-8 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-750 transition-all shadow-sm"
          >
            {theme === 'dark' ? (
              <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"
                />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"
                />
              </svg>
            )}
          </button>

          {/* Voice Response Toggle */}
          <button
            type="button"
            onClick={() => setAudioRepliesEnabled(!audioRepliesEnabled)}
            title={audioRepliesEnabled ? 'Voice responses enabled' : 'Voice responses muted'}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all shadow-sm ${
              audioRepliesEnabled
                ? 'bg-zinc-100 dark:bg-zinc-800 border-zinc-300 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 hover:bg-zinc-200 dark:hover:bg-zinc-750'
                : 'bg-transparent border-zinc-200 dark:border-zinc-800 text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {audioRepliesEnabled ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.757 3.63 8.25 4.51 8.25H6.75z"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M17.25 9.75L19.5 12m0 0l2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-1.5l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.757 3.63 8.25 4.51 8.25H6.75z"
                />
              )}
            </svg>
            <span className="hidden sm:inline">
              {audioRepliesEnabled ? 'Voice On' : 'Voice Muted'}
            </span>
          </button>

          {/* Clear Chat Button */}
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearChat}
              title="Clear chat history"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 text-xs font-medium transition-all shadow-sm"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                />
              </svg>
              <span>Clear</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Chat Canvas */}
      <main className="relative flex-1 overflow-y-auto flex flex-col items-center px-4">
        {/* Subtle Ambient Background Glows */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[480px] h-[260px] bg-gradient-to-tr from-indigo-500/10 via-violet-500/10 to-teal-500/10 blur-3xl rounded-full" />
        </div>

        <div className="relative w-full max-w-2xl flex-1 flex flex-col justify-between py-6">
          {/* Welcome Screen when Empty */}
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center my-auto py-8 animate-fade-in">
              {/* Jewel Gradient Border Icon */}
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-teal-400 p-[1.5px] shadow-lg shadow-indigo-500/15 mb-4">
                <div className="w-full h-full bg-white dark:bg-zinc-900 rounded-[14px] flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                  <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
                    />
                  </svg>
                </div>
              </div>

              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 mb-1">
                How may I assist you today?
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 max-w-md mb-8">
                I can help you reserve a table, look up your existing booking, or answer questions
                about opening hours and refund policies.
              </p>

              {/* Quick Prompt Cards with Color Badges */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                {quickPrompts.map((p) => (
                  <button
                    key={p.title}
                    type="button"
                    onClick={() => sendUserQuery(p.query)}
                    className={`p-3.5 text-left rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 transition-all text-xs group shadow-sm ${p.hoverClass}`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <div className="font-semibold text-zinc-900 dark:text-zinc-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        {p.title}
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${p.badgeClass}`}>
                        {p.category}
                      </span>
                    </div>
                    <div className="text-[11px] text-zinc-500 dark:text-zinc-400 line-clamp-1">{p.query}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <ChatHistory messages={messages} isThinking={isProcessing} />
          )}

          {/* Active Voice Bar (Appears when recording or when voice option is open) */}
          <div className="mt-4 mb-2 flex flex-col items-center">
            <VoiceRecorder
              ref={recorderRef}
              isRecording={isRecording}
              isProcessing={isProcessing}
              onRecordingComplete={handleRecordingComplete}
              onRecordingStart={handleRecordingStart}
              onRecordingStop={handleRecordingStop}
              onRecordingCancel={handleRecordingCancel}
              onRecordingError={handleRecordingError}
            />
          </div>
        </div>
      </main>

      {/* Floating Bottom Input Bar */}
      <footer className="w-full border-t border-zinc-200 dark:border-zinc-800/80 bg-white/95 dark:bg-zinc-900/95 backdrop-blur px-4 py-3 flex justify-center z-10 transition-colors">
        <div className="w-full max-w-2xl">
          <ChatInput
            onSendMessage={(text) => sendUserQuery(text)}
            disabled={isRecording || isProcessing}
            isRecording={isRecording}
            onToggleVoice={handleToggleVoice}
          />
          <div className="text-[11px] text-zinc-400 dark:text-zinc-500 text-center mt-2">
            Nexio24 Customer Support &bull; Multi-agent AI system
          </div>
        </div>
      </footer>
    </div>
  )
}

function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}
