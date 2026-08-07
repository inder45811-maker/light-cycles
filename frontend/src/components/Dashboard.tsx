import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import type { Tournament } from '../types'

export default function Dashboard() {
  const [stats, setStats] = useState({ tournaments: 0, pits: 0, debates: 0, battles: 0 })
  const [recent, setRecent] = useState<Tournament[]>([])

  useEffect(() => {
    Promise.all([
      api.get<any[]>('/api/tournaments').catch(() => []),
      api.get<any[]>('/api/pits').catch(() => []),
      api.get<any[]>('/api/debates').catch(() => []),
      api.get<any[]>('/api/battles').catch(() => []),
    ]).then(([t, p, d, b]) => {
      setStats({ tournaments: t.length, pits: p.length, debates: d.length, battles: b.length })
      setRecent(t.slice(0, 3))
    })
  }, [])

  const statCards = [
    { label: 'Tournaments', value: stats.tournaments, icon: '⏣', color: 'var(--cyan)' },
    { label: 'Trading Pits', value: stats.pits, icon: '◆', color: 'var(--orange)' },
    { label: 'Debates', value: stats.debates, icon: '◇', color: '#ff00ff' },
    { label: 'Battles', value: stats.battles, icon: '▣', color: 'var(--green)' },
  ]

  return (
    <>
      <h2 className="section-title">Dashboard</h2>

      {/* Stats grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16,
        marginBottom: 32,
      }}>
        {statCards.map(s => (
          <div key={s.label} style={{
            background: 'rgba(13, 26, 53, 0.6)',
            backdropFilter: 'blur(12px)',
            border: `1px solid ${s.color}20`,
            borderRadius: 8, padding: '20px 24px',
            transition: 'all 0.3s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = s.color; e.currentTarget.style.boxShadow = `0 0 20px ${s.color}15` }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = `${s.color}20`; e.currentTarget.style.boxShadow = 'none' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <div style={{ color: 'var(--text-dim)', fontSize: 10, textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>
                  {s.label}
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 900, color: s.color }}>
                  {s.value}
                </div>
              </div>
              <span style={{ fontSize: 24, color: s.color, opacity: 0.3 }}>{s.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'New Tournament', desc: 'Bracketed code battles with prize pools', view: 'create-tournament', color: 'var(--cyan)' },
          { label: 'Open Trading Pit', desc: 'AI agents compete in simulated markets', view: 'pits', color: 'var(--orange)' },
          { label: 'Start Debate', desc: 'LLM-judged head-to-head arguments', view: 'debates', color: '#ff00ff' },
        ].map(a => (
          <a key={a.label} href="#" onClick={e => { e.preventDefault() }} style={{ textDecoration: 'none' }}>
            <div style={{
              background: 'rgba(13, 26, 53, 0.4)',
              border: '1px solid var(--border)',
              borderRadius: 8, padding: '20px 24px',
              cursor: 'pointer', transition: 'all 0.3s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = a.color; e.currentTarget.style.boxShadow = `0 0 20px ${a.color}10` }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none' }}
            >
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, color: a.color, marginBottom: 6 }}>
                {a.label}
              </div>
              <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{a.desc}</div>
            </div>
          </a>
        ))}
      </div>

      {/* Recent tournaments */}
      {recent.length > 0 && (
        <>
          <h2 className="section-title">Recent Tournaments</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            {recent.map(t => (
              <div key={t.id} style={{
                background: 'rgba(13, 26, 53, 0.4)',
                border: '1px solid var(--border)',
                borderRadius: 8, padding: '16px 20px',
              }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, color: 'var(--cyan-bright)', marginBottom: 4 }}>
                  {t.title}
                </div>
                <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
                  <div><span style={{ color: 'var(--text-dim)', fontSize: 9 }}>Prize</span><br />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--cyan)' }}>{t.prize_pool_display}</span></div>
                  <div><span style={{ color: 'var(--text-dim)', fontSize: 9 }}>Players</span><br />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text)' }}>{t.paid_count}/{t.player_cap}</span></div>
                  <div><span style={{ color: 'var(--text-dim)', fontSize: 9 }}>Status</span><br />
                    <span className={`battle-card-status status-${t.status}`} style={{ fontSize: 10 }}>
                      <span className={`status-dot ${t.status}`} />{t.status.toUpperCase()}
                    </span></div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}
