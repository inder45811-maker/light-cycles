import { useState, useEffect } from 'react'
import { api } from '../lib/api'

interface Agent {
  id: string
  name: string
  description: string
  personality: string
  mode: string
  model: string
  stats: Record<string, number>
}

export default function Marketplace() {
  const [agents, setAgents] = useState<Agent[]>([])

  useEffect(() => {
    api.get<Agent[]>('/api/agents/marketplace').then(setAgents).catch(() => {})
  }, [])

  const personalities: Record<string, string> = {
    aggressive: '⚡', balanced: '◆', conservative: '◆', creative: '◆',
  }

  return (
    <div style={{ maxWidth: 700 }}>
      <h2 className="section-title">Agent Marketplace</h2>
      <div style={{ color: 'var(--text-dim)', fontSize: 12, marginBottom: 24 }}>
        Community agents you can use in tournaments and battles. Publish yours from <strong style={{ color: 'var(--cyan)' }}>My Agents</strong>.
      </div>

      {agents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⬡</div>
          <div className="empty-state-text">No public agents yet. Be the first to publish one.</div>
        </div>
      ) : (
        agents.map(agent => (
          <div key={agent.id} className="arena-panel" style={{ padding: 20, marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 18 }}>{personalities[agent.personality] || '◆'}</span>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, color: 'var(--cyan-bright)' }}>
                    {agent.name}
                  </div>
                </div>
                <div style={{ color: 'var(--text-dim)', fontSize: 12, marginTop: 6, marginLeft: 28 }}>
                  {agent.description || 'No description'}
                </div>
                <div style={{ marginLeft: 28, marginTop: 8, display: 'flex', gap: 12, fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                  <span>{agent.personality}</span>
                  <span>|</span>
                  <span>{agent.mode === 'webhook' ? 'Webhook' : 'AI'}</span>
                  <span>|</span>
                  <span>{agent.model}</span>
                </div>
              </div>
              {agent.stats && (
                <div style={{ textAlign: 'right', fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                  {agent.stats.battles > 0 && <div>⚔️ {agent.stats.battles} battles</div>}
                  {agent.stats.tournaments > 0 && <div>🏆 {agent.stats.tournaments} tournaments</div>}
                  {agent.stats.pits > 0 && <div>📈 {agent.stats.pits} pits</div>}
                  {agent.stats.wins > 0 && <div style={{ color: 'var(--green)', marginTop: 4 }}>{agent.stats.wins} wins</div>}
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
