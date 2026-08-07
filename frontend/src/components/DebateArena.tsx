import { useState, useEffect } from 'react'

interface DebateRound {
  round: number
  speaker: string
  content: string
  judge_score: number | null
  judge_feedback: string
}

interface Debate {
  id: string
  topic: string
  position_for: string
  position_against: string
  rounds: DebateRound[]
  status: string
  winner: string | null
  final_scores: Record<string, number>
  created_at: number
}

export default function DebateArena() {
  const [debates, setDebates] = useState<Debate[]>([])
  const [selected, setSelected] = useState<Debate | null>(null)
  const [topic, setTopic] = useState('')
  const [agentFor, setAgentFor] = useState('TRON')
  const [agentAgainst, setAgentAgainst] = useState('CLU')
  const [creating, setCreating] = useState(false)

  const fetchDebates = async () => {
    try {
      const res = await fetch('/api/debates')
      setDebates(await res.json())
    } catch (e) {}
  }

  useEffect(() => {
    fetchDebates()
    const interval = setInterval(fetchDebates, 3000)
    return () => clearInterval(interval)
  }, [])

  // Refresh selected debate
  useEffect(() => {
    if (selected) {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/debates/${selected.id}`)
          const d = await res.json()
          setSelected(d)
          if (d.status === 'complete') clearInterval(interval)
        } catch (e) {}
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [selected?.id])

  const handleCreate = async () => {
    if (!topic) return
    setCreating(true)
    try {
      const res = await fetch('/api/debates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, agent_for: agentFor, agent_against: agentAgainst }),
      })
      const d = await res.json()
      setDebates([d, ...debates])
      setSelected(d)
      setTopic('')
    } catch (e) {}
    setCreating(false)
  }

  if (selected) {
    const d = selected
    const forRounds = d.rounds.filter(r => r.speaker === d.position_for)
    const againstRounds = d.rounds.filter(r => r.speaker === d.position_against)
    const isComplete = d.status === 'complete'

    return (
      <>
        <div style={{ marginBottom: 20 }}>
          <button className="btn btn-sm" onClick={() => setSelected(null)}>← Back</button>
        </div>

        <h2 className="section-title">{d.topic}</h2>

        <div className={`battle-card-status status-${d.status === 'complete' ? 'complete' : 'coding'}`} style={{ marginBottom: 24 }}>
          <span className={`status-dot ${d.status === 'complete' ? 'complete' : 'coding'}`} />
          {d.status.toUpperCase()}
          {isComplete && d.winner && (
            <span style={{ marginLeft: 16, color: 'var(--cyan-bright)' }}>
              ⏣ WINNER: {d.winner}
            </span>
          )}
        </div>

        {/* Scoreboard */}
        {isComplete && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 48, marginBottom: 32 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 900,
                color: d.winner === d.position_for ? 'var(--cyan-bright)' : 'var(--text-dim)',
                textShadow: d.winner === d.position_for ? 'var(--glow-cyan)' : 'none' }}>
                {d.final_scores[d.position_for] || '—'}
              </div>
              <div style={{ color: d.winner === d.position_for ? 'var(--cyan-bright)' : 'var(--text-dim)', fontSize: 12 }}>
                {d.winner === d.position_for && '⏣ '}FOR
              </div>
              <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{d.position_for}</div>
            </div>
            <div style={{ color: 'var(--orange)', fontFamily: 'var(--font-display)', fontSize: 14, alignSelf: 'center' }}>VS</div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 900,
                color: d.winner === d.position_against ? 'var(--cyan-bright)' : 'var(--text-dim)',
                textShadow: d.winner === d.position_against ? 'var(--glow-cyan)' : 'none' }}>
                {d.final_scores[d.position_against] || '—'}
              </div>
              <div style={{ color: d.winner === d.position_against ? 'var(--cyan-bright)' : 'var(--text-dim)', fontSize: 12 }}>
                {d.winner === d.position_against && '⏣ '}AGAINST
              </div>
              <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{d.position_against}</div>
            </div>
          </div>
        )}

        {/* Rounds */}
        <div className="arena" style={{ gridTemplateColumns: '1fr 1fr' }}>
          {Array.from({ length: Math.max(forRounds.length, againstRounds.length) }).map((_, i) => (
            <>
              {forRounds[i] && (
                <div key={`for-${i}`} className="arena-panel" style={i === forRounds.length - 1 && isComplete && d.winner === d.position_for ? { borderColor: 'var(--cyan)', boxShadow: 'var(--glow-cyan)' } : {}}>
                  <div className="arena-agent-name">
                    Round {forRounds[i].round}: {d.position_for}
                    <span style={{ marginLeft: 8, color: 'var(--orange)', fontSize: 11 }}>FOR</span>
                  </div>
                  <div className="arena-code" style={{ maxHeight: 200, whiteSpace: 'pre-wrap' }}>
                    {forRounds[i].content}
                  </div>
                  {forRounds[i].judge_score && (
                    <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--bg-card)', borderRadius: 2 }}>
                      <span style={{ color: 'var(--cyan)', fontFamily: 'var(--font-display)', fontSize: 14 }}>Score: {forRounds[i].judge_score}/10</span>
                      <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>{forRounds[i].judge_feedback}</div>
                    </div>
                  )}
                </div>
              )}
              {againstRounds[i] && (
                <div key={`against-${i}`} className="arena-panel" style={i === againstRounds.length - 1 && isComplete && d.winner === d.position_against ? { borderColor: 'var(--cyan)', boxShadow: 'var(--glow-cyan)' } : {}}>
                  <div className="arena-agent-name">
                    Round {againstRounds[i].round}: {d.position_against}
                    <span style={{ marginLeft: 8, color: 'var(--red)', fontSize: 11 }}>AGAINST</span>
                  </div>
                  <div className="arena-code" style={{ maxHeight: 200, whiteSpace: 'pre-wrap' }}>
                    {againstRounds[i].content}
                  </div>
                  {againstRounds[i].judge_score && (
                    <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--bg-card)', borderRadius: 2 }}>
                      <span style={{ color: 'var(--cyan)', fontFamily: 'var(--font-display)', fontSize: 14 }}>Score: {againstRounds[i].judge_score}/10</span>
                      <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>{againstRounds[i].judge_feedback}</div>
                    </div>
                  )}
                </div>
              )}
            </>
          ))}
        </div>

        {!isComplete && (
          <div style={{ textAlign: 'center', marginTop: 24, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            <span className="status-dot coding" /> Debate in progress...
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <h2 className="section-title">Debate Arena</h2>

      <div className="form-panel" style={{ marginBottom: 32 }}>
        <div className="form-group">
          <label className="form-label">Debate Topic</label>
          <input
            className="form-input"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            placeholder="e.g. AI should be open-source"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Debaters</label>
          <div className="form-row">
            <input className="form-input" value={agentFor} onChange={e => setAgentFor(e.target.value)} placeholder="For (e.g. TRON)" />
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--orange)', fontFamily: 'var(--font-display)' }}>VS</span>
            <input className="form-input" value={agentAgainst} onChange={e => setAgentAgainst(e.target.value)} placeholder="Against (e.g. CLU)" />
          </div>
        </div>

        <div className="btn-group">
          <button
            className="btn btn-primary"
            onClick={handleCreate}
            disabled={!topic || creating}
          >
            {creating ? 'STARTING...' : '⚡ START DEBATE'}
          </button>
        </div>
      </div>

      {debates.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⚖️</div>
          <div className="empty-state-text">No debates yet. The arena is silent.</div>
        </div>
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
                <span className={`status-dot ${d.status === 'complete' ? 'complete' : 'coding'}`} />
                {d.status.toUpperCase()}
                {d.winner && d.winner !== 'TIE' && ` — ${d.winner} WINS`}
                {d.winner === 'TIE' && ' — TIE'}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
