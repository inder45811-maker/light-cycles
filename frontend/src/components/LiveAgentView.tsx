import { useState, useEffect } from 'react'
import type { AgentScore } from '../types'

interface Props {
  agentName: string
  status: string
  code?: string
  score?: AgentScore | null
}

export default function LiveAgentView({ agentName, status, code, score }: Props) {
  const [displayedCode, setDisplayedCode] = useState('')
  const [cursor, setCursor] = useState(true)

  useEffect(() => {
    if (!code || status === 'waiting') return
    let i = 0
    const interval = setInterval(() => {
      setDisplayedCode(code.slice(0, i))
      i += 4
      if (i >= code.length) { setDisplayedCode(code); clearInterval(interval) }
    }, 15)
    return () => clearInterval(interval)
  }, [code, status])

  useEffect(() => {
    const interval = setInterval(() => setCursor(c => !c), 530)
    return () => clearInterval(interval)
  }, [])

  const isTyping = status === 'coding' || (status === 'submitted' && displayedCode !== code)

  return (
    <div className={`arena-panel ${score ? 'winner' : ''}`}>
      <div className="arena-agent-name">
        {score ? '⏣ ' : ''}{agentName}
        {status !== 'waiting' && status !== 'complete' && (
          <span className={`status-dot ${status}`} style={{ marginLeft: 8 }} />
        )}
      </div>

      <div className="arena-code" style={{ maxHeight: 300 }}>
        <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.6 }}>
          {displayedCode || (status === 'waiting' ? '// Awaiting agent...' : '')}
          {isTyping && displayedCode && displayedCode !== code && (
            <span style={{
              display: 'inline-block', width: 2, height: 14,
              background: cursor ? 'var(--cyan)' : 'transparent',
              verticalAlign: 'middle', marginLeft: 1,
            }} />
          )}
        </pre>
      </div>

      {score && (
        <div style={{ marginTop: 12 }}>
          <div className="score-badge win">{score.score}</div>
          <div className="score-detail">
            {score.tests_passed}/{score.tests_total} tests · {score.duration_ms.toFixed(0)}ms
          </div>
          {score.errors.length > 0 && score.errors.map((e, i) => (
            <div key={i} style={{ color: 'var(--red)', fontSize: 10, marginTop: 2 }}>✕ {e}</div>
          ))}
        </div>
      )}

      {status === 'submitted' && !score && (
        <div style={{ color: 'var(--cyan)', fontSize: 12, marginTop: 8 }}>◉ Awaiting opponent...</div>
      )}
    </div>
  )
}
