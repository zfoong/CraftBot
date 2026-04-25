import { useState, useEffect, useCallback, useRef } from 'react'
import { getWsUrl } from '../../utils/connection'

export function useSettingsWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  // Support multiple handlers per message type (e.g., multiple ShareSections)
  const messageHandlersRef = useRef<Map<string, Set<(data: unknown) => void>>>(new Map())

  useEffect(() => {
    const wsUrl = getWsUrl()
    let cancelled = false
    let reconnectAttempts = 0
    let reconnectTimeout: number | null = null

    const connect = () => {
      if (cancelled) return
      const connId = Math.random().toString(36).slice(2, 8)
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttempts = 0
        setIsConnected(true)
      }

      ws.onclose = (e) => {
        setIsConnected(false)
        if (cancelled) return
        reconnectAttempts += 1
        const delay = Math.min(500 * Math.pow(1.5, reconnectAttempts - 1), 30000)
        console.log(`[Settings WS ${connId}] closed code=${e.code}, reconnecting in ${delay}ms (attempt ${reconnectAttempts})`)
        reconnectTimeout = window.setTimeout(connect, delay)
      }

      ws.onerror = () => {
        // onclose fires after onerror — reconnect handled there
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          const handlers = messageHandlersRef.current.get(msg.type)
          if (handlers) {
            handlers.forEach(handler => handler(msg.data))
          }
        } catch (err) {
          console.error(`[Settings WS] Failed to parse message:`, err)
        }
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      wsRef.current?.close()
    }
  }, [])

  const send = useCallback((type: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }))
    }
  }, [])

  const onMessage = useCallback((type: string, handler: (data: unknown) => void) => {
    if (!messageHandlersRef.current.has(type)) {
      messageHandlersRef.current.set(type, new Set())
    }
    messageHandlersRef.current.get(type)!.add(handler)
    return () => {
      const handlers = messageHandlersRef.current.get(type)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) messageHandlersRef.current.delete(type)
      }
    }
  }, [])

  return { send, onMessage, isConnected }
}
