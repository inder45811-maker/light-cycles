import { useState } from 'react'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'

export default function WalletPanel() {
  const { user, refreshBalance } = useAuth()
  const [depositAmount, setDepositAmount] = useState('10')
  const [loading, setLoading] = useState(false)
  const [showDeposit, setShowDeposit] = useState(false)

  if (!user) return null

  const handleDeposit = async () => {
    const cents = Math.round(parseFloat(depositAmount || '0') * 100)
    if (cents < 100) return
    setLoading(true)
    try {
      await api.post('/api/auth/deposit', { amount_cents: cents })
      await refreshBalance()
      setShowDeposit(false)
    } catch {}
    setLoading(false)
  }

  return (
    <div style={{ position: 'relative' }}>
      <button
        className="btn btn-sm"
        style={{
          borderColor: 'var(--cyan)', color: 'var(--cyan)',
          fontFamily: 'var(--font-mono)', fontSize: 11,
        }}
        onClick={() => setShowDeposit(!showDeposit)}
      >
        ⏣ {user.balance_display}
      </button>

      {showDeposit && (
        <div style={{
          position: 'absolute', right: 0, top: 38, zIndex: 500,
          background: 'var(--bg-panel)', border: '1px solid var(--border)',
          borderRadius: 4, padding: 16, width: 220,
        }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>
            Add Funds
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {['5', '10', '25', '50'].map(amt => (
              <button key={amt} className="btn btn-sm"
                style={{
                  borderColor: depositAmount === amt ? 'var(--cyan)' : 'var(--border)',
                  color: depositAmount === amt ? 'var(--cyan-bright)' : 'var(--text-dim)',
                  fontSize: 11, padding: '4px 10px',
                }}
                onClick={() => setDepositAmount(amt)}>
                ${amt}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
            <input className="form-input" type="number" value={depositAmount}
              onChange={e => setDepositAmount(e.target.value)}
              style={{ width: 80, fontSize: 12, padding: '6px 10px' }} />
            <button className="btn btn-primary btn-sm" onClick={handleDeposit} disabled={loading}>
              {loading ? '...' : 'Deposit'}
            </button>
          </div>
          <div style={{ color: 'var(--text-dim)', fontSize: 9, marginTop: 6 }}>Dev mode — instant top-up</div>
        </div>
      )}
    </div>
  )
}
