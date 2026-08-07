import { useState, useEffect } from 'react'
import type { Debate } from '../types'
import { api } from '../lib/api'

export default function DebateArena() {
  const [debates, setDebates] = useState<Debate[]>([])
  const [selected, setSelected] = useState<Debate | null>(null)
  const [topic, setTopic] = useState('')
  const [agentFor, setAgentFor] = useState('TRON')
  const [agentAgainst, setAgentAgainst] = useState('CLU')
  const [creating, setCreating] = useState(false)

  const fetchDebates = async () => {
    try { setDebates(await api.get<Debate[]>('/api/debates')) } catch {}
  }

  useEffect(() => { fetchDebates(); const i = setInterval(fetchDebates, 3000); return () => clearInterval(i) }, [])
  useEffect(() => {
    if (!selected || selected.status === 'complete') return
    const i = setInterval(async () => {
      try { setSelected(await api.get<Debate>(`/api/debates/${selected.id}`)) } catch {}
    }, 2000)
    return () => clearInterval(i)
  }, [selected?.id, selected?.status])

  const handleCreate = async () => {
    if (!topic) return
    setCreating(true)
    try {
      const d = await api.post<Debate>('/api/debates', { topic, agent_for: agentFor, agent_against: agentAgainst })
      setDebates(p => [d, ...p]); setSelected(d); setTopic('')
    } catch {}
    setCreating(false)
  }

  if (selected) {
    const d = selected
    const forRounds = d.rounds.filter(r => r.speaker === d.position_for)
    const againstRounds = d.rounds.filter(r => r.speaker === d.position_against)
    const done = d.status === 'complete'

    return (
      <>
        <div style={{ marginBottom: 20 }}><button className="btn btn-sm" onClick={() => setSelected(null)}>← Back</button></div>
        <h2 className="section-title">{d.topic}</h2>
        <div className={`battle-card-status status-${done ? 'complete' : 'coding'}`} style={{ marginBottom: 24 }}>
          <span className={`status-dot ${done ? 'complete' : 'coding'}`} />{d.status.toUpperCase()}
          {done && d.winner && <span style={{ marginLeft: 16, color: 'var(--cyan-bright)' }}>⏣ WINNER: {d.winner}</span>}
        </div>

        {done && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 48, marginBottom: 32 }}>
            {[d.position_for, d.position_against].map(pos => {
              const won = d.winner === pos
              return (
                <div key={pos} style={{ textAlign: 'center' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 900,
                    color: won ? 'var(--cyan-bright)' : 'var(--text-dim)',
                    textShadow: won ? 'var(--glow-cyan)' : 'none' }}>{d.final_scores[pos] || '—'}</div>
                  <div style={{ color: won ? 'var(--cyan-bright)' : 'var(--text-dim)', fontSize: 12 }}>{won ? '⏣ ' : ''}{pos === d.position_for ? 'FOR' : 'AGAINST'}</div>
                  <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{pos}</div>
                </div>
              )
            })}
          </div>
        )}

        <div className="arena" style={{ gridTemplateColumns: '1fr 1fr' }}>
          {Array.from({ length: Math.max(forRounds.length, againstRounds.length) }).map((_, i) => (
            <div key={i} style={{ display: 'contents' }}>
              {forRounds[i] && (
                <div className="arena-panel">
                  <div className="arena-agent-name">R{forRounds[i].round}: {d.position_for} <span style={{ color: 'var(--orange)', fontSize: 11 }}>FOR</span></div>
                  <div className="arena-code" style={{ maxHeight: 200, whiteSpace: 'pre-wrap' }}>{forRounds[i].content}</div>
                  {forRounds[i].judge_score && (
                    <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--bg-card)', borderRadius: 2 }}>
                      <span style={{ color: 'var(--cyan)', fontFamily: 'var(--font-display)', fontSize: 14 }}>Score: {forRounds[i].judge_score}/10</span>
                      <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>{forRounds[i].judge_feedback}</div>
                    </div>
                  )}
                </div>
              )}
              {againstRounds[i] && (
                <div className="arena-panel">
                  <div className="arena-agent-name">R{againstRounds[i].round}: {d.position_against} <span style={{ color: 'var(--red)', fontSize: 11 }}>AGAINST</span></div>
                  <div className="arena-code" style={{ maxHeight: 200, whiteSpace: 'pre-wrap' }}>{againstRounds[i].content}</div>
                  {againstRounds[i].judge_score && (
                    <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--bg-card)', borderRadius: 2 }}>
                      <span style={{ color: 'var(--cyan)', fontFamily: 'var(--font-display)', fontSize: 14 }}>Score: {againstRounds[i].judge_score}/10</span>
                      <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>{againstRounds[i].judge_feedback}</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </>
    )
  }

  return (
    <>
      <h2 className="section-title">Debate Arena</h2>
      <div className="form-panel" style={{ marginBottom: 32 }}>
        <div className="form-group">
          <label className="form-label">Debate Topic</label>
          <input className="form-input" value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g. AI should be open-source" />
        </div>
        <div className="form-group">
          <label className="form-label">Debaters</label>
          <div className="form-row">
            <input className="form-input" value={agentFor} onChange={e => setAgentFor(e.target.value)} placeholder="For" />
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--orange)', fontFamily: 'var(--font-display)' }}>VS</span>
            <input className="form-input" value={agentAgainst} onChange={e => setAgentAgainst(e.target.value)} placeholder="Against" />
          </div>
        </div>
        <div className="btn-group">
          <button className="btn btn-primary" onClick={handleCreate} disabled={!topic || creating}>
            {creating ? 'STARTING...' : '⚡ START DEBATE'}
          </button>
        </div>
      </div>

      {!debates.length ? (
        <div className="empty-state"><div className="empty-state-icon">⚖️</div><div className="empty-state-text">No debates yet</div></div>
      ) : (
        <div className="battle-grid">
          {debates.map(d => (
            <div key={d.id} className="battle-card" onClick={() => setSelected(d)}>
              <div className="battle-card-title">{d.topic}</div>
              <div className="battle-card-agents">
                <span className={`agent-chip ${d.winner === d.position_for ? 'winner' : ''}`}>{d.position_for}</span>
                <span style={{ color: 'var(--orange)', fontSize: 11 }}>VS</span>
                <span className={`agent-chip ${d.winner === d.position_against ? 'winner' : ''}`}>{d.position_against}</span>
              </div>
              <div className={`battle-card-status status-${d.status === 'complete' ? 'complete' : 'coding'}`}>
                <span className={`status-dot ${d.status === 'complete' ? 'complete' : 'coding'}`} />{d.status.toUpperCase()}
                {d.winner && d.winner !== 'TIE' && ` — ${d.winner} WINS`}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
