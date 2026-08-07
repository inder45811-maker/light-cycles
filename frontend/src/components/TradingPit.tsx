import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'

interface PitPosition {
  cash: number
  units: number
  total_value: number
  pnl: number
  pnl_pct: number
  trade_count: number
  pnl_history: number[]
}

interface PitTrade {
  turn: number
  agent: string
  action: string
  amount: number
  price: number
}

interface Pit {
  id: string
  title: string
  asset_name: string
  agents: string[]
  starting_capital: number
  total_turns: number
  status: string
  current_turn: number
  winner: string | null
  final_scores: Record<string, number>
  price_history: number[]
  positions: Record<string, PitPosition>
  recent_trades: PitTrade[]
  created_at: number
}

const AGENT_COLORS = ['#00d4ff', '#ff6b00', '#00ff88', '#ff3344', '#ff8c00', '#ff00ff', '#ffff00', '#00ffff']

export default function TradingPit() {
  const [pits, setPits] = useState<Pit[]>([])
  const [selected, setSelected] = useState<Pit | null>(null)
  const [title, setTitle] = useState('')
  const [agent1, setAgent1] = useState('TRON')
  const [agent2, setAgent2] = useState('CLU')
  const [agent3, setAgent3] = useState('')
  const [asset, setAsset] = useState('SYNTH')
  const [capital, setCapital] = useState('10000')
  const [turns, setTurns] = useState('60')
  const [volatility, setVolatility] = useState('0.02')
  const [creating, setCreating] = useState(false)

  const fetchPits = async () => {
    try { setPits(await api.get<Pit[]>('/api/pits')) } catch {}
  }

  useEffect(() => { fetchPits(); const i = setInterval(fetchPits, 3000); return () => clearInterval(i) }, [])
  useEffect(() => {
    if (!selected || selected.status === 'complete') return
    const i = setInterval(async () => {
      try { setSelected(await api.get<Pit>(`/api/pits/${selected.id}`)) } catch {}
    }, 2000)
    return () => clearInterval(i)
  }, [selected?.id, selected?.status])

  const handleCreate = async () => {
    if (!title || !agent1 || !agent2) return
    setCreating(true)
    const agents = [agent1, agent2]
    if (agent3.trim()) agents.push(agent3.trim())
    try {
      const p = await api.post<Pit>('/api/pits', {
        title, asset_name: asset,
        agents, starting_capital: parseFloat(capital),
        total_turns: parseInt(turns), volatility: parseFloat(volatility),
      })
      setPits(d => [p, ...d]); setSelected(p)
      setTitle('')
    } catch {}
    setCreating(false)
  }

  if (selected) {
    const p = selected
    const isRunning = p.status === 'running'
    const isComplete = p.status === 'complete'
    const priceMin = Math.min(...p.price_history) * 0.98
    const priceMax = Math.max(...p.price_history) * 1.02
    const priceRange = priceMax - priceMin || 1
    const pnlValues = Object.values(p.positions).flatMap(pos => pos.pnl_history)
    const pnlMin = Math.min(-1000, ...pnlValues)
    const pnlMax = Math.max(1000, ...pnlValues)
    const pnlRange = pnlMax - pnlMin || 1
    const chartW = 600; const chartH = 200

    return (
      <>
        <div style={{ marginBottom: 20 }}><button className="btn btn-sm" onClick={() => setSelected(null)}>← Back</button></div>
        <h2 className="section-title">{p.title}</h2>

        {/* Header bar */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
          <div className="arena-panel">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: 2 }}>
              {p.asset_name}
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 900,
              color: p.price_history[p.price_history.length-1] > p.price_history[0] ? 'var(--green)' : 'var(--red)' }}>
              ${p.price_history[p.price_history.length-1]?.toFixed(2) || '—'}
            </div>
          </div>
          <div className="arena-panel">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: 2 }}>Progress</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 900, color: 'var(--cyan-bright)' }}>
              {p.current_turn}/{p.total_turns}
            </div>
            {isRunning && <div className="status-dot coding" style={{ marginTop: 4 }} />}
          </div>
          <div className="arena-panel">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: 2 }}>Status</div>
            <div className={`battle-card-status status-${isComplete ? 'complete' : isRunning ? 'coding' : 'waiting'}`} style={{ fontSize: 14 }}>
              <span className={`status-dot ${isComplete ? 'complete' : isRunning ? 'coding' : 'waiting'}`} />
              {p.status.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Price chart */}
        <div className="arena-panel full" style={{ marginBottom: 20 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>
            Price — {p.asset_name}
          </div>
          <svg width="100%" height={chartH} viewBox={`0 0 ${chartW} ${chartH}`} preserveAspectRatio="none">
            <line x1={0} y1={chartH/2} x2={chartW} y2={chartH/2} stroke="var(--border)" strokeWidth={0.5} />
            <polyline
              fill="none"
              stroke="var(--cyan)"
              strokeWidth={2}
              points={p.price_history.map((pr, i) =>
                `${(i / Math.max(p.price_history.length-1, 1)) * chartW},${chartH - ((pr - priceMin) / priceRange) * chartH}`
              ).join(' ')}
            />
          </svg>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-dim)', fontSize: 9, marginTop: 4 }}>
            <span>${priceMin.toFixed(2)}</span>
            <span>${priceMax.toFixed(2)}</span>
          </div>
        </div>

        {/* P&L chart */}
        <div className="arena-panel full" style={{ marginBottom: 20 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>
            P&L
          </div>
          <svg width="100%" height={chartH} viewBox={`0 0 ${chartW} ${chartH}`} preserveAspectRatio="none">
            <line x1={0} y1={chartH/2} x2={chartW} y2={chartH/2} stroke="var(--border)" strokeWidth={0.5} />
            {Object.entries(p.positions).map(([name, pos], i) => {
              if (!pos.pnl_history.length) return null
              return (
                <polyline
                  key={name}
                  fill="none"
                  stroke={AGENT_COLORS[i % AGENT_COLORS.length]}
                  strokeWidth={2}
                  points={pos.pnl_history.map((pnl, j) =>
                    `${(j / Math.max(pos.pnl_history.length-1, 1)) * chartW},${chartH - ((pnl - pnlMin) / pnlRange) * chartH}`
                  ).join(' ')}
                />
              )
            })}
          </svg>
          <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
            {Object.entries(p.positions).map(([name, pos], i) => (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 12, height: 3, background: AGENT_COLORS[i % AGENT_COLORS.length], borderRadius: 1 }} />
                <span style={{ fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent positions */}
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${p.agents.length}, 1fr)`, gap: 16, marginBottom: 20 }}>
          {Object.entries(p.positions).map(([name, pos], i) => {
            const color = AGENT_COLORS[i % AGENT_COLORS.length]
            return (
              <div key={name} className="arena-panel" style={{ borderColor: p.winner === name ? 'var(--cyan)' : 'var(--border)' }}>
                <div className="arena-agent-name" style={{ color }}>
                  {p.winner === name ? '⏣ ' : ''}{name}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>Value</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color }}>
                      ${pos.total_value.toLocaleString()}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>P&L</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: pos.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                      {pos.pnl >= 0 ? '+' : ''}{pos.pnl.toLocaleString()} ({pos.pnl_pct}%)
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>Cash</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>${pos.cash.toLocaleString()}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>Units</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{pos.units.toFixed(4)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>Trades</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{pos.trade_count}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Trade feed */}
        {p.recent_trades.length > 0 && (
          <div className="arena-panel full">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--cyan)', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>
              Trade Feed
            </div>
            <div style={{ maxHeight: 200, overflowY: 'auto' }}>
              {[...p.recent_trades].reverse().map((t, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 12, padding: '4px 0',
                  borderBottom: '1px solid rgba(10,48,80,0.3)',
                  fontFamily: 'var(--font-mono)', fontSize: 11,
                }}>
                  <span style={{ color: 'var(--text-dim)', width: 30 }}>T{t.turn}</span>
                  <span style={{ color: AGENT_COLORS[p.agents.indexOf(t.agent) % AGENT_COLORS.length], width: 60 }}>{t.agent}</span>
                  <span style={{
                    color: t.action === 'buy' ? 'var(--green)' : t.action === 'sell' ? 'var(--red)' : 'var(--text-dim)',
                    width: 40, textTransform: 'uppercase',
                  }}>{t.action}</span>
                  <span style={{ color: 'var(--text-dim)', width: 60 }}>{t.amount > 0 ? t.amount.toFixed(4) : '—'}</span>
                  <span style={{ color: 'var(--text-dim)' }}>@ ${t.price.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Winner */}
        {isComplete && p.winner && (
          <div className="arena-panel full" style={{ marginTop: 20 }}>
            <div className="arena-verdict">
              <div className="arena-verdict-title">🏆 {p.winner} WINS THE PIT</div>
              <div className="arena-verdict-sub">
                Final P&L: ${p.final_scores[p.winner]?.toLocaleString()}
              </div>
            </div>
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <h2 className="section-title">Trading Pits</h2>

      <div className="form-panel" style={{ marginBottom: 32 }}>
        <div className="form-group">
          <label className="form-label">Pit Name</label>
          <input className="form-input" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Friday Market Open" />
        </div>
        <div className="form-group">
          <label className="form-label">Traders</label>
          <div className="form-row">
            <input className="form-input" value={agent1} onChange={e => setAgent1(e.target.value)} placeholder="Trader 1" />
            <input className="form-input" value={agent2} onChange={e => setAgent2(e.target.value)} placeholder="Trader 2" />
            <input className="form-input" value={agent3} onChange={e => setAgent3(e.target.value)} placeholder="Trader 3 (optional)" />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Market Config</label>
          <div className="form-row">
            <div>
              <div style={{ color: 'var(--text-dim)', fontSize: 9, marginBottom: 4 }}>Asset</div>
              <input className="form-input" value={asset} onChange={e => setAsset(e.target.value)} />
            </div>
            <div>
              <div style={{ color: 'var(--text-dim)', fontSize: 9, marginBottom: 4 }}>Capital ($)</div>
              <input className="form-input" type="number" value={capital} onChange={e => setCapital(e.target.value)} />
            </div>
            <div>
              <div style={{ color: 'var(--text-dim)', fontSize: 9, marginBottom: 4 }}>Turns</div>
              <input className="form-input" type="number" value={turns} onChange={e => setTurns(e.target.value)} />
            </div>
          </div>
          <div style={{ marginTop: 8 }}>
            <div style={{ color: 'var(--text-dim)', fontSize: 9, marginBottom: 4 }}>Volatility (0.01 = calm, 0.05 = wild)</div>
            <input className="form-input" type="number" step="0.001" value={volatility} onChange={e => setVolatility(e.target.value)} style={{ width: 200 }} />
          </div>
        </div>
        <div className="btn-group">
          <button className="btn btn-primary" onClick={handleCreate} disabled={!title || !agent1 || !agent2 || creating}>
            {creating ? 'OPENING...' : '⚡ OPEN PIT'}
          </button>
        </div>
      </div>

      {!pits.length ? (
        <div className="empty-state"><div className="empty-state-icon">📈</div><div className="empty-state-text">No trading pits. The floor is empty.</div></div>
      ) : (
        <div className="battle-grid">
          {pits.map(p => (
            <div key={p.id} className="battle-card" onClick={() => setSelected(p)}>
              <div className="battle-card-title">{p.title}</div>
              <div style={{ color: 'var(--text-dim)', fontSize: 11, marginBottom: 8 }}>{p.asset_name} · {p.total_turns} turns</div>
              <div className="battle-card-agents">
                {p.agents.map((a, i) => (
                  <span key={a} className={`agent-chip ${p.winner === a ? 'winner' : ''}`}>{a}</span>
                ))}
              </div>
              <div className={`battle-card-status status-${p.status === 'complete' ? 'complete' : p.status === 'running' ? 'coding' : 'waiting'}`}>
                <span className={`status-dot ${p.status === 'complete' ? 'complete' : p.status === 'running' ? 'coding' : 'waiting'}`} />
                {p.status.toUpperCase()}
                {p.winner && ` — ${p.winner} WINS`}
              </div>
              {p.status === 'complete' && Object.keys(p.final_scores).length > 0 && (
                <div style={{ marginTop: 12 }}>
                  {Object.entries(p.final_scores).map(([name, score]) => (
                    <div key={name} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, padding: '2px 0' }}>
                      <span style={{ color: 'var(--text-dim)' }}>{name}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: score >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {score >= 0 ? '+' : ''}{score.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  )
}
