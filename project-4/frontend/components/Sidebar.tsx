interface Metrics {
  sessionId: string
  uptime: string
  turns: number
  sttAvg: number
  supervisorAvg: number
  ttsAvg: number
}

interface SidebarProps {
  metrics: Metrics
  onClearChat: () => void
}

export default function Sidebar({ metrics, onClearChat }: SidebarProps) {
  return (
    <div className="w-72 bg-slate-900/50 backdrop-blur-md border-r border-slate-700/50 p-6 overflow-y-auto flex-shrink-0">
      <div className="text-xl font-bold mb-6 text-white">🎤 Voice Agent</div>

      {/* Session Info */}
      <div className="mb-6">
        <h3 className="text-xs font-bold uppercase tracking-wider text-pink-500 mb-3">
          Session Info
        </h3>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between text-slate-400">
            <span>ID</span>
            <span className="font-mono text-slate-200">{metrics.sessionId ? metrics.sessionId.slice(0, 8) : '--------'}</span>
          </div>
          <div className="flex justify-between text-slate-400 border-t border-slate-700/30 pt-2">
            <span>Uptime</span>
            <span className="font-mono text-slate-200">{metrics.uptime}</span>
          </div>
        </div>
      </div>

      {/* Performance */}
      <div className="mb-6">
        <h3 className="text-xs font-bold uppercase tracking-wider text-pink-500 mb-3">
          Performance
        </h3>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between text-slate-400">
            <span>Turns</span>
            <span className="font-mono text-slate-200">{metrics.turns}</span>
          </div>
          <div className="flex justify-between text-slate-400 border-t border-slate-700/30 pt-2">
            <span>STT avg</span>
            <span className="font-mono text-slate-200">{metrics.sttAvg}ms</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Supervisor avg</span>
            <span className="font-mono text-slate-200">{metrics.supervisorAvg}ms</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>TTS avg</span>
            <span className="font-mono text-slate-200">{metrics.ttsAvg}ms</span>
          </div>
        </div>
      </div>

      {/* Clear Button */}
      <button
        onClick={onClearChat}
        className="w-full bg-gradient-to-r from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95 text-sm"
      >
        🗑️ Clear Chat
      </button>
    </div>
  )
}
