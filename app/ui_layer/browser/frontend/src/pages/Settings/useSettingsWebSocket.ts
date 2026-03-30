import { useState, useEffect, useCallback, useRef } from 'react'
import { getWsUrl } from '../../utils/connection'

export function useSettingsWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const messageHandlersRef = useRef<Map<string, (data: unknown) => void>>(new Map())

  useEffect(() => {
    const wsUrl = getWsUrl()
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const handler = messageHandlersRef.current.get(msg.type)
        if (handler) {
          handler(msg.data)
        }
      } catch (err) {
        console.error('[Settings WS] Failed to parse message:', err)
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  const send = useCallback((type: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }))
    }
  }, [])

  const onMessage = useCallback((type: string, handler: (data: unknown) => void) => {
    messageHandlersRef.current.set(type, handler)
    return () => {
      messageHandlersRef.current.delete(type)
    }
  }, [])

  return { send, onMessage, isConnected }
}
