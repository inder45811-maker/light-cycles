import { useState, useEffect } from 'react'
import { api } from '../lib/api'

interface Agent {
  id: string
  name: string
  personality: string
  description: string
}

interface Props {
  selected: string[]
  onChange: (agents: string[]) => void
  label?: string
  max?: number
}

export default function AgentPicker({ selected, onChange, label = 'Select Agents', max = 8 }: Props) {
  const [myAgents, setMyAgents] = useState<Agent[]>([])
  const [marketAgents, setMarketAgents] = useState<Agent[]>([])
  const [showPicker, setShowPicker] = useState(false)
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.get<Agent[]>('/api/agents/mine').then(setMyAgents).catch(() => {})
    api.get<Agent[]>('/api/agents/marketplace').then(setMarketAgents).catch(() => {})
  }, [])

  const allAgents = [...myAgents, ...marketAgents.filter(m => !myAgents.find(a => a.id === m.id))]
  const filtered = search
    ? allAgents.filter(a => a.name.toLowerCase().includes(search.toLowerCase()))
    : allAgents

  const toggle = (name: string) => {
    if (selected.includes(name)) {
      onChange(selected.filter(n => n !== name))
    } else if (selected.length < max) {
      onChange([...selected, name])
    }
  }

  const addCustom = () => {
    const name = search.trim()
    if (name && !selected.includes(name) && selected.length < max) {
      onChange([...selected, name])
      setSearch('')
    }
  }

  return (
    <div style={{ position: 'relative' }}>
      <div className="form-label" style={{ marginBottom: 6 }}>{label} ({selected.length}/{max})</div>

      {/* Selected chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
        {selected.map(name => (
          <span key={name} style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '4px 10px', borderRadius: 4,
            background: 'rgba(0, 212, 255, 0.1)', border: '1px solid var(--cyan)',
            color: 'var(--cyan-bright)', fontFamily: 'var(--font-mono)', fontSize: 11,
          }}>
            {name}
            <button onClick={() => toggle(name)} style={{
              background: 'none', border: 'none', color: 'var(--text-dim)',
              cursor: 'pointer', fontSize: 14, lineHeight: 1, padding: 0,
            }}>×</button>
          </span>
        ))}
        <button onClick={() => setShowPicker(!showPicker)} style={{
          padding: '4px 10px', borderRadius: 4,
          background: 'transparent', border: '1px dashed var(--border)',
          color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 11,
          cursor: 'pointer',
        }}>
          {showPicker ? 'Close' : '+ Find Agents'}
        </button>
      </div>

      {/* Picker dropdown */}
      {showPicker && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50,
          background: 'var(--bg-panel)', border: '1px solid var(--border)',
          borderRadius: 6, padding: 12, maxHeight: 300, overflow: 'auto',
          boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
        }}>
          <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addCustom()}
              placeholder="Search or type a custom name..."
              style={{
                flex: 1, padding: '6px 10px',
                background: 'var(--bg-deep)', border: '1px solid var(--border)',
                borderRadius: 4, color: 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: 11,
              }}
            />
            {search.trim() && !filtered.find(a => a.name.toLowerCase() === search.toLowerCase()) && (
              <button onClick={addCustom} style={{
                padding: '4px 10px', borderRadius: 4,
                background: 'rgba(0, 212, 255, 0.1)', border: '1px solid var(--cyan)',
                color: 'var(--cyan)', fontFamily: 'var(--font-mono)', fontSize: 10,
                cursor: 'pointer', whiteSpace: 'nowrap',
              }}>
                + Custom
              </button>
            )}
          </div>

          {filtered.length === 0 && !search && (
            <div style={{ color: 'var(--text-dim)', fontSize: 11, textAlign: 'center', padding: 12 }}>
              No agents yet. Create one in <strong style={{ color: 'var(--cyan)' }}>My Agents</strong> or type a name above.
            </div>
          )}

          {filtered.map(agent => {
            const isSelected = selected.includes(agent.name)
            return (
              <div key={agent.id}
                onClick={() => toggle(agent.name)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 10px', borderRadius: 4, cursor: 'pointer',
                  background: isSelected ? 'rgba(0, 212, 255, 0.06)' : 'transparent',
                  border: isSelected ? '1px solid var(--cyan)' : '1px solid transparent',
                  marginBottom: 2,
                }}>
                <input type="checkbox" checked={isSelected} readOnly
                  style={{ accentColor: 'var(--cyan)' }} />
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: isSelected ? 'var(--cyan-bright)' : 'var(--text)' }}>
                    {agent.name}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {agent.personality} · {agent.description?.slice(0, 40)}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
