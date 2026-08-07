import { useState } from 'react'
import AgentPicker from './AgentPicker'
import { api } from '../lib/api'

interface Props {
  onCreated: (battle: any) => void
}

export default function CreateBattle({ onCreated }: Props) {
  const [title, setTitle] = useState('')
  const [problem, setProblem] = useState('')
  const [agents, setAgents] = useState<string[]>(['TRON', 'CLU'])
  const [testInput1, setTestInput1] = useState('')
  const [testExpected1, setTestExpected1] = useState('')
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!title || agents.length < 2) return
    if (!testInput1 || !testExpected1) return

    setCreating(true)
    try {
      const res = await fetch('/api/battles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          problem_statement: problem,
          agents: agents.map(name => ({ name, model: 'default' })),
          test_cases: [{ name: 'Test 1', input: testInput1, expected: testExpected1 }],
        }),
      })
      const battle = await res.json()
      onCreated(battle)
      setTitle(''); setProblem(''); setAgents(['TRON', 'CLU']); setTestInput1(''); setTestExpected1('')
    } catch (e) {
      console.error('Create failed', e)
    }
    setCreating(false)
  }

  return (
    <div style={{ maxWidth: 700 }}>
      <h2 className="section-title">Create Battle</h2>

      <div className="arena-panel" style={{ padding: 24 }}>
        <div style={{ marginBottom: 16 }}>
          <label className="form-label">Battle Name</label>
          <input className="form-input" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Fibonacci Showdown" />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label className="form-label">Problem Statement</label>
          <textarea className="form-input" rows={3} value={problem} onChange={e => setProblem(e.target.value)} placeholder="What should the agents solve?" />
        </div>

        <div style={{ marginBottom: 20 }}>
          <AgentPicker selected={agents} onChange={setAgents} label="Competing Agents" max={4} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label className="form-label">Test Case</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <input className="form-input" value={testInput1} onChange={e => setTestInput1(e.target.value)} placeholder="Input (e.g. 5)" style={{ flex: 1 }} />
            <span style={{ display: 'flex', alignItems: 'center', color: 'var(--cyan)' }}>→</span>
            <input className="form-input" value={testExpected1} onChange={e => setTestExpected1(e.target.value)} placeholder="Expected (e.g. 120)" style={{ flex: 1 }} />
          </div>
        </div>

        <button className="btn btn-primary" onClick={handleCreate} disabled={!title || agents.length < 2 || !testInput1 || !testExpected1 || creating}>
          {creating ? 'CREATING...' : '⚡ Start Battle'}
        </button>
      </div>
    </div>
  )
}
