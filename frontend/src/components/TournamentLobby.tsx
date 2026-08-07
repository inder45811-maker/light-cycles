import { useState, useEffect } from 'react'
import type { Tournament, ToastMessage } from '../types'
import BracketTree from './BracketTree'
import { api } from '../lib/api'

interface Props {
  onBack?: () => void
  addToast?: (type: ToastMessage['type'], text: string) => void
}

export default function TournamentLobby({ onBack }: Props) {
  const [tournaments, setTournaments] = useState<Tournament[]>([])
  const [selected, setSelected] = useState<Tournament | null>(null)
  const [playerName, setPlayerName] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchTournaments = async () => {
    try {
      setTournaments(await api.get<Tournament[]>('/api/tournaments'))
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchTournaments() }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('session_id')) {
      window.history.replaceState({}, '', window.location.pathname)
      fetchTournaments()
    }
  }, [])

  const handleRegister = async (tournamentId: string) => {
    if (!playerName.trim()) return
    try {
      const data = await api.post<{ payment_required?: boolean; checkout_url?: string }>(
        `/api/tournaments/${tournamentId}/register`,
        { player_name: playerName.trim() },
      )
      if (data.payment_required && data.checkout_url) {
        window.location.href = data.checkout_url
        return
      }
      setPlayerName('')
      fetchTournaments()
    } catch {}
  }

  const handleStart = async (id: string) => {
    try {
      await api.post(`/api/tournaments/${id}/start`)
      fetchTournaments()
    } catch {}
  }

  if (loading) return <div className="empty-state"><div className="empty-state-text">Loading tournaments...</div></div>

  if (selected) {
    const t = selected
    return (
      <>
        <div style={{ marginBottom: 20 }}><button className="btn btn-sm" onClick={() => setSelected(null)}>← Back to Lobby</button></div>
        <h2 className="section-title">{t.title}</h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          <div className="arena-panel">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Prize Pool</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 900, color: 'var(--cyan-bright)', textShadow: 'var(--glow-cyan)' }}>{t.prize_pool_display}</div>
            <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>Platform fee: {t.platform_fee_display} (15%)</div>
          </div>
          <div className="arena-panel">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Status</div>
            <div className={`battle-card-status status-${t.status}`} style={{ fontSize: 14 }}>
              <span className={`status-dot ${t.status}`} />{t.status.toUpperCase()}
              {t.status === 'in_progress' && ` — ${t.round_name}`}
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 8 }}>{t.paid_count}/{t.player_cap} players · Entry {t.entry_fee_display}</div>
          </div>
        </div>

        {/* Players */}
        <div className="arena-panel full" style={{ marginBottom: 24 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>
            Programs ({t.paid_count}/{t.player_cap})
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {t.players.map(p => (
              <span key={p.id} className={`agent-chip ${p.eliminated ? '' : p.paid ? 'winner' : ''}`}
                style={p.eliminated ? { opacity: 0.4, textDecoration: 'line-through' } : {}}>
                {p.name} {p.paid ? '●' : '○'}
              </span>
            ))}
          </div>
          {['upcoming', 'registering'].includes(t.status) && t.player_count < t.player_cap && (
            <div style={{ marginTop: 20, display: 'flex', gap: 12, alignItems: 'end' }}>
              <div>
                <label className="form-label">Your Program Name</label>
                <input className="form-input" value={playerName} onChange={e => setPlayerName(e.target.value)}
                  placeholder="e.g. TRON" style={{ width: 200 }}
                  onKeyDown={e => e.key === 'Enter' && handleRegister(t.id)} />
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => handleRegister(t.id)} disabled={!playerName.trim()}>
                Register — {t.entry_fee_display}
              </button>
            </div>
          )}
          {['upcoming', 'registering', 'full'].includes(t.status) && t.paid_count >= 2 && (
            <div style={{ marginTop: 16 }}>
              <button className="btn btn-orange btn-sm" onClick={() => handleStart(t.id)}>⏣ Start Tournament</button>
            </div>
          )}
        </div>

        {/* Bracket Tree */}
        {t.matches.length > 0 && (
          <div className="arena-panel full">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>Bracket</div>
            <BracketTree matches={t.matches} players={t.players} />
          </div>
        )}

        {t.status === 'complete' && t.winner_name && (
          <div className="arena-panel full">
            <div className="arena-verdict">
              <div className="arena-verdict-title">🏆 {t.winner_name} WINS</div>
              <div className="arena-verdict-sub">Prize: {t.prize_pool_display}</div>
            </div>
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <h2 className="section-title">Tournament Lobby</h2>
      {tournaments.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⏣</div>
          <div className="empty-state-text">No tournaments scheduled</div>
        </div>
      ) : (
        <div className="battle-grid">
          {tournaments.map(t => (
            <div key={t.id} className="battle-card" onClick={() => setSelected(t)}>
              <div className="battle-card-title">{t.title}</div>
              <div className="battle-card-desc">{t.description}</div>
              <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                <div><div style={{ fontFamily: 'var(--font-display)', fontSize: 18, color: 'var(--cyan-bright)', fontWeight: 700 }}>{t.prize_pool_display}</div><div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Prize Pool</div></div>
                <div><div style={{ fontSize: 14, color: 'var(--text)' }}>{t.paid_count}/{t.player_cap}</div><div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Programs</div></div>
                <div><div style={{ fontSize: 14, color: 'var(--orange)' }}>{t.entry_fee_display}</div><div style={{ fontSize: 9, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Entry</div></div>
              </div>
              <div className={`battle-card-status status-${t.status}`}>
                <span className={`status-dot ${t.status}`} />{t.status.toUpperCase()}
                {t.status === 'in_progress' && ` — ${t.round_name}`}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
