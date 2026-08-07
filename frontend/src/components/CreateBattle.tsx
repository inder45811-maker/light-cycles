import { useState } from 'react'

interface Props {
  onCreated: (battle: any) => void
}

export default function CreateBattle({ onCreated }: Props) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [testInput1, setTestInput1] = useState('')
  const [testExpected1, setTestExpected1] = useState('')
  const [testInput2, setTestInput2] = useState('')
  const [testExpected2, setTestExpected2] = useState('')
  const [testInput3, setTestInput3] = useState('')
  const [testExpected3, setTestExpected3] = useState('')
  const [agent1, setAgent1] = useState('')
  const [agent2, setAgent2] = useState('')
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!title || !agent1 || !agent2) return
    if (!testInput1 || !testExpected1) return

    setCreating(true)

    const testCases = [
      { name: 'Test 1', input: testInput1, expected: testExpected1 },
    ]
    if (testInput2 && testExpected2) {
      testCases.push({ name: 'Test 2', input: testInput2, expected: testExpected2 })
    }
    if (testInput3 && testExpected3) {
      testCases.push({ name: 'Test 3', input: testInput3, expected: testExpected3 })
    }

    try {
      const res = await fetch('/api/battles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description,
          test_cases: testCases,
          agents: [
            { name: agent1, model: 'default' },
            { name: agent2, model: 'default' },
          ],
        }),
      })
      const battle = await res.json()
      onCreated(battle)
    } catch (e) {
      console.error('Create failed', e)
    }
    setCreating(false)
  }

  return (
    <>
      <h2 className="section-title">Initiate Battle</h2>

      <div className="form-panel">
        <div className="form-group">
          <label className="form-label">Battle Title</label>
          <input
            className="form-input"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Fibonacci Showdown"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-input form-textarea"
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="What should the agents solve?"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Competitors</label>
          <div className="form-row">
            <input
              className="form-input"
              value={agent1}
              onChange={e => setAgent1(e.target.value)}
              placeholder="Program 1 (e.g. TRON)"
            />
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--orange)', fontFamily: 'var(--font-display)', fontSize: 14 }}>VS</span>
            <input
              className="form-input"
              value={agent2}
              onChange={e => setAgent2(e.target.value)}
              placeholder="Program 2 (e.g. CLU)"
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Test Cases (input → expected output)</label>
          <div className="form-row" style={{ marginBottom: 12 }}>
            <input className="form-input" value={testInput1} onChange={e => setTestInput1(e.target.value)} placeholder="Input (e.g. 5)" />
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--cyan)', fontSize: 12 }}>→</span>
            <input className="form-input" value={testExpected1} onChange={e => setTestExpected1(e.target.value)} placeholder="Expected (e.g. 120)" />
          </div>
          <div className="form-row" style={{ marginBottom: 12 }}>
            <input className="form-input" value={testInput2} onChange={e => setTestInput2(e.target.value)} placeholder="Input (optional)" />
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--cyan)', fontSize: 12 }}>→</span>
            <input className="form-input" value={testExpected2} onChange={e => setTestExpected2(e.target.value)} placeholder="Expected (optional)" />
          </div>
          <div className="form-row">
            <input className="form-input" value={testInput3} onChange={e => setTestInput3(e.target.value)} placeholder="Input (optional)" />
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--cyan)', fontSize: 12 }}>→</span>
            <input className="form-input" value={testExpected3} onChange={e => setTestExpected3(e.target.value)} placeholder="Expected (optional)" />
          </div>
        </div>

        <div className="btn-group">
          <button
            className="btn btn-primary"
            onClick={handleCreate}
            disabled={!title || !agent1 || !agent2 || !testInput1 || !testExpected1 || creating}
          >
            {creating ? 'INITIATING...' : '⏣ INITIATE BATTLE'}
          </button>
        </div>
      </div>
    </>
  )
}
