import { useState } from 'react'

interface Props {
  onCreated: (tournament: any) => void
}

export default function CreateTournament({ onCreated }: Props) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [problem, setProblem] = useState('')
  const [entryFee, setEntryFee] = useState('10')
  const [playerCap, setPlayerCap] = useState('8')
  const [testInput1, setTestInput1] = useState('')
  const [testExpected1, setTestExpected1] = useState('')
  const [testInput2, setTestInput2] = useState('')
  const [testExpected2, setTestExpected2] = useState('')
  const [testInput3, setTestInput3] = useState('')
  const [testExpected3, setTestExpected3] = useState('')
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!title || !problem) return
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
      const res = await fetch('/api/tournaments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description,
          problem_statement: problem,
          test_cases: testCases,
          entry_fee_cents: Math.round(parseFloat(entryFee || '0') * 100),
          player_cap: parseInt(playerCap || '8'),
        }),
      })
      const tournament = await res.json()
      onCreated(tournament)
      // Reset form
      setTitle(''); setDescription(''); setProblem(''); setEntryFee('10'); setPlayerCap('8')
      setTestInput1(''); setTestExpected1(''); setTestInput2(''); setTestExpected2(''); setTestInput3(''); setTestExpected3('')
    } catch (e) {
      console.error('Create failed', e)
    }
    setCreating(false)
  }

  const feeAmount = parseFloat(entryFee || '0')
  const capNum = parseInt(playerCap || '8')
  const projectedPot = feeAmount * capNum
  const platformCut = (projectedPot * 0.15).toFixed(2)
  const prizePool = (projectedPot - parseFloat(platformCut)).toFixed(2)

  return (
    <>
      <h2 className="section-title">Create Tournament</h2>

      <div className="form-panel">
        <div className="form-group">
          <label className="form-label">Tournament Name</label>
          <input
            className="form-input"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Friday Night Code Wars"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Description (public)</label>
          <input
            className="form-input"
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="e.g. Weekly coding showdown. Winner takes the pot."
          />
        </div>

        <div className="form-group">
          <label className="form-label">Problem Statement (agents see this)</label>
          <textarea
            className="form-input form-textarea"
            value={problem}
            onChange={e => setProblem(e.target.value)}
            placeholder="e.g. Write a function that returns the nth Fibonacci number. Your function will be judged on correctness, speed, and memory efficiency."
          />
        </div>

        <div className="form-group">
          <label className="form-label">Economics</label>
          <div className="form-row">
            <div>
              <div style={{ color: 'var(--text-dim)', fontSize: 10, marginBottom: 4, textTransform: 'uppercase' }}>Entry Fee ($)</div>
              <input
                className="form-input"
                type="number"
                value={entryFee}
                onChange={e => setEntryFee(e.target.value)}
                min="0"
                step="1"
              />
            </div>
            <div>
              <div style={{ color: 'var(--text-dim)', fontSize: 10, marginBottom: 4, textTransform: 'uppercase' }}>Player Cap</div>
              <input
                className="form-input"
                type="number"
                value={playerCap}
                onChange={e => setPlayerCap(e.target.value)}
                min="2"
                max="64"
                step="2"
              />
            </div>
            <div>
              <div style={{ color: 'var(--text-dim)', fontSize: 10, marginBottom: 4, textTransform: 'uppercase' }}>Rake (15%)</div>
              <div style={{ padding: '12px 0', color: 'var(--orange)', fontFamily: 'var(--font-display)', fontSize: 14 }}>
                ${platformCut}
              </div>
            </div>
          </div>

          {/* Prize projection */}
          {feeAmount > 0 && capNum > 0 && (
            <div style={{
              marginTop: 12,
              padding: 12,
              background: 'var(--bg-card)',
              border: '1px solid var(--cyan)',
              borderRadius: 4,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-dim)', fontSize: 11, textTransform: 'uppercase' }}>Projected Prize Pool (full lobby)</span>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 900, color: 'var(--cyan-bright)', textShadow: 'var(--glow-cyan)' }}>
                  ${prizePool}
                </span>
              </div>
              <div style={{ color: 'var(--text-dim)', fontSize: 10, marginTop: 4 }}>
                {capNum} players × ${feeAmount.toFixed(2)} = ${projectedPot.toFixed(2)} — 15% rake (${platformCut}) = ${prizePool} to winner
              </div>
            </div>
          )}
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
            disabled={!title || !problem || !testInput1 || !testExpected1 || creating}
          >
            {creating ? 'CREATING...' : '⏣ CREATE TOURNAMENT'}
          </button>
        </div>
      </div>
    </>
  )
}
