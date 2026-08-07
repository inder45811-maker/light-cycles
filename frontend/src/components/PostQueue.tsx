import { useState, useEffect } from 'react'
import { api } from '../lib/api'

interface QueuedPost {
  id: string
  title: string
  mode: string
  winner: string
  loser: string
  posts: Record<string, string>
  status: string
  posted_to: string
  created_at: number
}

export default function PostQueue() {
  const [posts, setPosts] = useState<QueuedPost[]>([])
  const [stats, setStats] = useState({ pending: 0, approved: 0, posted: 0 })
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [copied, setCopied] = useState('')

  useEffect(() => { loadQueue() }, [])

  const loadQueue = async () => {
    try {
      const data = await api.get<{ posts: QueuedPost[]; stats: any }>('/api/posts/queue')
      setPosts(data.posts)
      setStats(data.stats)
    } catch {}
  }

  const markPosted = async (id: string, platform: string) => {
    await api.post(`/api/posts/${id}/mark`, { platform })
    loadQueue()
  }

  const deletePost = async (id: string) => {
    await api.del(`/api/posts/${id}`)
    loadQueue()
  }

  const copy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(text.slice(0, 20))
    setTimeout(() => setCopied(''), 2000)
  }

  const formatDate = (ts: number) => {
    return new Date(ts * 1000).toLocaleString()
  }

  return (
    <div style={{ maxWidth: 700 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 className="section-title" style={{ margin: 0 }}>Auto-Post Queue</h2>
        <div style={{ display: 'flex', gap: 12, fontSize: 11, fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: 'var(--orange)' }}>📋 {stats.pending + stats.approved} queued</span>
          <span style={{ color: 'var(--green)' }}>✅ {stats.posted} posted</span>
        </div>
      </div>

      {posts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📢</div>
          <div className="empty-state-text">No posts yet. Complete a battle to auto-generate one.</div>
        </div>
      ) : (
        posts.map(post => (
          <div key={post.id} className="arena-panel" style={{
            padding: 20, marginBottom: 12,
            borderColor: post.status === 'posted' ? 'var(--green)' : 'var(--cyan)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, color: 'var(--cyan-bright)' }}>
                  {post.title}
                </div>
                <div style={{ color: 'var(--text-dim)', fontSize: 10, marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                  {post.mode.toUpperCase()} · {post.winner} won · {formatDate(post.created_at)}
                </div>
                {post.posted_to && (
                  <div style={{ marginTop: 4, fontSize: 9, color: 'var(--green)' }}>
                    ✅ Posted to: {post.posted_to}
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', gap: 4 }}>
                <button className="btn btn-sm" style={{ borderColor: 'var(--border)', fontSize: 9 }}
                  onClick={() => setExpandedId(expandedId === post.id ? null : post.id)}>
                  {expandedId === post.id ? 'Collapse' : 'View Posts'}
                </button>
                <button className="btn btn-sm" style={{ borderColor: 'rgba(255,0,0,0.3)', color: '#ff4444', fontSize: 9 }}
                  onClick={() => deletePost(post.id)}>
                  ✕
                </button>
              </div>
            </div>

            {expandedId === post.id && (
              <div style={{ marginTop: 16 }}>
                {[
                  { key: 'twitter', label: '🐦 Twitter/X', color: '#1DA1F2' },
                  { key: 'reddit_title', label: '📕 Reddit', color: '#FF4500' },
                  { key: 'discord', label: '💬 Discord', color: '#5865F2' },
                ].map(({ key, label, color }) => (
                  <div key={key} style={{
                    marginBottom: 12, padding: 12,
                    background: 'rgba(0,0,0,0.2)', borderRadius: 6,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 10, color, fontFamily: 'var(--font-display)', textTransform: 'uppercase', letterSpacing: 1 }}>
                        {label}
                      </span>
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button className="btn btn-sm" style={{ borderColor: 'var(--border)', fontSize: 8, padding: '2px 8px' }}
                          onClick={() => copy(post.posts[key])}>
                          {copied === post.posts[key]?.slice(0, 20) ? '✓' : 'Copy'}
                        </button>
                        {!post.posted_to?.includes(key.replace('_title', '')) && (
                          <button className="btn btn-sm" style={{ borderColor: 'var(--green)', color: 'var(--green)', fontSize: 8, padding: '2px 8px' }}
                            onClick={() => markPosted(post.id, key.replace('_title', ''))}>
                            Mark Posted
                          </button>
                        )}
                      </div>
                    </div>
                    <textarea
                      readOnly
                      value={key === 'reddit_title' ? post.posts.reddit_title : post.posts[key]}
                      style={{
                        width: '100%', minHeight: 60, background: 'var(--bg-deep)',
                        border: '1px solid var(--border)', borderRadius: 4, padding: 8,
                        color: 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: 10,
                        resize: 'vertical',
                      }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}
