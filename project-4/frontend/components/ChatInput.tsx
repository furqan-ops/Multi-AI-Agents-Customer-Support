'use client'

import { useState, FormEvent, KeyboardEvent } from 'react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  isRecording?: boolean
  onToggleVoice?: () => void
}

export default function ChatInput({
  onSendMessage,
  disabled,
  isRecording,
  onToggleVoice,
}: ChatInputProps) {
  const [text, setText] = useState('')

  const handleSubmit = (e?: FormEvent) => {
    if (e) e.preventDefault()
    if (!text.trim() || disabled) return
    onSendMessage(text.trim())
    setText('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative flex items-center bg-white dark:bg-zinc-800/95 border border-zinc-200 dark:border-zinc-700/80 rounded-2xl p-1.5 shadow-sm focus-within:border-indigo-500/80 dark:focus-within:border-indigo-400/80 focus-within:ring-2 focus-within:ring-indigo-500/15 transition-all">
        {/* Integrated Voice Microphone Trigger */}
        {onToggleVoice && (
          <button
            type="button"
            onClick={onToggleVoice}
            disabled={disabled && !isRecording}
            title={isRecording ? 'Stop voice recording' : 'Speak with microphone'}
            className={`flex items-center justify-center w-9 h-9 rounded-xl transition-all mr-1 ${
              isRecording
                ? 'bg-rose-500 text-white shadow-md shadow-rose-500/30 ring-2 ring-rose-500/30 animate-pulse'
                : 'text-zinc-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40'
            }`}
          >
            {isRecording ? (
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"
                />
              </svg>
            )}
          </button>
        )}

        {/* Text Input */}
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isRecording
              ? 'Listening to your voice...'
              : 'Ask a question or type a message...'
          }
          disabled={disabled || isRecording}
          className="flex-1 bg-transparent px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none disabled:opacity-50"
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={disabled || !text.trim() || isRecording}
          title="Send message"
          className="flex items-center justify-center w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-md shadow-indigo-500/25 disabled:opacity-30 disabled:pointer-events-none transition-all transform active:scale-95 flex-shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"
            />
          </svg>
        </button>
      </div>
    </form>
  )
}
