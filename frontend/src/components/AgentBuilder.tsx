import { useState, useEffect } from 'react'
import { api } from '../lib/api'

interface Agent {
  id: string
  name: string
  description: string
  personality: string
  mode: string
  webhook_url: string
  model: string
  is_public: boolean
  stats: Record<string, number>
}

export default function AgentBuilder() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [showForm, setShowForm] = useState(false)

  const [form, setForm] = useState({
    name: '', description: '', personality: 'balanced',
    mode: 'ai', webhook_url: '', model: 'gemini-2.0-flash',
    custom_prompt: '', is_public: false,
  })

  useEffect(() => { loadAgents() }, [])

  const loadAgents = async () => {
    try { setAgents(await api.get<Agent[]>('/api/agents/mine')) } catch {}
  }

  const createAgent = async () => {
    try {
      await api.post('/api/agents', form)
      setForm({ name: '', description: '', personality: 'balanced', mode: 'ai', webhook_url: '', model: 'gemini-2.0-flash', custom_prompt: '', is_public: false })
      setShowForm(false)
      loadAgents()
    } catch {}
  }

  const deleteAgent = async (id: string) => {
    try { await api.del(`/api/agents/${id}`); loadAgents() } catch {}
  }

  const togglePublic = async (agent: Agent) => {
    try {
      await api.patch(`/api/agents/${agent.id}`, { is_public: !agent.is_public })
      loadAgents()
    } catch {}
  }

  const personalities = [
    { value: 'aggressive', label: '⚡ Aggressive', desc: 'Takes risks, acts decisively' },
    { value: 'balanced', label: '◆ Balanced', desc: 'Analytical, weighs options' },
    { value: 'conservative', label: '◆ Conservative', desc: 'Cautious, defensive' },
    { value: 'creative', label: '◆ Creative', desc: 'Unconventional approaches' },
  ]

  return (
    <div style={{ maxWidth: 700 }}>
      <h2 className="section-title">My Agents</h2>

      {!showForm && (
        <button className="btn" style={{ borderColor: 'var(--cyan)', color: 'var(--cyan)', marginBottom: 20 }}
          onClick={() => setShowForm(true)}>
          + Create New Agent
        </button>
      )}

      {showForm && (
        <div className="arena-panel" style={{ padding: 24, marginBottom: 24 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, color: 'var(--cyan-bright)', marginBottom: 20 }}>
            Create Agent
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <div className="form-label">Name</div>
              <input className="form-input" value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. TradeBot-5000" />
            </div>
            <div>
              <div className="form-label">Model</div>
              <input className="form-input" value={form.model}
                onChange={e => setForm({ ...form, model: e.target.value })} />
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <div className="form-label">Description</div>
            <input className="form-input" value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              placeholder="What does your agent do?" />
          </div>

          <div style={{ marginTop: 16 }}>
            <div className="form-label" style={{ marginBottom: 8 }}>Personality</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {personalities.map(p => (
                <button key={p.value}
                  onClick={() => setForm({ ...form, personality: p.value })}
                  style={{
                    padding: '10px', borderRadius: 6, border: form.personality === p.value ? '1px solid var(--cyan)' : '1px solid var(--border)',
                    background: form.personality === p.value ? 'rgba(0, 212, 255, 0.08)' : 'transparent',
                    color: form.personality === p.value ? 'var(--cyan-bright)' : 'var(--text-dim)',
                    cursor: 'pointer', textAlign: 'left', fontFamily: 'var(--font-mono)', fontSize: 11,
                  }}>
                  <div>{p.label}</div>
                  <div style={{ fontSize: 9, marginTop: 2 }}>{p.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 16 }}>
            <div className="form-label">Mode</div>
            <select className="form-input" value={form.mode}
              onChange={e => setForm({ ...form, mode: e.target.value })}>
              <option value="ai">AI-Powered (uses your Gemini key)</option>
              <option value="webhook">Webhook (your own API)</option>
              <option value="mock">Mock (built-in strategies)</option>
            </select>
          </div>

          {form.mode === 'webhook' && (
            <div style={{ marginTop: 12 }}>
              <div className="form-label">Webhook URL</div>
              <input className="form-input" value={form.webhook_url}
                onChange={e => setForm({ ...form, webhook_url: e.target.value })}
                placeholder="https://your-bot.com/api/decide" />
            </div>
          )}

          <div style={{ marginTop: 16 }}>
            <div className="form-label">Custom Prompt (optional)</div>
            <textarea className="form-input" rows={3} value={form.custom_prompt}
              onChange={e => setForm({ ...form, custom_prompt: e.target.value })}
              placeholder="Extra instructions for your agent..." />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', cursor: 'pointer' }}>
              <input type="checkbox" checked={form.is_public}
                onChange={e => setForm({ ...form, is_public: e.target.checked })} />
              Publish to marketplace
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-sm" style={{ borderColor: 'var(--border)' }}
                onClick={() => setShowForm(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createAgent}>Create Agent</button>
            </div>
          </div>
        </div>
      )}

      {agents.length === 0 && !showForm && (
        <div className="empty-state">
          <div className="empty-state-icon">⬡</div>
          <div className="empty-state-text">No agents yet. Create your first one to compete.</div>
        </div>
      )}

      {agents.map(agent => (
        <div key={agent.id} className="arena-panel" style={{ padding: 20, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, color: 'var(--cyan-bright)' }}>{agent.name}</div>
              <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>{agent.description || 'No description'}</div>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                <span>{agent.personality}</span>
                <span>|</span>
                <span>{agent.mode === 'webhook' ? 'Webhook' : agent.mode === 'ai' ? 'AI' : 'Mock'}</span>
                <span>|</span>
                <span>{agent.model}</span>
                {agent.is_public && <><span>|</span><span style={{ color: 'var(--green)' }}>Public</span></>}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button className="btn btn-sm" style={{ borderColor: 'var(--border)', fontSize: 9 }}
                onClick={() => togglePublic(agent)}>
                {agent.is_public ? 'Unpublish' : 'Publish'}
              </button>
              <button className="btn btn-sm" style={{ borderColor: 'rgba(255,0,0,0.3)', color: '#ff4444', fontSize: 9 }}
                onClick={() => deleteAgent(agent.id)}>
                Delete
              </button>
            </div>
          </div>
          {agent.stats && (agent.stats.battles > 0 || agent.stats.tournaments > 0) && (
            <div style={{ display: 'flex', gap: 16, marginTop: 12, padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 6, fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
              {agent.stats.battles > 0 && <span>⚔️ {agent.stats.battles} battles ({agent.stats.wins} wins)</span>}
              {agent.stats.tournaments > 0 && <span>🏆 {agent.stats.tournaments} tournaments</span>}
              {agent.stats.pits > 0 && <span>📈 {agent.stats.pits} pits</span>}
              {agent.stats.debates > 0 && <span>⚖️ {agent.stats.debates} debates</span>}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
