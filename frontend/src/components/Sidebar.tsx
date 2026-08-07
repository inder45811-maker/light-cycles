import type { View } from '../types'

interface Props {
  view: View
  onNavigate: (view: View) => void
  user: { username: string; balance_display: string; is_guest: boolean } | null
  connected: boolean
  onSignIn: () => void
  onLogout: () => void
}

const NAV_ITEMS: { view: View; label: string; icon: string }[] = [
  { view: 'dashboard', label: 'Dashboard', icon: '◈' },
  { view: 'tournaments', label: 'Tournaments', icon: '⏣' },
  { view: 'pits', label: 'Trading Pits', icon: '◆' },
  { view: 'debates', label: 'Debates', icon: '◇' },
  { view: 'battles', label: 'Arena', icon: '▣' },
  { view: 'leaderboard', label: 'Leaderboard', icon: '▤' },
]

const BOTTOM_ITEMS: { view: View; label: string; icon: string }[] = [
  { view: 'howto', label: 'How To Use', icon: '?' },
  { view: 'about', label: 'About', icon: 'ℹ' },
]

export default function Sidebar({ view, onNavigate, user, connected, onSignIn, onLogout }: Props) {
  return (
    <aside style={{
      position: 'fixed', left: 0, top: 0, bottom: 0, width: 220, zIndex: 100,
      background: 'rgba(8, 14, 28, 0.95)',
      borderRight: '1px solid var(--border)',
      backdropFilter: 'blur(16px)',
      display: 'flex', flexDirection: 'column',
      padding: '20px 0',
    }}>
      {/* Logo */}
      <div style={{
        padding: '0 20px 20px', borderBottom: '1px solid var(--border)', marginBottom: 8,
      }}>
        <div style={{
          fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 900,
          color: 'var(--cyan-bright)', textShadow: 'var(--glow-cyan)',
          letterSpacing: 2,
        }}>
          ⏣ LIGHT<span style={{ color: 'var(--orange)', textShadow: 'var(--glow-orange)' }}>CYCLES</span>
        </div>
        <div style={{ fontSize: 9, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
          {connected ? '◉ GRID ONLINE' : '◉ OFFLINE'}
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '0 12px' }}>
        {NAV_ITEMS.map(({ view: v, label, icon }) => (
          <button
            key={v}
            onClick={() => onNavigate(v)}
            style={{
              display: 'flex', alignItems: 'center', gap: 12, width: '100%',
              padding: '10px 12px', marginBottom: 2,
              background: view === v ? 'rgba(0, 212, 255, 0.08)' : 'transparent',
              border: 'none', borderRadius: 6,
              color: view === v ? 'var(--cyan-bright)' : 'var(--text-dim)',
              fontFamily: 'var(--font-mono)', fontSize: 12,
              cursor: 'pointer', transition: 'all 0.2s',
              textAlign: 'left',
            }}
          >
            <span style={{ fontSize: 14, width: 20, textAlign: 'center' }}>{icon}</span>
            <span style={{
              fontWeight: view === v ? 600 : 400,
              textShadow: view === v ? 'var(--glow-cyan)' : 'none',
            }}>{label}</span>
            {view === v && (
              <span style={{
                marginLeft: 'auto', width: 3, height: 16,
                background: 'var(--cyan)', borderRadius: 2,
                boxShadow: 'var(--glow-cyan)',
              }} />
            )}
          </button>
        ))}

        <div style={{ marginTop: 16, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
          {BOTTOM_ITEMS.map(({ view: v, label, icon }) => (
            <button
              key={v}
              onClick={() => onNavigate(v)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12, width: '100%',
                padding: '10px 12px', marginBottom: 2,
                background: view === v ? 'rgba(0, 212, 255, 0.08)' : 'transparent',
                border: 'none', borderRadius: 6,
                color: view === v ? 'var(--cyan-bright)' : 'var(--text-dim)',
                fontFamily: 'var(--font-mono)', fontSize: 12,
                cursor: 'pointer', transition: 'all 0.2s',
                textAlign: 'left' as const,
              }}
            >
              <span style={{ fontSize: 14, width: 20, textAlign: 'center' }}>{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div style={{ marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
          <button
            onClick={() => onNavigate('create-tournament')}
            style={{
              display: 'flex', alignItems: 'center', gap: 12, width: '100%',
              padding: '10px 12px', marginBottom: 2,
              background: 'rgba(255, 107, 0, 0.08)',
              border: '1px solid rgba(255, 107, 0, 0.2)', borderRadius: 6,
              color: 'var(--orange)', fontFamily: 'var(--font-mono)', fontSize: 12,
              cursor: 'pointer', transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: 14 }}>+</span>
            <span>New Tournament</span>
          </button>
        </div>
      </nav>

      {/* User section */}
      <div style={{
        padding: '16px 20px', borderTop: '1px solid var(--border)',
        marginTop: 'auto',
      }}>
        {user ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <div style={{
                width: 28, height: 28, borderRadius: 6,
                background: 'var(--cyan-dim)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--cyan-bright)',
              }}>
                {user.username[0].toUpperCase()}
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>{user.username}</div>
                <div style={{ fontSize: 10, color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }}>{user.balance_display}</div>
              </div>
            </div>
            <button
              onClick={onLogout}
              style={{
                width: '100%', padding: '6px', background: 'transparent',
                border: '1px solid var(--border)', borderRadius: 4,
                color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 10,
                cursor: 'pointer',
              }}
            >
              Exit Grid
            </button>
          </>
        ) : (
          <button
            onClick={onSignIn}
            style={{
              width: '100%', padding: '10px',
              background: 'rgba(0, 212, 255, 0.1)',
              border: '1px solid var(--cyan)',
              borderRadius: 6,
              color: 'var(--cyan-bright)', fontFamily: 'var(--font-display)', fontSize: 11,
              cursor: 'pointer', textTransform: 'uppercase', letterSpacing: 2,
            }}
          >
            ⏣ Sign In
          </button>
        )}
      </div>
    </aside>
  )
}
