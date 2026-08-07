import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-deep)',
          color: 'var(--text)',
          fontFamily: 'var(--font-mono)',
          padding: 32,
        }}>
          <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>⏣</div>
          <h1 style={{ fontFamily: 'var(--font-display)', color: 'var(--red)', fontSize: 18, marginBottom: 8 }}>
            SYSTEM FAULT
          </h1>
          <p style={{ color: 'var(--text-dim)', fontSize: 13, textAlign: 'center', maxWidth: 400 }}>
            {this.state.error.message}
          </p>
          <button
            className="btn btn-orange"
            style={{ marginTop: 24 }}
            onClick={() => this.setState({ error: null })}
          >
            RELOAD
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
