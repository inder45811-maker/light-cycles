import { useState, useEffect, useCallback } from 'react'
import Arena from './components/Arena'
import Leaderboard from './components/Leaderboard'
import CreateBattle from './components/CreateBattle'
import TournamentLobby from './components/TournamentLobby'
import CreateTournament from './components/CreateTournament'
import DebateArena from './components/DebateArena'

type View = 'battles' | 'leaderboard' | 'create' | 'tournaments' | 'create-tournament' | 'debates'

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
  created_at: number
}

export default function App() {
  const [view, setView] = useState<View>('tournaments')
  const [battles, setBattles] = useState<Battle[]>([])
  const [selectedBattle, setSelectedBattle] = useState<Battle | null>(null)
  const [wsConnected, setWsConnected] = useState(false)

  const fetchBattles = useCallback(async () => {
    try {
      const res = await fetch('/api/battles')
      const data = await res.json()
      setBattles(data)
    } catch (e) {
      console.error('Failed to fetch battles', e)
    }
  }, [])

  // WebSocket for real-time updates
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'battle_created' || msg.type === 'battle_complete' || msg.type === 'agent_submitted') {
        fetchBattles()
        if (msg.battle && selectedBattle?.id === msg.battle.id) {
          setSelectedBattle(msg.battle)
        }
      }
    }

    return () => ws.close()
  }, [fetchBattles, selectedBattle?.id])

  useEffect(() => {
    fetchBattles()
  }, [fetchBattles])

  return (
    <div className="app">
      <div className="grid-bg" />
      <div className="scanline" />

      <header className="header">
        <div className="header-brand">
          <span className="header-logo">
            ⏣ LIGHT<span>CYCLES</span>
          </span>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            {wsConnected ? '◉ GRID ONLINE' : '◉ OFFLINE'}
          </span>
        </div>
        <nav className="header-nav">
          <a
            href="#"
            className={view === 'tournaments' ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); setView('tournaments'); setSelectedBattle(null) }}
          >
            Tournaments
          </a>
          <a
            href="#"
            className={view === 'debates' ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); setView('debates'); setSelectedBattle(null) }}
          >
            Debates
          </a>
          <a
            href="#"
            className={view === 'battles' ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); setView('battles'); setSelectedBattle(null) }}
          >
            Arena
          </a>
          <a
            href="#"
            className={view === 'leaderboard' ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); setView('leaderboard'); setSelectedBattle(null) }}
          >
            Leaderboard
          </a>
          <a
            href="#"
            className={view === 'create-tournament' ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); setView('create-tournament'); setSelectedBattle(null) }}
          >
            + New
          </a>
        </nav>
      </header>

      <main className="main">
        {view === 'battles' && !selectedBattle && (
          <>
            <h2 className="section-title">Active Battles</h2>
            {battles.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">⏣</div>
                <div className="empty-state-text">No battles yet. The Grid is quiet.</div>
                <br />
                <button className="btn btn-primary" onClick={() => setView('create')}>
                  Initiate First Battle
                </button>
              </div>
            ) : (
              <div className="battle-grid">
                {battles.map(b => (
                  <div key={b.id} className="battle-card" onClick={() => setSelectedBattle(b)}>
                    <div className="battle-card-title">{b.title}</div>
                    <div className="battle-card-desc">{b.description}</div>
                    <div className="battle-card-agents">
                      {b.agents.map(a => (
                        <span key={a.name} className={`agent-chip ${b.winner === a.name ? 'winner' : ''}`}>
                          {a.name}
                        </span>
                      ))}
                    </div>
                    <div className={`battle-card-status status-${b.status}`}>
                      <span className={`status-dot ${b.status}`} />
                      {b.status.toUpperCase()}
                    </div>
                    {b.status === 'complete' && b.scores.length > 0 && (
                      <div className="battle-card-score">
                        {b.scores.map(s => (
                          <div key={s.agent}>
                            <div className={`score-badge ${s.score === Math.max(...b.scores.map(x => x.score)) ? 'win' : 'loss'}`}>
                              {s.score}
                            </div>
                            <div className="score-detail">{s.agent}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {view === 'battles' && selectedBattle && (
          <Arena battle={selectedBattle} onBack={() => setSelectedBattle(null)} onRefresh={fetchBattles} />
        )}

        {view === 'leaderboard' && <Leaderboard />}
        {view === 'create' && <CreateBattle onCreated={(b) => { setBattles([b, ...battles]); setView('battles') }} />}
        {view === 'tournaments' && (
          <TournamentLobby onBack={() => setView('battles')} />
        )}
        {view === 'create-tournament' && (
          <CreateTournament onCreated={() => setView('tournaments')} />
        )}
        {view === 'debates' && <DebateArena />}
      </main>
    </div>
  )
}
