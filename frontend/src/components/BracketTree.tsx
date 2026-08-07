import type { MatchEntry, PlayerEntry } from '../types'

interface Props {
  matches: MatchEntry[]
  players: PlayerEntry[]
}

export default function BracketTree({ matches, players }: Props) {
  const rounds = new Map<number, MatchEntry[]>()
  for (const m of matches) {
    if (!rounds.has(m.round)) rounds.set(m.round, [])
    rounds.get(m.round)!.push(m)
  }
  const roundKeys = [...rounds.keys()].sort((a, b) => a - b)

  return (
    <div style={{
      display: 'flex', gap: 40, overflowX: 'auto', padding: '24px 0',
      justifyContent: 'center', minHeight: 300,
    }}>
      {roundKeys.map((roundNum, ri) => {
        const roundMatches = rounds.get(roundNum)!
        const gap = ri === 0 ? 16 : 64

        return (
          <div key={roundNum} style={{
            display: 'flex', flexDirection: 'column',
            justifyContent: 'space-around', minWidth: 180, gap,
          }}>
            <div style={{
              fontFamily: 'var(--font-display)', fontSize: 10,
              color: ri === roundKeys.length - 1 ? 'var(--cyan-bright)' : 'var(--orange)',
              textTransform: 'uppercase', letterSpacing: 2, textAlign: 'center', marginBottom: 4,
            }}>
              {roundMatches[0]?.round_name || `R${roundNum}`}
            </div>

            {roundMatches.map(m => (
              <div key={m.id} style={{ position: 'relative' }}>
                {/* Connector lines to next round */}
                {ri > 0 && (
                  <>
                    <div style={{ position: 'absolute', left: -40, top: '50%', width: 20, height: 1, background: 'var(--border)' }} />
                    <div style={{ position: 'absolute', left: -20, top: '50%', width: 1, height: '50%', background: 'var(--border)' }} />
                  </>
                )}

                <div style={{
                  background: m.status === 'complete' && m.winner ? 'rgba(0, 212, 255, 0.04)' : 'var(--bg-card)',
                  border: `1px solid ${m.status === 'complete' ? 'var(--cyan-dim)' : 'var(--border)'}`,
                  borderRadius: 4, padding: '10px 14px',
                }}>
                  {[m.player1, m.player2].map((name, i) => {
                    const isWinner = m.winner === name
                    const eliminated = m.status === 'complete' && !isWinner
                    return (
                      <div key={name} style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '3px 0', opacity: eliminated ? 0.35 : 1,
                        borderBottom: i === 0 ? '1px solid var(--border)' : 'none',
                      }}>
                        <span style={{
                          fontFamily: 'var(--font-mono)', fontSize: 11,
                          color: isWinner ? 'var(--cyan-bright)' : 'var(--text)',
                          fontWeight: isWinner ? 700 : 400,
                          textDecoration: eliminated ? 'line-through' : 'none',
                        }}>
                          {isWinner ? '⏣ ' : ''}{name}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )
      })}
    </div>
  )
}
