/**
 * UI Capture Service
 *
 * Captures UI state and screenshots for agent observation.
 * Uses HTTP POST to send data to backend.
 *
 * Protocol:
 * 1. Frontend captures UI state on-demand (state changes, user interactions)
 * 2. Frontend POSTs snapshot to /api/ui-snapshot
 * 3. Agent GETs /api/ui-snapshot to observe UI
 * 4. Screenshot captured only when explicitly requested
 * 5. Agent GETs /api/ui-screenshot for visual observation
 *
 * NO timer-based polling - captures happen on meaningful events only.
 */

import html2canvas from 'html2canvas'

export interface UISnapshot {
  htmlStructure: string | null
  visibleText: string[]
  inputValues: Record<string, string>
  componentState: Record<string, unknown>
  currentView: string | null
  viewport: {
    width: number
    height: number
    scrollX: number
    scrollY: number
  }
  timestamp: string | null
}

export interface ComponentRegistration {
  name: string
  state: Record<string, unknown>
}

/**
 * UICapture - HTTP-based UI observation for agents
 *
 * Event-driven capture - no polling. Captures on:
 * - Page load
 * - State changes (call capture() after setState)
 * - User interactions (debounced)
 * - Explicit request
 */
export class UICapture {
  private static instance: UICapture | null = null
  private backendUrl: string = ''
  private registeredComponents: Map<string, Record<string, unknown>> = new Map()
  private initialized: boolean = false
  private pendingCapture: number | null = null
  private debounceMs: number = 100

  private constructor() {}

  /**
   * Get singleton instance
   */
  static getInstance(): UICapture {
    if (!UICapture.instance) {
      UICapture.instance = new UICapture()
    }
    return UICapture.instance
  }

  /**
   * Initialize the capture service
   *
   * @param backendUrl - Backend API URL (e.g., http://localhost:3101/api)
   */
  initialize(backendUrl: string): void {
    this.backendUrl = backendUrl
    this.initialized = true
    console.log(`[UICapture] Initialized with backend: ${backendUrl}`)

    // Capture initial state on page load
    this.capture()

    // Listen for user interactions (debounced)
    this.setupEventListeners()
  }

  /**
   * Setup event listeners for user interactions
   */
  private setupEventListeners(): void {
    // Capture on form input changes
    document.addEventListener('input', () => this.captureDebounced(), { passive: true })

    // Capture on clicks (may change UI state)
    document.addEventListener('click', () => this.captureDebounced(), { passive: true })

    // Capture on navigation
    window.addEventListener('hashchange', () => this.capture())
    window.addEventListener('popstate', () => this.capture())
  }

  /**
   * Debounced capture - prevents excessive captures during rapid events
   */
  private captureDebounced(): void {
    if (this.pendingCapture) {
      clearTimeout(this.pendingCapture)
    }
    this.pendingCapture = window.setTimeout(() => {
      this.capture()
      this.pendingCapture = null
    }, this.debounceMs)
  }

  /**
   * Capture UI state and POST to backend
   *
   * Call this after state changes to update the snapshot.
   */
  async capture(): Promise<void> {
    if (!this.initialized || !this.backendUrl) {
      return
    }

    try {
      const snapshot = this.buildSnapshot()
      await this.postSnapshot(snapshot)
    } catch (error) {
      console.error('[UICapture] Failed to capture:', error)
    }
  }

  /**
   * Register a component's state for capture
   *
   * Call this when component mounts or state changes.
   * Automatically triggers a capture.
   */
  registerComponent(name: string, state: Record<string, unknown>): void {
    this.registeredComponents.set(name, state)
    this.captureDebounced()
  }

  /**
   * Update a component's state
   *
   * Call this when component state changes.
   * Automatically triggers a capture.
   */
  updateComponent(name: string, state: Record<string, unknown>): void {
    this.registeredComponents.set(name, state)
    this.captureDebounced()
  }

  /**
   * Unregister a component
   */
  unregisterComponent(name: string): void {
    this.registeredComponents.delete(name)
  }

  /**
   * Build snapshot object
   */
  buildSnapshot(): Omit<UISnapshot, 'timestamp'> {
    return {
      htmlStructure: this.captureHtmlStructure(),
      visibleText: this.captureVisibleText(),
      inputValues: this.captureInputValues(),
      componentState: Object.fromEntries(this.registeredComponents),
      currentView: this.getCurrentView(),
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
        scrollX: window.scrollX,
        scrollY: window.scrollY,
      },
    }
  }

  /**
   * POST snapshot to backend
   */
  private async postSnapshot(snapshot: Omit<UISnapshot, 'timestamp'>): Promise<void> {
    const response = await fetch(`${this.backendUrl}/ui-snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(snapshot),
    })

    if (!response.ok) {
      throw new Error(`Failed to post snapshot: ${response.status}`)
    }
  }

  /**
   * Capture and POST a screenshot
   *
   * Call this only when a screenshot is needed - it's expensive.
   * Agent can trigger via POST /api/action with {"action": "capture_screenshot"}
   */
  async captureScreenshot(): Promise<void> {
    if (!this.initialized || !this.backendUrl) {
      console.warn('[UICapture] Not initialized')
      return
    }

    try {
      console.log('[UICapture] Capturing screenshot...')
      const canvas = await html2canvas(document.body, {
        logging: false,
        useCORS: true,
        scale: 1,
      })

      const imageData = canvas.toDataURL('image/png').split(',')[1]

      await fetch(`${this.backendUrl}/ui-screenshot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          imageData,
          width: canvas.width,
          height: canvas.height,
        }),
      })

      console.log(`[UICapture] Screenshot captured (${canvas.width}x${canvas.height})`)
    } catch (error) {
      console.error('[UICapture] Failed to capture screenshot:', error)
    }
  }

  /**
   * Capture simplified HTML structure
   */
  private captureHtmlStructure(): string {
    const simplify = (element: Element, depth: number = 0): string => {
      if (depth > 5) return ''
      if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(element.tagName)) return ''

      const tag = element.tagName.toLowerCase()
      const id = element.id ? `#${element.id}` : ''
      const classes = element.className && typeof element.className === 'string'
        ? `.${element.className.split(' ').filter(Boolean).join('.')}`
        : ''

      const children = Array.from(element.children)
        .map(child => simplify(child, depth + 1))
        .filter(Boolean)
        .join('')

      const indent = '  '.repeat(depth)
      if (children) {
        return `${indent}<${tag}${id}${classes}>\n${children}${indent}</${tag}>\n`
      }
      return `${indent}<${tag}${id}${classes}/>\n`
    }

    return simplify(document.body)
  }

  /**
   * Capture visible text content
   */
  private captureVisibleText(): string[] {
    const texts: string[] = []
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          const parent = node.parentElement
          if (!parent) return NodeFilter.FILTER_REJECT
          if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(parent.tagName)) {
            return NodeFilter.FILTER_REJECT
          }
          const text = node.textContent?.trim()
          if (!text) return NodeFilter.FILTER_REJECT
          return NodeFilter.FILTER_ACCEPT
        },
      }
    )

    let node: Node | null
    while ((node = walker.nextNode()) && texts.length < 100) {
      const text = node.textContent?.trim()
      if (text) {
        texts.push(text)
      }
    }

    return texts
  }

  /**
   * Capture form input values
   */
  private captureInputValues(): Record<string, string> {
    const values: Record<string, string> = {}
    const inputs = document.querySelectorAll('input, textarea, select')

    inputs.forEach((input, index) => {
      const element = input as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      const key = element.id || element.name || `input_${index}`
      values[key] = element.value || ''
    })

    return values
  }

  /**
   * Get current view/route
   */
  private getCurrentView(): string {
    return window.location.hash || window.location.pathname || document.title
  }

  /**
   * Check if initialized
   */
  isInitialized(): boolean {
    return this.initialized
  }
}

// Export singleton instance
export const uiCapture = UICapture.getInstance()
