import type { ToastMessage } from '../types'

interface Props {
  toasts: ToastMessage[]
  onDismiss: (id: string) => void
}

const ICONS: Record<ToastMessage['type'], string> = {
  success: '✓',
  error: '✕',
  info: '◉',
  warning: '⚠',
}

const COLORS: Record<ToastMessage['type'], string> = {
  success: 'var(--green)',
  error: 'var(--red)',
  info: 'var(--cyan)',
  warning: 'var(--orange)',
}

export default function Toast({ toasts, onDismiss }: Props) {
  if (!toasts.length) return null

  return (
    <div style={{
      position: 'fixed', top: 80, right: 16, zIndex: 1000,
      display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      {toasts.map(t => (
        <div
          key={t.id}
          onClick={() => onDismiss(t.id)}
          style={{
            background: 'var(--bg-panel)',
            border: `1px solid ${COLORS[t.type]}`,
            borderRadius: 4,
            padding: '12px 20px',
            color: COLORS[t.type],
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            cursor: 'pointer',
            animation: 'toastIn 0.3s ease',
            maxWidth: 350,
          }}
        >
          {ICONS[t.type]} {t.text}
        </div>
      ))}
      <style>{`@keyframes toastIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}`}</style>
    </div>
  )
}
