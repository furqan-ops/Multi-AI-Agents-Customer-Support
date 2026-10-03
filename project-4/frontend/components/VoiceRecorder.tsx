'use client'

import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react'

export interface VoiceRecorderHandle {
  startRecording: () => void
  stopRecording: () => void
  cancelRecording: () => void
}

interface VoiceRecorderProps {
  isRecording: boolean
  isProcessing: boolean
  onRecordingComplete: (audioBlob: Blob, transcript: string) => Promise<void>
  onRecordingStart: () => void
  onRecordingStop: () => void
  onRecordingCancel?: () => void
  onRecordingError?: (message: string) => void
}

const VoiceRecorder = forwardRef<VoiceRecorderHandle, VoiceRecorderProps>(function VoiceRecorder(
  {
    isRecording,
    isProcessing,
    onRecordingComplete,
    onRecordingStart,
    onRecordingStop,
    onRecordingCancel,
    onRecordingError,
  },
  ref
) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const [error, setError] = useState<string>('')
  const [recordSeconds, setRecordSeconds] = useState<number>(0)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const isCanceledRef = useRef<boolean>(false)

  // Recording duration timer
  useEffect(() => {
    if (isRecording) {
      setRecordSeconds(0)
      timerRef.current = setInterval(() => {
        setRecordSeconds((s) => s + 1)
      }, 1000)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
      setRecordSeconds(0)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isRecording])

  const startRecording = async () => {
    try {
      setError('')
      isCanceledRef.current = false

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      let mimeType = 'audio/webm'
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4'
        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
          mimeType = 'audio/ogg'
        }
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop())
          streamRef.current = null
        }

        if (isCanceledRef.current) {
          isCanceledRef.current = false
          if (onRecordingCancel) onRecordingCancel()
          return
        }

        const audioBlob = new Blob(chunksRef.current, { type: mimeType })
        if (audioBlob.size === 0) {
          setError('No audio captured. Please try speaking again.')
          if (onRecordingError) onRecordingError('No audio captured')
          return
        }

        try {
          const sttResponse = await fetch('/api/stt', {
            method: 'POST',
            body: audioBlob,
            headers: {
              'Content-Type': mimeType,
            },
          })

          if (!sttResponse.ok) {
            throw new Error(`STT server returned status ${sttResponse.status}`)
          }

          const sttData = await sttResponse.json()
          const transcript = sttData.transcript ? sttData.transcript.trim() : ''

          if (!transcript) {
            setError('No speech detected. Please speak clearly into your microphone.')
            if (onRecordingError) onRecordingError('No speech detected')
            return
          }

          setError('')
          await onRecordingComplete(audioBlob, transcript)
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Transcription failed'
          setError(`Transcription: ${msg}. You can also type your message in the chat.`)
          console.error('STT error:', err)
          if (onRecordingError) onRecordingError(msg)
        }
      }

      mediaRecorder.start(250)
      onRecordingStart()
    } catch (err) {
      console.error('Microphone error:', err)
      setError('Microphone access was denied or not available.')
      if (onRecordingError) onRecordingError('Microphone access denied')
    }
  }

  const stopRecording = () => {
    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        isCanceledRef.current = false
        if (mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.requestData()
        }
        mediaRecorderRef.current.stop()
      }
      onRecordingStop()
    } catch (err) {
      console.error('Error stopping recording:', err)
      onRecordingStop()
    }
  }

  const cancelRecording = () => {
    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        isCanceledRef.current = true
        mediaRecorderRef.current.stop()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
      if (onRecordingCancel) onRecordingCancel()
    } catch (err) {
      console.error('Error canceling recording:', err)
      if (onRecordingCancel) onRecordingCancel()
    }
  }

  useImperativeHandle(ref, () => ({
    startRecording,
    stopRecording,
    cancelRecording,
  }))

  const formatTimer = (sec: number) => {
    const mins = Math.floor(sec / 60)
    const secs = sec % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Action Buttons: Clean SVG Icons & Neutral Styling */}
      <div className="flex items-center gap-2.5">
        {!isRecording ? (
          <button
            type="button"
            onClick={startRecording}
            disabled={isProcessing}
            title="Start voice recording"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-50 to-violet-50 dark:from-indigo-950/40 dark:to-violet-950/40 hover:from-indigo-100 hover:to-violet-100 dark:hover:from-indigo-900/60 dark:hover:to-violet-900/60 border border-indigo-200/70 dark:border-indigo-800/60 text-indigo-700 dark:text-indigo-300 text-xs font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm active:scale-95"
          >
            <svg className="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
            </svg>
            <span>Start Voice</span>
          </button>
        ) : (
          <>
            <button
              type="button"
              onClick={stopRecording}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-rose-500 to-red-600 text-white border border-rose-400/40 text-xs font-medium shadow-md shadow-rose-500/25 transition-all hover:brightness-105 active:scale-95"
            >
              <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
              <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                <rect x="5" y="5" width="14" height="14" rx="2" />
              </svg>
              <span>Stop Recording ({formatTimer(recordSeconds)})</span>
            </button>
            <button
              type="button"
              onClick={cancelRecording}
              className="px-3 py-2 rounded-xl bg-white dark:bg-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-700 border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 text-xs transition-colors shadow-sm"
            >
              Cancel
            </button>
          </>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/40 px-3 py-1.5 rounded-lg text-center max-w-sm">
          {error}
        </div>
      )}
    </div>
  )
})

export default VoiceRecorder
