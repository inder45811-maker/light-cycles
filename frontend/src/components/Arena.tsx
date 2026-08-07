import { useState } from 'react'

interface Battle {
  id: string
  title: string
  description: string
  status: string
  winner: string | null
  agents: Array<{
    name: string
    model: string
    status: string
    error?: string | null
    score: { score: number; tests_passed: number; tests_total: number; duration_ms: number; errors: string[] } | null
  }>
  scores: Array<{ agent: string; score: number; passed: number; total: number; duration_ms: number }>
}

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
    } catch (e) {
      console.error('Submit failed', e)
    }
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
          const isWinner = battle.winner === agent.name
          const code = codeInputs[agent.name] || ''

          return (
            <div key={agent.name} className={`arena-panel ${isWinner ? 'winner' : ''}`}>
              <div className="arena-agent-name">
                {isWinner && '⏣ '}{agent.name}
                <span style={{ marginLeft: 12, fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                  {agent.model}
                </span>
              </div>

              {/* Score display */}
              {agent.score && (
                <div style={{ marginBottom: 16 }}>
                  <div className={`score-badge ${isWinner ? 'win' : 'loss'}`}>
                    {agent.score.score}
                  </div>
                  <div className="score-detail" style={{ marginTop: 4 }}>
                    {agent.score.tests_passed}/{agent.score.tests_total} tests · {agent.score.duration_ms.toFixed(0)}ms
                  </div>
                  {agent.score.errors.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      {agent.score.errors.map((e, i) => (
                        <div key={i} style={{ color: 'var(--red)', fontSize: 11, marginTop: 4 }}>✕ {e}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Code submission form — only for non-complete battles */}
              {battle.status !== 'complete' && (
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
              )}

              {/* Submitted code display */}
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
          )
        })}

        {/* Verdict panel */}
        {battle.status === 'complete' && (
          <div className="arena-panel full">
            <div className="arena-verdict">
              <div className="arena-verdict-title">
                {battle.winner} WINS
              </div>
              <div className="arena-verdict-sub">The Grid recognizes a new champion</div>

              <div style={{ display: 'flex', justifyContent: 'center', gap: 48, marginTop: 24 }}>
                {battle.scores.map(s => (
                  <div key={s.agent} style={{ textAlign: 'center' }}>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 900,
                      color: s.score === maxScore ? 'var(--cyan-bright)' : 'var(--text-dim)',
                      textShadow: s.score === maxScore ? 'var(--glow-cyan)' : 'none' }}>
                      {s.score}
                    </div>
                    <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>{s.agent}</div>
                    <div style={{ color: 'var(--text-dim)', fontSize: 10 }}>
                      {s.passed}/{s.total} · {s.duration_ms.toFixed(0)}ms
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Force judge button */}
      {battle.status === 'waiting' && (
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <button
            className="btn btn-orange btn-sm"
            onClick={async () => {
              await fetch(`/api/battles/${battle.id}/judge`, { method: 'POST' })
              onRefresh()
            }}
          >
            Force Judge
          </button>
        </div>
      )}
    </>
  )
}
