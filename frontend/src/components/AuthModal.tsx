import { useState } from 'react'
import { useAuth } from '../lib/auth'

interface Props {
  onClose: () => void
}

export default function AuthModal({ onClose }: Props) {
  const { login, register, loginAsGuest } = useAuth()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setError('')
    setLoading(true)
    const err = mode === 'login'
      ? await login(email, password)
      : await register(email, username, password)
    if (err) setError(err)
    else onClose()
    setLoading(false)
  }

  const handleGuest = async () => {
    setLoading(true)
    await loginAsGuest()
    onClose()
    setLoading(false)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(5, 10, 20, 0.9)', backdropFilter: 'blur(8px)',
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-panel)', border: '1px solid var(--border)',
        borderRadius: 4, padding: 32, width: 380, maxWidth: '90vw',
      }} onClick={e => e.stopPropagation()}>
        <div style={{
          fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700,
          color: 'var(--cyan-bright)', textAlign: 'center', marginBottom: 24,
          textShadow: 'var(--glow-cyan)',
        }}>
          ⏣ {mode === 'login' ? 'SIGN IN' : 'REGISTER'}
        </div>

        {error && (
          <div style={{ color: 'var(--red)', fontSize: 12, marginBottom: 16, textAlign: 'center' }}>{error}</div>
        )}

        {mode === 'register' && (
          <div className="form-group">
            <label className="form-label">Username</label>
            <input className="form-input" value={username} onChange={e => setUsername(e.target.value)} placeholder="TRON" />
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Email</label>
          <input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="user@grid.net" />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <input className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="••••••••" onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
        </div>

        <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleSubmit} disabled={loading || !email || !password}>
          {loading ? '...' : mode === 'login' ? 'SIGN IN' : 'CREATE ACCOUNT'}
        </button>

        <div style={{ textAlign: 'center', marginTop: 12 }}>
          <button className="btn btn-sm" style={{ border: 'none', color: 'var(--text-dim)' }}
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
            {mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in'}
          </button>
        </div>

        <div style={{ textAlign: 'center', marginTop: 8 }}>
          <button className="btn btn-sm" style={{ border: 'none', color: 'var(--orange)' }}
            onClick={handleGuest} disabled={loading}>
            Continue as Guest
          </button>
        </div>
      </div>
    </div>
  )
}
