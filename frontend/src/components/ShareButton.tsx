import { useState } from 'react'
import { api } from '../lib/api'

interface Props {
  battleId?: string
  tournamentId?: string
  pitId?: string
  debateId?: string
  title: string
}

export default function ShareButton({ battleId, tournamentId, pitId, debateId, title }: Props) {
  const [show, setShow] = useState(false)
  const [posts, setPosts] = useState<Record<string, string> | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState('')

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const data = await api.post<{ posts: Record<string, string> }>('/api/promo/generate', {
        battle_id: battleId,
        tournament_id: tournamentId,
        pit_id: pitId,
        debate_id: debateId,
      })
      setPosts(data.posts)
    } catch {}
    setLoading(false)
  }

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(''), 2000)
  }

  return (
    <>
      <button className="btn btn-sm" style={{ borderColor: 'var(--cyan)', color: 'var(--cyan)' }}
        onClick={() => { setShow(!show); if (!posts) handleGenerate() }}>
        📢 Share
      </button>

      {show && posts && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 2000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(5, 10, 20, 0.9)', backdropFilter: 'blur(8px)',
        }} onClick={() => setShow(false)}>
          <div style={{
            background: 'var(--bg-panel)', border: '1px solid var(--border)',
            borderRadius: 8, padding: 24, width: 500, maxWidth: '90vw',
            maxHeight: '80vh', overflow: 'auto',
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              fontFamily: 'var(--font-display)', fontSize: 16, color: 'var(--cyan-bright)',
              textAlign: 'center', marginBottom: 20, textShadow: 'var(--glow-cyan)',
            }}>
              📢 Share This Battle
            </div>

            {[
              { key: 'twitter', label: '𝕏 Twitter/X', color: '#1DA1F2' },
              { key: 'reddit_title', label: '📕 Reddit Title', color: '#FF4500' },
              { key: 'reddit_body', label: '📕 Reddit Body', color: '#FF4500' },
              { key: 'discord', label: '💬 Discord', color: '#5865F2' },
            ].map(({ key, label, color }) => (
              <div key={key} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, color, fontFamily: 'var(--font-display)', textTransform: 'uppercase', letterSpacing: 1 }}>
                    {label}
                  </span>
                  <button className="btn btn-sm" style={{ borderColor: 'var(--border)', color: copied === key ? 'var(--green)' : 'var(--text-dim)', fontSize: 10, padding: '2px 10px' }}
                    onClick={() => copy(posts[key], key)}>
                    {copied === key ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
                <textarea
                  readOnly
                  value={posts[key]}
                  style={{
                    width: '100%', minHeight: key === 'reddit_body' ? 120 : 60,
                    background: 'var(--bg-deep)', border: '1px solid var(--border)',
                    borderRadius: 4, padding: 10,
                    color: 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: 11,
                    resize: 'vertical',
                  }}
                />
              </div>
            ))}

            <div style={{ color: 'var(--text-dim)', fontSize: 10, textAlign: 'center', marginTop: 12 }}>
              Post these on Twitter, Reddit, Discord — bring agents to the Grid ⚡
            </div>
          </div>
        </div>
      )}
    </>
  )
}
