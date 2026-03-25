import type { UIStateSnapshot, ComponentState } from '../models/types'
import type { AgentBridge } from './AgentBridge'

/**
 * StateReporter - Reports UI state to CraftBot so agent can "see" the UI
 * Periodically captures and sends UI state snapshots
 */
export class StateReporter {
  private bridge: AgentBridge
  private intervalId: ReturnType<typeof setInterval> | null = null
  private reportInterval: number = 1000 // Default 1 second
  private registeredComponents: Map<string, Record<string, unknown>> = new Map()

  constructor(bridge: AgentBridge) {
    this.bridge = bridge
  }

  /**
   * Start periodic state reporting
   */
  startReporting(interval?: number): void {
    if (interval) {
      this.reportInterval = interval
    }

    // Stop any existing interval
    this.stopReporting()

    // Start new interval
    this.intervalId = setInterval(() => {
      this.reportCurrentState()
    }, this.reportInterval)

    // Also report immediately
    this.reportCurrentState()

    console.log(`[StateReporter] Started reporting every ${this.reportInterval}ms`)
  }

  /**
   * Stop periodic state reporting
   */
  stopReporting(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
      console.log('[StateReporter] Stopped reporting')
    }
  }

  /**
   * Register a component's state for tracking
   */
  registerComponent(name: string, state: Record<string, unknown>): void {
    this.registeredComponents.set(name, state)
  }

  /**
   * Unregister a component
   */
  unregisterComponent(name: string): void {
    this.registeredComponents.delete(name)
  }

  /**
   * Update a registered component's state
   */
  updateComponentState(name: string, state: Record<string, unknown>): void {
    if (this.registeredComponents.has(name)) {
      this.registeredComponents.set(name, state)
    }
  }

  /**
   * Capture and report current state
   */
  private reportCurrentState(): void {
    try {
      const state = this.captureState()
      this.bridge.reportState(state)
    } catch (error) {
      console.error('[StateReporter] Failed to capture state:', error)
    }
  }

  /**
   * Capture complete UI state snapshot
   */
  private captureState(): UIStateSnapshot {
    const root = document.getElementById('root')

    return {
      componentTree: this.getComponentTree(),
      visibleText: root ? this.extractVisibleText(root) : [],
      inputValues: this.getInputValues(),
      currentView: this.getCurrentView(),
      scrollPosition: {
        x: window.scrollX,
        y: window.scrollY,
      },
      timestamp: Date.now(),
    }
  }

  /**
   * Get component tree from registered components
   */
  private getComponentTree(): ComponentState[] {
    const tree: ComponentState[] = []

    this.registeredComponents.forEach((props, name) => {
      tree.push({
        name,
        props: { ...props },
      })
    })

    return tree
  }

  /**
   * Extract visible text from DOM
   */
  private extractVisibleText(element: HTMLElement): string[] {
    const texts: string[] = []
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          const parent = node.parentElement
          if (!parent) return NodeFilter.FILTER_REJECT

          // Skip hidden elements
          const style = getComputedStyle(parent)
          if (style.display === 'none' || style.visibility === 'hidden') {
            return NodeFilter.FILTER_REJECT
          }

          // Skip script and style tags
          const tagName = parent.tagName.toLowerCase()
          if (tagName === 'script' || tagName === 'style') {
            return NodeFilter.FILTER_REJECT
          }

          return NodeFilter.FILTER_ACCEPT
        },
      }
    )

    let node: Node | null
    while ((node = walker.nextNode())) {
      const text = node.textContent?.trim()
      if (text && text.length > 0) {
        texts.push(text)
      }
    }

    // Limit to first 100 text nodes to avoid huge payloads
    return texts.slice(0, 100)
  }

  /**
   * Get all input values from the page
   */
  private getInputValues(): Record<string, string> {
    const values: Record<string, string> = {}

    // Get input values
    document.querySelectorAll('input').forEach((input, index) => {
      const key = input.name || input.id || `input_${index}`
      values[key] = input.value
    })

    // Get textarea values
    document.querySelectorAll('textarea').forEach((textarea, index) => {
      const key = textarea.name || textarea.id || `textarea_${index}`
      values[key] = textarea.value
    })

    // Get select values
    document.querySelectorAll('select').forEach((select, index) => {
      const key = select.name || select.id || `select_${index}`
      values[key] = select.value
    })

    return values
  }

  /**
   * Determine current view/route
   */
  private getCurrentView(): string {
    // Try to get from URL hash or pathname
    const hash = window.location.hash.slice(1)
    if (hash) return hash

    const pathname = window.location.pathname
    if (pathname && pathname !== '/') return pathname

    // Fall back to page title
    return document.title || 'main'
  }

  /**
   * Set reporting interval
   */
  setReportInterval(interval: number): void {
    this.reportInterval = interval

    // Restart if already running
    if (this.intervalId) {
      this.startReporting()
    }
  }

  /**
   * Force an immediate state report
   */
  forceReport(): void {
    this.reportCurrentState()
  }
}
