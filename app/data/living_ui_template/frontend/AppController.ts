import type { AppState } from './types'
import { ApiService } from './services/ApiService'
import { stateCache } from './services/StatePersistence'

/**
 * AppController - Main application controller
 *
 * Handles business logic and state management.
 * State is persisted to the backend (SQLite) and survives page reloads.
 *
 * Architecture:
 * - Backend holds the source of truth for state
 * - Frontend fetches state on mount
 * - State changes are sent to backend, then local state updated
 * - localStorage used as cache for faster initial load
 * - Agent observes via HTTP (GET /api/ui-snapshot, /api/state)
 * - Agent triggers actions via HTTP (POST /api/action)
 */
export class AppController {
  private state: AppState = {
    initialized: false,
    loading: true,
    error: null,
  }

  private listeners: Set<(state: AppState) => void> = new Set()
  private backendAvailable: boolean = false

  /**
   * Initialize the controller
   *
   * Fetches state from backend, falls back to localStorage cache.
   */
  async initialize(): Promise<void> {
    console.log('[AppController] Initializing...')

    // Check if backend is available
    this.backendAvailable = await ApiService.healthCheck()

    if (this.backendAvailable) {
      console.log('[AppController] Backend available, fetching state...')
      try {
        // Fetch state from backend
        const backendState = await ApiService.getState<Partial<AppState>>()
        this.state = {
          ...this.state,
          ...backendState,
          initialized: true,
          loading: false,
          error: null,
        }

        // Update local cache
        stateCache.saveSync(backendState)
        console.log('[AppController] State loaded from backend')
      } catch (error) {
        console.error('[AppController] Failed to load from backend:', error)
        this.loadFromCache()
      }
    } else {
      console.warn('[AppController] Backend unavailable, using cache')
      this.loadFromCache()
    }

    this.notifyListeners()
    console.log('[AppController] Initialized')
  }

  /**
   * Load state from localStorage cache (fallback)
   */
  private loadFromCache(): void {
    const cached = stateCache.load()
    if (cached) {
      this.state = {
        ...this.state,
        ...cached,
        initialized: true,
        loading: false,
        error: this.backendAvailable ? null : 'Backend unavailable - using cached data',
      }
      console.log('[AppController] State loaded from cache')
    } else {
      this.state = {
        ...this.state,
        initialized: true,
        loading: false,
        error: this.backendAvailable ? null : 'Backend unavailable - no cached data',
      }
      console.log('[AppController] No cached state found')
    }
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
   * Update state and persist to backend
   *
   * @param updates - Partial state to merge
   * @param persistToBackend - Whether to save to backend (default: true)
   */
  async setState(
    updates: Partial<AppState>,
    persistToBackend: boolean = true
  ): Promise<void> {
    // Update local state immediately for responsive UI
    this.state = { ...this.state, ...updates }
    this.notifyListeners()

    // Persist to backend
    if (persistToBackend && this.backendAvailable) {
      try {
        // Remove internal fields before sending to backend
        const { initialized, loading, error, ...persistableState } = updates
        if (Object.keys(persistableState).length > 0) {
          await ApiService.updateState(persistableState)
        }
      } catch (err) {
        console.error('[AppController] Failed to persist state:', err)
      }
    }

    // Update local cache
    stateCache.save(this.state)
  }

  /**
   * Execute an action via the backend
   *
   * For complex actions that need server-side processing.
   */
  async executeAction(
    action: string,
    payload?: Record<string, unknown>
  ): Promise<void> {
    if (!this.backendAvailable) {
      console.warn('[AppController] Backend unavailable, cannot execute action')
      return
    }

    try {
      const result = await ApiService.executeAction(action, payload)
      if (result.data) {
        // Update local state with result
        this.state = { ...this.state, ...result.data }
        this.notifyListeners()
        stateCache.save(this.state)
      }
    } catch (error) {
      console.error('[AppController] Action failed:', error)
    }
  }

  /**
   * Check if backend is available
   */
  isBackendAvailable(): boolean {
    return this.backendAvailable
  }

  private notifyListeners(): void {
    this.listeners.forEach((listener) => listener(this.getState()))
  }

  /**
   * Refresh state from backend
   *
   * Agent can trigger this via POST /api/action with {"action": "refresh"}
   */
  async refresh(): Promise<void> {
    console.log('[AppController] Refresh requested')
    await this.setState({ loading: true }, false)
    await this.initialize()
  }
}
