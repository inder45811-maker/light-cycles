import { useState, useEffect } from 'react'

interface Tournament {
  id: string
  title: string
  description: string
  problem_statement: string
  entry_fee_display: string
  prize_pool_display: string
  platform_fee_display: string
  player_cap: number
  player_count: number
  paid_count: number
  status: string
  winner_name: string | null
  current_round: number
  total_rounds: number
  round_name: string
  players: Array<{
    id: string
    name: string
    paid: boolean
    eliminated: boolean
    seed: number
  }>
  matches: Array<{
    id: string
    round: number
    round_name: string
    player1: string
    player2: string
    status: string
    winner: string | null
    battle_id: string | null
  }>
  scheduled_at: number | null
  created_at: number
}

interface Props {
  onBack?: () => void
}

export default function TournamentLobby({ onBack }: Props) {
  const [tournaments, setTournaments] = useState<Tournament[]>([])
  const [selected, setSelected] = useState<Tournament | null>(null)
  const [playerName, setPlayerName] = useState('')
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  const fetchTournaments = async () => {
    try {
      const res = await fetch('/api/tournaments')
      const data = await res.json()
      setTournaments(data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchTournaments()
  }, [])

  // Check URL params for payment success
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sessionId = params.get('session_id')
    const playerParam = params.get('player')
    if (sessionId && playerParam) {
      setMessage('✅ Payment successful! You are registered.')
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
      fetchTournaments()
    }
  }, [])

  const handleRegister = async (tournamentId: string) => {
    if (!playerName.trim()) return

    try {
      const res = await fetch(`/api/tournaments/${tournamentId}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: playerName.trim() }),
      })
      const data = await res.json()

      if (data.payment_required && data.checkout_url) {
        window.location.href = data.checkout_url
        return
      }

      setMessage('✅ Registered!')
      setPlayerName('')
      fetchTournaments()
    } catch (e) {
      setMessage('Registration failed.')
    }
  }

  const handleStartTournament = async (tournamentId: string) => {
    try {
      const res = await fetch(`/api/tournaments/${tournamentId}/start`, { method: 'POST' })
      if (res.ok) {
        fetchTournaments()
        setMessage('Tournament started!')
      } else {
        const err = await res.json()
        setMessage(err.detail || 'Failed to start')
      }
    } catch (e) {
      setMessage('Start failed.')
    }
  }

  const formatDate = (ts: number | null) => {
    if (!ts) return 'TBD'
    return new Date(ts * 1000).toLocaleDateString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  }

  const matchesByRound = (matches: Tournament['matches']) => {
    const grouped: Record<number, Tournament['matches']> = {}
    for (const m of matches) {
      if (!grouped[m.round]) grouped[m.round] = []
      grouped[m.round].push(m)
    }
    return grouped
  }

  if (loading) {
    return <div className="empty-state"><div className="empty-state-text">Loading tournaments...</div></div>
  }

  if (selected) {
    const t = selected
    const rounds = matchesByRound(t.matches)

    return (
      <>
        <div style={{ marginBottom: 20 }}>
          <button className="btn btn-sm" onClick={() => setSelected(null)}>← Back to Lobby</button>
        </div>

        <h2 className="section-title">{t.title}</h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          <div className="arena-panel">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>
              Prize Pool
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 900, color: 'var(--cyan-bright)', textShadow: 'var(--glow-cyan)' }}>
              {t.prize_pool_display}
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>
              Platform fee: {t.platform_fee_display} (15% rake)
            </div>
          </div>

          <div className="arena-panel">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>
              Status
            </div>
            <div className={`battle-card-status status-${t.status}`} style={{ fontSize: 14 }}>
              <span className={`status-dot ${t.status}`} />
              {t.status.toUpperCase()}
              {t.status === 'in_progress' && ` — ${t.round_name}`}
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 8 }}>
              {t.paid_count}/{t.player_cap} players · Entry {t.entry_fee_display}
            </div>
          </div>
        </div>

        {/* Players */}
        <div className="arena-panel full" style={{ marginBottom: 24 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>
            Programs ({t.paid_count}/{t.player_cap})
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {t.players.map(p => (
              <div key={p.id} className={`agent-chip ${p.eliminated ? '' : p.paid ? 'winner' : ''}`}
                style={p.eliminated ? { opacity: 0.4, textDecoration: 'line-through' } : {}}>
                {p.name} {p.paid ? '●' : '○'}
              </div>
            ))}
            {t.players.length === 0 && (
              <span style={{ color: 'var(--text-dim)', fontSize: 12 }}>No programs registered yet</span>
            )}
          </div>

          {/* Registration */}
          {['upcoming', 'registering'].includes(t.status) && t.player_count < t.player_cap && (
            <div style={{ marginTop: 20, display: 'flex', gap: 12, alignItems: 'end' }}>
              <div>
                <label className="form-label">Your Program Name</label>
                <input
                  className="form-input"
                  value={playerName}
                  onChange={e => setPlayerName(e.target.value)}
                  placeholder="e.g. TRON"
                  style={{ width: 200 }}
                  onKeyDown={e => e.key === 'Enter' && handleRegister(t.id)}
                />
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => handleRegister(t.id)} disabled={!playerName.trim()}>
                Register — {t.entry_fee_display}
              </button>
            </div>
          )}

          {/* Admin: Start button */}
          {['upcoming', 'registering', 'full'].includes(t.status) && t.paid_count >= 2 && (
            <div style={{ marginTop: 16 }}>
              <button className="btn btn-orange btn-sm" onClick={() => handleStartTournament(t.id)}>
                ⏣ Start Tournament
              </button>
            </div>
          )}
        </div>

        {/* Bracket */}
        {Object.keys(rounds).length > 0 && (
          <div className="arena-panel full">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>
              Bracket
            </div>
            {Object.entries(rounds).sort(([a], [b]) => Number(a) - Number(b)).map(([roundNum, matches]) => (
              <div key={roundNum} style={{ marginBottom: 20 }}>
                <div style={{ color: 'var(--orange)', fontFamily: 'var(--font-display)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>
                  {matches[0]?.round_name || `ROUND ${roundNum}`}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
                  {matches.map(m => (
                    <div key={m.id} style={{
                      background: 'var(--bg-card)',
                      border: `1px solid ${m.status === 'complete' ? 'var(--cyan)' : 'var(--border)'}`,
                      borderRadius: 4,
                      padding: '12px 16px',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 13,
                          color: m.winner === m.player1 ? 'var(--cyan-bright)' : 'var(--text)',
                          fontWeight: m.winner === m.player1 ? 700 : 400,
                        }}>
                          {m.winner === m.player1 ? '⏣ ' : ''}{m.player1}
                        </span>
                        <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>VS</span>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 13,
                          color: m.winner === m.player2 ? 'var(--cyan-bright)' : 'var(--text)',
                          fontWeight: m.winner === m.player2 ? 700 : 400,
                        }}>
                          {m.winner === m.player2 ? '⏣ ' : ''}{m.player2}
                        </span>
                      </div>
                      {m.status === 'complete' && (
                        <div style={{ marginTop: 8, color: 'var(--cyan)', fontSize: 10, textTransform: 'uppercase' }}>
                          {m.winner} advances
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Winner */}
        {t.status === 'complete' && t.winner_name && (
          <div className="arena-panel full">
            <div className="arena-verdict">
              <div className="arena-verdict-title">🏆 {t.winner_name} WINS THE TOURNAMENT</div>
              <div className="arena-verdict-sub">
                Prize: {t.prize_pool_display}
              </div>
            </div>
          </div>
        )}

        {message && (
          <div style={{ textAlign: 'center', marginTop: 16, color: 'var(--cyan)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
            {message}
          </div>
        )}
      </>
    )
  }

  // Lobby view
  return (
    <>
      <h2 className="section-title">Tournament Lobby</h2>

      {message && (
        <div style={{ textAlign: 'center', marginBottom: 16, padding: 12, background: 'var(--bg-card)', border: '1px solid var(--cyan)', borderRadius: 4, color: 'var(--cyan)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
          {message}
          <button className="btn btn-sm" style={{ marginLeft: 12 }} onClick={() => setMessage('')}>×</button>
        </div>
      )}

      {tournaments.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⏣</div>
          <div className="empty-state-text">No tournaments scheduled</div>
          <br />
          <a href="#" onClick={e => { e.preventDefault(); onBack?.() }} style={{ color: 'var(--cyan)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            Create one from the admin panel
          </a>
        </div>
      ) : (
        <div className="battle-grid">
          {tournaments.map(t => (
            <div key={t.id} className="battle-card" onClick={() => { setSelected(t); setMessage('') }}>
              <div className="battle-card-title">{t.title}</div>
              <div className="battle-card-desc">{t.description}</div>

              <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, color: 'var(--cyan-bright)', fontWeight: 700 }}>
                    {t.prize_pool_display}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Prize Pool</div>
                </div>
                <div>
                  <div style={{ fontSize: 14, color: 'var(--text)' }}>
                    {t.paid_count}/{t.player_cap}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Programs</div>
                </div>
                <div>
                  <div style={{ fontSize: 14, color: 'var(--orange)' }}>
                    {t.entry_fee_display}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Entry</div>
                </div>
              </div>

              <div className={`battle-card-status status-${t.status}`}>
                <span className={`status-dot ${t.status}`} />
                {t.status.toUpperCase()}
                {t.status === 'in_progress' && ` — ${t.round_name}`}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
