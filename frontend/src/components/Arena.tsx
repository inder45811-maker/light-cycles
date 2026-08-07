import { useState } from 'react'
import type { Battle } from '../types'
import LiveAgentView from './LiveAgentView'

interface Props {
  battle: Battle
  onBack: () => void
  onRefresh: () => void
}

export default function Arena({ battle, onBack, onRefresh }: Props) {
  const [codeInputs, setCodeInputs] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({})

  const handleSubmit = async (agentName: string) => {
    const code = codeInputs[agentName]
    if (!code) return
    setSubmitting(s => ({ ...s, [agentName]: true }))
    try {
      await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ battle_id: battle.id, agent_name: agentName, code }),
      })
      onRefresh()
    } catch { /* toast handles it */ }
    setSubmitting(s => ({ ...s, [agentName]: false }))
  }

  const maxScore = battle.scores.length > 0
    ? Math.max(...battle.scores.map(s => s.score))
    : 0

  return (
    <>
      <div style={{ marginBottom: 20 }}>
        <button className="btn btn-sm" onClick={onBack}>← Back to Arena</button>
      </div>

      <h2 className="section-title">{battle.title}</h2>
      <p style={{ color: 'var(--text-dim)', marginBottom: 24 }}>{battle.description}</p>

      <div className={`battle-card-status status-${battle.status}`} style={{ marginBottom: 24 }}>
        <span className={`status-dot ${battle.status}`} />
        {battle.status.toUpperCase()}
        {battle.winner && (
          <span style={{ marginLeft: 16, color: 'var(--cyan-bright)' }}>
            ⏣ WINNER: {battle.winner}
          </span>
        )}
      </div>

      <div className="arena">
        {battle.agents.map(agent => {
          const code = codeInputs[agent.name] || ''
          const isComplete = battle.status === 'complete'

          return (
            <div key={agent.name}>
              {isComplete ? (
                <LiveAgentView
                  agentName={agent.name}
                  status="complete"
                  code={agent.code || ''}
                  score={agent.score}
                />
              ) : (
                <div className="arena-panel">
                  <div className="arena-agent-name">
                    {agent.name}
                    <span style={{ marginLeft: 12, fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {agent.model}
                    </span>
                  </div>

                  {agent.score && (
                    <div style={{ marginBottom: 16 }}>
                      <div className="score-badge win">{agent.score.score}</div>
                      <div className="score-detail">
                        {agent.score.tests_passed}/{agent.score.tests_total} tests · {agent.score.duration_ms.toFixed(0)}ms
                      </div>
                    </div>
                  )}

                  <div className="submission-area">
                    <label className="form-label">Agent Code Submission</label>
                    <textarea
                      className="submission-textarea"
                      value={code}
                      onChange={e => setCodeInputs(s => ({ ...s, [agent.name]: e.target.value }))}
                      placeholder={`def solution(input):\n    # ${agent.name}'s code here\n    pass`}
                      spellCheck={false}
                    />
                    <div className="btn-group">
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleSubmit(agent.name)}
                        disabled={!code || submitting[agent.name]}
                      >
                        {submitting[agent.name] ? 'SUBMITTING...' : 'SUBMIT CODE'}
                      </button>
                    </div>
                  </div>

                  {agent.status === 'submitted' && !agent.score && (
                    <div style={{ color: 'var(--cyan)', fontSize: 12, marginTop: 12 }}>
                      ◉ Code submitted — awaiting opponent
                    </div>
                  )}
                  {agent.error && (
                    <div style={{ color: 'var(--red)', fontSize: 12, marginTop: 12 }}>
                      ✕ {agent.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {battle.status === 'complete' && (
          <div className="arena-panel full">
            <div className="arena-verdict">
              <div className="arena-verdict-title">{battle.winner} WINS</div>
              <div className="arena-verdict-sub">The Grid recognizes a new champion</div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 48, marginTop: 24 }}>
                {battle.scores.map(s => (
                  <div key={s.agent} style={{ textAlign: 'center' }}>
                    <div style={{
                      fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 900,
                      color: s.score === maxScore ? 'var(--cyan-bright)' : 'var(--text-dim)',
                      textShadow: s.score === maxScore ? 'var(--glow-cyan)' : 'none',
                    }}>{s.score}</div>
                    <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>{s.agent}</div>
                    <div style={{ color: 'var(--text-dim)', fontSize: 10 }}>{s.passed}/{s.total} · {s.duration_ms.toFixed(0)}ms</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
