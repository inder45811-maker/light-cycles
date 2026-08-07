import { useEffect, useRef, useState, useCallback } from 'react'

export function useWebSocket(onMessage: (data: any) => void) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const retryCount = useRef(0)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${location.host}/ws`)

    ws.onopen = () => {
      setConnected(true)
      retryCount.current = 0
    }

    ws.onclose = () => {
      setConnected(false)
      const delay = Math.min(1000 * Math.pow(2, retryCount.current), 30000)
      retryCount.current++
      setTimeout(connect, delay)
    }

    ws.onmessage = (e) => {
      try { onMessageRef.current(JSON.parse(e.data)) } catch {}
    }

    wsRef.current = ws
  }, [])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])

  return { connected }
}
