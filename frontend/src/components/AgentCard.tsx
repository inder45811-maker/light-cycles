import type { AgentScore } from '../types'

interface Props {
  name: string
  model?: string
  status?: string
  score?: AgentScore | null
  isWinner?: boolean
  isEliminated?: boolean
  size?: 'sm' | 'md' | 'lg'
  onClick?: () => void
}

const SIZES = {
  sm: { fontSize: 11, padding: '6px 12px', scoreSize: 16 } as const,
  md: { fontSize: 13, padding: '10px 16px', scoreSize: 22 } as const,
  lg: { fontSize: 16, padding: '16px 24px', scoreSize: 32 } as const,
}

export default function AgentCard({ name, model, status, score, isWinner, isEliminated, size = 'md', onClick }: Props) {
  const s = SIZES[size]

  return (
    <div
      onClick={onClick}
      style={{
        background: isWinner ? 'rgba(0, 212, 255, 0.06)' : 'var(--bg-card)',
        border: `1px solid ${isWinner ? 'var(--cyan)' : 'var(--border)'}`,
        borderRadius: 4, padding: s.padding,
        opacity: isEliminated ? 0.4 : 1,
        transition: 'all 0.3s',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {status && <span className={`status-dot ${status}`} />}
        <span style={{
          fontFamily: 'var(--font-display)', fontSize: s.fontSize,
          fontWeight: isWinner ? 700 : 400,
          color: isWinner ? 'var(--cyan-bright)' : 'var(--text)',
          textDecoration: isEliminated ? 'line-through' : 'none',
        }}>
          {isWinner ? '⏣ ' : ''}{name}
        </span>
        {model && <span style={{ color: 'var(--text-dim)', fontSize: 9, fontFamily: 'var(--font-mono)' }}>{model}</span>}
      </div>
      {score && (
        <div style={{ marginTop: 8, display: 'flex', gap: 16, alignItems: 'baseline' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: s.scoreSize, fontWeight: 900,
            color: isWinner ? 'var(--cyan-bright)' : 'var(--text-dim)',
            textShadow: isWinner ? 'var(--glow-cyan)' : 'none',
          }}>
            {score.score}
          </span>
          <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>
            {score.tests_passed}/{score.tests_total} tests
          </span>
        </div>
      )}
    </div>
  )
}
