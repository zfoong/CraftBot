import type { AgentCommand, UIStateSnapshot } from '../models/types'
import { StateReporter } from './StateReporter'

/**
 * AgentBridge - Connects Living UI to CraftBot agent
 * Handles bidirectional communication via WebSocket
 */
export class AgentBridge {
  private static instance: AgentBridge | null = null
  private ws: WebSocket | null = null
  private wsUrl: string = ''
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 10
  private reconnectDelay: number = 1000
  private commandListeners: Set<(command: AgentCommand) => void> = new Set()
  private stateReporter: StateReporter

  private constructor(wsUrl: string) {
    this.wsUrl = wsUrl
    this.stateReporter = new StateReporter(this)
    this.connect()
  }

  /**
   * Initialize the AgentBridge singleton
   */
  static initialize(wsUrl: string): AgentBridge {
    if (!AgentBridge.instance) {
      AgentBridge.instance = new AgentBridge(wsUrl)
    }
    return AgentBridge.instance
  }

  /**
   * Get the singleton instance
   */
  static getInstance(): AgentBridge {
    if (!AgentBridge.instance) {
      throw new Error('AgentBridge not initialized. Call initialize() first.')
    }
    return AgentBridge.instance
  }

  /**
   * Connect to CraftBot WebSocket server
   */
  private connect(): void {
    try {
      this.ws = new WebSocket(this.wsUrl)

      this.ws.onopen = () => {
        console.log('[AgentBridge] Connected to CraftBot')
        this.reconnectAttempts = 0
        this.sendHandshake()
        this.stateReporter.startReporting()
      }

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data)
      }

      this.ws.onclose = () => {
        console.log('[AgentBridge] Connection closed')
        this.stateReporter.stopReporting()
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('[AgentBridge] WebSocket error:', error)
      }
    } catch (error) {
      console.error('[AgentBridge] Failed to connect:', error)
      this.attemptReconnect()
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[AgentBridge] Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000)

    console.log(`[AgentBridge] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)

    setTimeout(() => this.connect(), delay)
  }

  /**
   * Send handshake message to identify this Living UI
   */
  private sendHandshake(): void {
    this.send({
      type: 'living_ui_handshake',
      data: {
        projectId: '{{PROJECT_ID}}',
        projectName: '{{PROJECT_NAME}}',
        version: '1.0.0',
      },
    })
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data)

      if (message.type === 'agent_command') {
        const command: AgentCommand = {
          type: message.data.type,
          payload: message.data.payload || {},
          timestamp: Date.now(),
        }
        this.notifyCommandListeners(command)
      }
    } catch (error) {
      console.error('[AgentBridge] Failed to parse message:', error)
    }
  }

  /**
   * Send message to CraftBot
   */
  send(message: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('[AgentBridge] WebSocket not connected, message not sent')
    }
  }

  /**
   * Report UI state to CraftBot
   */
  reportState(state: UIStateSnapshot): void {
    this.send({
      type: 'living_ui_state_update',
      data: {
        projectId: '{{PROJECT_ID}}',
        state,
      },
    })
  }

  /**
   * Subscribe to agent commands
   */
  onCommand(listener: (command: AgentCommand) => void): () => void {
    this.commandListeners.add(listener)
    return () => this.commandListeners.delete(listener)
  }

  private notifyCommandListeners(command: AgentCommand): void {
    this.commandListeners.forEach((listener) => listener(command))
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Get the StateReporter instance
   */
  getStateReporter(): StateReporter {
    return this.stateReporter
  }

  /**
   * Disconnect from CraftBot
   */
  disconnect(): void {
    this.stateReporter.stopReporting()
    this.ws?.close()
    this.ws = null
  }
}
