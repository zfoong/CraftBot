/**
 * StatePersistence - localStorage persistence for Living UI
 *
 * Provides client-side state persistence as:
 * 1. A fallback when backend is unavailable
 * 2. Quick local cache for UI preferences
 * 3. Offline support for temporary state
 *
 * Note: For important data, always use the backend (ApiService).
 * localStorage should be used for:
 * - UI preferences (theme, layout, panel sizes)
 * - Temporary drafts
 * - Cached data for faster initial load
 */

export interface PersistenceOptions {
  /** Debounce delay for save operations (ms) */
  debounceMs?: number
  /** Version number for migration support */
  version?: number
}

export class StatePersistence<T extends Record<string, unknown>> {
  private storageKey: string
  private saveTimeout: ReturnType<typeof setTimeout> | null = null
  private debounceMs: number
  private version: number

  /**
   * Create a new StatePersistence instance
   *
   * @param projectId - Unique project identifier (uses {{PROJECT_ID}} placeholder)
   * @param namespace - Optional namespace for multiple persistence stores
   * @param options - Configuration options
   */
  constructor(
    projectId: string = '{{PROJECT_ID}}',
    namespace: string = 'state',
    options: PersistenceOptions = {}
  ) {
    this.storageKey = `living-ui-${projectId}-${namespace}`
    this.debounceMs = options.debounceMs ?? 500
    this.version = options.version ?? 1
  }

  /**
   * Save state to localStorage
   *
   * Automatically debounces to avoid excessive writes.
   * For immediate save, use saveSync().
   */
  save(state: Partial<T>): void {
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout)
    }
    this.saveTimeout = setTimeout(() => {
      this.saveSync(state)
    }, this.debounceMs)
  }

  /**
   * Save state immediately without debouncing
   */
  saveSync(state: Partial<T>): void {
    try {
      const data = {
        version: this.version,
        timestamp: Date.now(),
        state,
      }
      localStorage.setItem(this.storageKey, JSON.stringify(data))
    } catch (error) {
      console.warn('[StatePersistence] Failed to save:', error)
    }
  }

  /**
   * Load state from localStorage
   *
   * @returns The saved state, or null if not found/invalid
   */
  load(): Partial<T> | null {
    try {
      const raw = localStorage.getItem(this.storageKey)
      if (!raw) return null

      const data = JSON.parse(raw)

      // Version mismatch - don't load old data
      if (data.version !== this.version) {
        console.info('[StatePersistence] Version mismatch, clearing old data')
        this.clear()
        return null
      }

      return data.state || null
    } catch (error) {
      console.warn('[StatePersistence] Failed to load:', error)
      return null
    }
  }

  /**
   * Check if saved state exists
   */
  exists(): boolean {
    return localStorage.getItem(this.storageKey) !== null
  }

  /**
   * Clear saved state
   */
  clear(): void {
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout)
      this.saveTimeout = null
    }
    localStorage.removeItem(this.storageKey)
  }

  /**
   * Get the timestamp of last save
   *
   * @returns Unix timestamp in ms, or null if no save exists
   */
  getLastSaveTime(): number | null {
    try {
      const raw = localStorage.getItem(this.storageKey)
      if (!raw) return null
      const data = JSON.parse(raw)
      return data.timestamp || null
    } catch {
      return null
    }
  }

  /**
   * Merge updates into existing saved state
   *
   * Useful for partial updates without loading full state.
   */
  merge(updates: Partial<T>): void {
    const current = this.load() || {}
    const merged = { ...current, ...updates }
    this.save(merged as Partial<T>)
  }
}

// ============================================================================
// Pre-configured instances for common use cases
// ============================================================================

/**
 * UI preferences persistence (theme, layout, etc.)
 */
export const uiPreferences = new StatePersistence<{
  theme: 'light' | 'dark' | 'system'
  sidebarWidth: number
  fontSize: number
  [key: string]: unknown
}>('{{PROJECT_ID}}', 'ui-prefs', { debounceMs: 1000 })

/**
 * Draft/temporary data persistence
 */
export const draftStorage = new StatePersistence<{
  [key: string]: unknown
}>('{{PROJECT_ID}}', 'drafts', { debounceMs: 300 })

/**
 * Cache for backend data (faster initial load)
 */
export const stateCache = new StatePersistence<{
  [key: string]: unknown
}>('{{PROJECT_ID}}', 'cache', { debounceMs: 1000 })
