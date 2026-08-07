import { useState, useEffect, useCallback } from 'react'
import type { Battle, ToastMessage, View } from './types'
import { AuthProvider, useAuth } from './lib/auth'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import Arena from './components/Arena'
import Leaderboard from './components/Leaderboard'
import CreateBattle from './components/CreateBattle'
import TournamentLobby from './components/TournamentLobby'
import CreateTournament from './components/CreateTournament'
import DebateArena from './components/DebateArena'
import TradingPit from './components/TradingPit'
import HowToUse from './components/HowToUse'
import About from './components/About'
import TronGrid from './components/TronGrid'
import Toast from './components/Toast'
import ErrorBoundary from './components/ErrorBoundary'
import AuthModal from './components/AuthModal'
import WalletPanel from './components/WalletPanel'
import { api } from './lib/api'
import { useWebSocket } from './hooks/useWebSocket'

function AppContent() {
  const [view, setView] = useState<View>('dashboard')
  const [battles, setBattles] = useState<Battle[]>([])
  const [selectedBattle, setSelectedBattle] = useState<Battle | null>(null)
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  const [showAuth, setShowAuth] = useState(false)
  const { user, loading, logout } = useAuth()

  const addToast = (type: ToastMessage['type'], text: string) => {
    const id = Math.random().toString(36).slice(2)
    setToasts(t => [...t.slice(-4), { id, type, text }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 5000)
  }

  const fetchBattles = useCallback(async () => {
    try { setBattles(await api.get<Battle[]>('/api/battles')) } catch {}
  }, [])

  const { connected } = useWebSocket((msg) => {
    if (msg.type === 'battle_created' || msg.type === 'battle_complete' || msg.type === 'agent_submitted') {
      fetchBattles()
      if (msg.battle) setSelectedBattle(msg.battle)
    }
    if (msg.type === 'tournament_created' || msg.type === 'tournament_started') addToast('info', 'Tournament updated')
    if (msg.type === 'tournament_match_complete') addToast('success', 'Match complete!')
  })

  useEffect(() => { fetchBattles() }, [fetchBattles])

  return (
    <ErrorBoundary>
      <div className="app">
        <TronGrid />

        <Sidebar
          view={view}
          onNavigate={(v) => { setView(v); setSelectedBattle(null) }}
          user={user ? { username: user.username, balance_display: user.balance_display, is_guest: user.is_guest } : null}
          connected={connected}
          onSignIn={() => setShowAuth(true)}
          onLogout={() => { logout(); setShowAuth(false) }}
        />

        {/* Header area — wallet + user */}
        <div style={{
          position: 'fixed', top: 12, right: 20, zIndex: 200,
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          {user && <WalletPanel />}
        </div>

        {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

        {/* Guest banner */}
        {user?.is_guest && (
          <div style={{
            position: 'fixed', top: 0, left: 220, right: 0, zIndex: 150,
            background: 'rgba(255, 107, 0, 0.1)', borderBottom: '1px solid var(--orange)',
            padding: '8px 20px', fontSize: 11,
            color: 'var(--orange)', fontFamily: 'var(--font-mono)',
            textAlign: 'center',
          }}>
            Guest mode — <button onClick={() => setShowAuth(true)}
              style={{ background: 'none', border: 'none', color: 'var(--cyan)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, textDecoration: 'underline' }}>
              Sign in
            </button> to deposit funds and win prizes
          </div>
        )}

        <main className="main" style={{
          marginLeft: 220, padding: '32px 40px',
          marginTop: user?.is_guest ? 40 : 0,
          minHeight: '100vh',
        }}>
          {view === 'dashboard' && <Dashboard />}

          {view === 'battles' && !selectedBattle && (
            <>
              <h2 className="section-title">Active Battles</h2>
              {battles.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">⏣</div>
                  <div className="empty-state-text">No battles yet. The Grid is quiet.</div>
                  <br />
                  <button className="btn btn-primary" onClick={() => setView('create')}>Initiate First Battle</button>
                </div>
              ) : (
                <div className="battle-grid">
                  {battles.map(b => (
                    <div key={b.id} className="battle-card" onClick={() => setSelectedBattle(b)}>
                      <div className="battle-card-title">{b.title}</div>
                      <div className="battle-card-desc">{b.description}</div>
                      <div className="battle-card-agents">
                        {b.agents.map(a => (
                          <span key={a.name} className={`agent-chip ${b.winner === a.name ? 'winner' : ''}`}>{a.name}</span>
                        ))}
                      </div>
                      <div className={`battle-card-status status-${b.status}`}>
                        <span className={`status-dot ${b.status}`} />{b.status.toUpperCase()}
                      </div>
                      {b.status === 'complete' && b.scores.length > 0 && (
                        <div className="battle-card-score">
                          {b.scores.map(s => (
                            <div key={s.agent}>
                              <div className={`score-badge ${s.score === Math.max(...b.scores.map(x => x.score)) ? 'win' : 'loss'}`}>{s.score}</div>
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
          {view === 'battles' && selectedBattle && <Arena battle={selectedBattle} onBack={() => setSelectedBattle(null)} onRefresh={fetchBattles} />}
          {view === 'leaderboard' && <Leaderboard />}
          {view === 'create' && <CreateBattle onCreated={(b: Battle) => { setBattles([b, ...battles]); setView('battles') }} />}
          {view === 'tournaments' && <TournamentLobby />}
          {view === 'create-tournament' && <CreateTournament onCreated={() => setView('tournaments')} />}
          {view === 'debates' && <DebateArena />}
          {view === 'pits' && <TradingPit />}
          {view === 'howto' && <HowToUse />}
          {view === 'about' && <About />}
        </main>

        <Toast toasts={toasts} onDismiss={(id) => setToasts(t => t.filter(x => x.id !== id))} />
      </div>
    </ErrorBoundary>
  )
}

export default function App() {
  return <AuthProvider><AppContent /></AuthProvider>
}
