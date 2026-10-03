'use client'

import { useEffect, useRef } from 'react'

export interface Message {
  id: string
  role: 'user' | 'agent'
  text: string
  timestamp: Date
  audioUrl?: string
}

interface ChatHistoryProps {
  messages: Message[]
  isThinking?: boolean
}

export default function ChatHistory({ messages, isThinking }: ChatHistoryProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  return (
    <div className="w-full flex flex-col gap-5 py-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex gap-3 ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          } animate-slide-in`}
        >
          {/* Agent Avatar */}
          {message.role === 'agent' && (
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/25 flex items-center justify-center flex-shrink-0 mt-0.5 ring-2 ring-emerald-500/20">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"
                />
              </svg>
            </div>
          )}

          {/* Message Content Bubble */}
          <div
            className={`max-w-[85%] sm:max-w-xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
              message.role === 'user'
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-500/20 rounded-2xl rounded-tr-xs'
                : 'bg-white text-zinc-800 border border-zinc-200/90 dark:bg-zinc-900/90 dark:text-zinc-100 dark:border-zinc-800/90 rounded-2xl rounded-tl-xs'
            }`}
          >
            {/* Agent Header Badge */}
            {message.role === 'agent' && (
              <div className="flex items-center gap-1.5 mb-2 pb-1.5 border-b border-zinc-100 dark:border-zinc-800/80 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span>Customer Support Agent</span>
              </div>
            )}

            <div className="whitespace-pre-wrap">{message.text}</div>

            {/* Inline Audio Player if Agent Speech is Available */}
            {message.audioUrl && message.role === 'agent' && (
              <div className="mt-3 pt-2.5 border-t border-zinc-100 dark:border-zinc-800 flex items-center gap-2">
                <svg className="w-4 h-4 text-zinc-400 dark:text-zinc-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.757 3.63 8.25 4.51 8.25H6.75z" />
                </svg>
                <audio controls className="w-full h-7 text-xs bg-zinc-100 dark:bg-zinc-800 rounded" src={message.audioUrl} />
              </div>
            )}

            <div
              className={`text-[10px] mt-1.5 text-right font-mono ${
                message.role === 'user'
                  ? 'text-indigo-200'
                  : 'text-zinc-400 dark:text-zinc-500'
              }`}
            >
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
          </div>

          {/* User Avatar */}
          {message.role === 'user' && (
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-500/25 flex items-center justify-center flex-shrink-0 mt-0.5 ring-2 ring-indigo-500/20">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
            </div>
          )}
        </div>
      ))}

      {/* Agent Thinking / Typing Indicator */}
      {isThinking && (
        <div className="flex items-center gap-3 py-1 animate-fade-in pl-0.5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 flex-shrink-0 shadow-sm">
            <svg className="w-4 h-4 animate-spin text-emerald-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
            </svg>
          </div>
          <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white dark:bg-zinc-900 border border-emerald-500/20 dark:border-emerald-500/20 text-xs text-zinc-700 dark:text-zinc-200 shadow-sm">
            <span className="font-medium tracking-wide">Agent is typing</span>
            <span className="inline-flex gap-1 items-center ml-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse [animation-delay:200ms]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse [animation-delay:400ms]"></span>
            </span>
          </div>
        </div>
      )}

      <div ref={endRef} />
    </div>
  )
}
