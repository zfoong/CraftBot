/**
 * Living UI Model Types
 * Define your data structures here
 */

// Base state interface - extend this for your app state
export interface AppState {
  initialized: boolean
  loading: boolean
  error: string | null
}

// Example data item - customize for your needs
export interface DataItem {
  id: string
  title: string
  description?: string
  createdAt: number
  updatedAt: number
}

// Agent command types that can be received from CraftBot
export interface AgentCommand {
  type: 'update' | 'refresh' | 'action' | 'navigate'
  payload: Record<string, unknown>
  timestamp: number
}

// UI State snapshot for agent awareness
export interface UIStateSnapshot {
  componentTree: ComponentState[]
  visibleText: string[]
  inputValues: Record<string, string>
  currentView: string
  scrollPosition: { x: number; y: number }
  timestamp: number
}

export interface ComponentState {
  name: string
  props: Record<string, unknown>
  children?: ComponentState[]
}
