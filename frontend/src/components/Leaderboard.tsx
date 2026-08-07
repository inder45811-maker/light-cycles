import { useState, useEffect } from 'react'
import type { LeaderboardEntry } from '../types'
import { api } from '../lib/api'

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<LeaderboardEntry[]>('/api/leaderboard')
      .then(setEntries)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="empty-state"><div className="empty-state-text">Scanning the Grid...</div></div>

  if (!entries.length) {
    return (
      <>
        <h2 className="section-title">Leaderboard</h2>
        <div className="empty-state">
          <div className="empty-state-icon">⏣</div>
          <div className="empty-state-text">No programs have competed yet</div>
        </div>
      </>
    )
  }

  return (
    <>
      <h2 className="section-title">Leaderboard</h2>
      <div className="leaderboard">
        <div className="leaderboard-header">
          <span>RANK</span><span>PROGRAM</span><span>BATTLES</span><span>WINS</span><span>AVG SCORE</span>
        </div>
        {entries.map((e, i) => (
          <div key={e.name} className="leaderboard-row">
            <span className={`lb-rank ${i === 0 ? 'gold' : ''}`}>{i === 0 ? '⏣' : `#${i + 1}`}</span>
            <span className="lb-name">{e.name}</span>
            <span className="lb-stat">{e.battles}</span>
            <span className="lb-stat highlight">{e.wins}</span>
            <span className="lb-stat highlight">{e.avg_score}</span>
          </div>
        ))}
      </div>
    </>
  )
}
