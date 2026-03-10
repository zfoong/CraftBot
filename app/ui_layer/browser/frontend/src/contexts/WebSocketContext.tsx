import React, { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react'
import type { ChatMessage, ActionItem, AgentStatus, InitialState, WSMessage } from '../types'

interface WebSocketState {
  connected: boolean
  messages: ChatMessage[]
  actions: ActionItem[]
  status: AgentStatus
  guiMode: boolean
  currentTask: { id: string; name: string } | null
  footageUrl: string | null
}

interface WebSocketContextType extends WebSocketState {
  sendMessage: (content: string) => void
  sendCommand: (command: string) => void
  clearMessages: () => void
}

const defaultState: WebSocketState = {
  connected: false,
  messages: [],
  actions: [],
  status: {
    state: 'idle',
    message: 'Connecting...',
    loading: false,
  },
  guiMode: false,
  currentTask: null,
  footageUrl: null,
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WebSocketState>(defaultState)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[WS] Connected')
      setState(prev => ({ ...prev, connected: true }))
    }

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        handleMessage(msg)
      } catch (err) {
        console.error('[WS] Failed to parse message:', err)
      }
    }

    ws.onclose = () => {
      console.log('[WS] Disconnected')
      setState(prev => ({
        ...prev,
        connected: false,
        status: { ...prev.status, message: 'Disconnected. Reconnecting...' },
      }))

      // Reconnect after delay
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, 2000)
    }

    ws.onerror = (err) => {
      console.error('[WS] Error:', err)
    }
  }, [])

  const handleMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'init': {
        const data = msg.data as unknown as InitialState
        setState(prev => ({
          ...prev,
          messages: data.messages || [],
          actions: data.actions || [],
          status: {
            state: data.agentState || 'idle',
            message: data.status || 'Ready',
            loading: false,
          },
          guiMode: data.guiMode || false,
          currentTask: data.currentTask || null,
        }))
        break
      }

      case 'chat_message': {
        const message = msg.data as unknown as ChatMessage
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, message],
        }))
        break
      }

      case 'chat_clear':
        setState(prev => ({ ...prev, messages: [] }))
        break

      case 'action_add': {
        const action = msg.data as unknown as ActionItem
        setState(prev => ({
          ...prev,
          actions: [...prev.actions, action],
        }))
        break
      }

      case 'action_update': {
        const { id, status } = msg.data as { id: string; status: string }
        setState(prev => ({
          ...prev,
          actions: prev.actions.map(a =>
            a.id === id ? { ...a, status: status as ActionItem['status'] } : a
          ),
        }))
        break
      }

      case 'action_remove': {
        const { id } = msg.data as { id: string }
        setState(prev => ({
          ...prev,
          actions: prev.actions.filter(a => a.id !== id),
        }))
        break
      }

      case 'action_clear':
        setState(prev => ({ ...prev, actions: [] }))
        break

      case 'status_update': {
        const { message, loading } = msg.data as { message: string; loading: boolean }
        setState(prev => ({
          ...prev,
          status: { ...prev.status, message, loading },
        }))
        break
      }

      case 'footage_update': {
        const { image } = msg.data as { image: string }
        setState(prev => ({ ...prev, footageUrl: image }))
        break
      }

      case 'footage_clear':
        setState(prev => ({ ...prev, footageUrl: null }))
        break

      case 'footage_visibility': {
        const { visible } = msg.data as { visible: boolean }
        setState(prev => ({ ...prev, guiMode: visible }))
        break
      }
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'message', content }))
    }
  }, [])

  const sendCommand = useCallback((command: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'command', command }))
    }
  }, [])

  const clearMessages = useCallback(() => {
    setState(prev => ({ ...prev, messages: [] }))
  }, [])

  return (
    <WebSocketContext.Provider
      value={{
        ...state,
        sendMessage,
        sendCommand,
        clearMessages,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}
