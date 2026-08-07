import type { View } from '../types'

interface Props {
  view: View
  connected: boolean
  onNavigate: (view: View) => void
}

const NAV_ITEMS: { view: View; label: string }[] = [
  { view: 'tournaments', label: 'Tournaments' },
  { view: 'debates', label: 'Debates' },
  { view: 'battles', label: 'Arena' },
  { view: 'leaderboard', label: 'Leaderboard' },
  { view: 'create-tournament', label: '+ New' },
]

export default function AppHeader({ view, connected, onNavigate }: Props) {
  return (
    <header className="header">
      <div className="header-brand">
        <span className="header-logo">
          ⏣ LIGHT<span>CYCLES</span>
        </span>
        <span style={{ fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
          {connected ? (
            <span className="status-dot" style={{ backgroundColor: 'var(--cyan)', animation: 'pulse 2s infinite' }} />
          ) : (
            <span className="status-dot" style={{ backgroundColor: 'var(--text-dim)' }} />
          )}
          {connected ? 'GRID ONLINE' : 'OFFLINE'}
        </span>
      </div>
      <nav className="header-nav">
        {NAV_ITEMS.map(({ view: v, label }) => (
          <a
            key={v}
            href="#"
            className={view === v ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); onNavigate(v) }}
          >
            {label}
          </a>
        ))}
      </nav>
    </header>
  )
}
