import type { AppState, AgentCommand } from '../models/types'
import { AgentBridge } from '../agent/AgentBridge'

/**
 * AppController - Main application controller
 * Handles business logic, state management, and agent commands
 */
export class AppController {
  private state: AppState = {
    initialized: false,
    loading: false,
    error: null,
  }

  private listeners: Set<(state: AppState) => void> = new Set()

  /**
   * Initialize the controller
   */
  initialize(): void {
    this.setState({ initialized: true })

    // Listen for agent commands
    AgentBridge.getInstance().onCommand(this.handleAgentCommand.bind(this))

    console.log('[AppController] Initialized')
  }

  /**
   * Cleanup on unmount
   */
  cleanup(): void {
    this.listeners.clear()
  }

  /**
   * Get current state
   */
  getState(): AppState {
    return { ...this.state }
  }

  /**
   * Subscribe to state changes
   */
  subscribe(listener: (state: AppState) => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  /**
   * Update state and notify listeners
   */
  protected setState(updates: Partial<AppState>): void {
    this.state = { ...this.state, ...updates }
    this.notifyListeners()
  }

  private notifyListeners(): void {
    this.listeners.forEach((listener) => listener(this.getState()))
  }

  /**
   * Handle commands from CraftBot agent
   */
  private handleAgentCommand(command: AgentCommand): void {
    console.log('[AppController] Received agent command:', command)

    switch (command.type) {
      case 'refresh':
        this.handleRefresh()
        break
      case 'update':
        this.handleUpdate(command.payload)
        break
      case 'action':
        this.handleAction(command.payload)
        break
      default:
        console.warn('[AppController] Unknown command type:', command.type)
    }
  }

  /**
   * Handle refresh command
   */
  private handleRefresh(): void {
    // Override this in your implementation
    console.log('[AppController] Refresh requested')
  }

  /**
   * Handle update command
   */
  private handleUpdate(payload: Record<string, unknown>): void {
    // Override this in your implementation
    console.log('[AppController] Update requested:', payload)
  }

  /**
   * Handle action command
   */
  private handleAction(payload: Record<string, unknown>): void {
    // Override this in your implementation
    console.log('[AppController] Action requested:', payload)
  }
}
