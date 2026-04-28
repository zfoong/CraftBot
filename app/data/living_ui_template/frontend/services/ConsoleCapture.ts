/**
 * ConsoleCapture - Captures browser console output for agent debugging
 *
 * Intercepts console.error, console.warn (always), and console.log
 * (only app-prefixed messages). Sends captured entries to the backend
 * via POST /api/logs for persistent storage.
 *
 * Filters out noise: React internals, Vite HMR, browser-generated messages.
 */

const BACKEND_URL = (window as any).__CRAFTBOT_BACKEND_URL__ || 'http://localhost:{{BACKEND_PORT}}'

// Prefixes that indicate agent-written or app-level console.log messages
const APP_LOG_PREFIXES = [
  '[App',
  '[AppController',
  '[ApiService',
  '[Main',
  '[Component',
  '[UI',
  '[State',
  '[Controller',
  '[Service',
  '[Error',
  '[Debug',
]

// Patterns to filter OUT from errors/warnings (noise)
const NOISE_PATTERNS = [
  /\[HMR\]/,
  /\[vite\]/,
  /hot update/i,
  /hmr/i,
  /DevTools/,
  /Download the React DevTools/,
  /React does not recognize/,
  /Warning: Each child in a list/,
  /Warning: validateDOMNesting/,
  /Manifest: Line/,
  /favicon\.ico/,
  /net::ERR_/,
]

interface LogEntry {
  level: string
  message: string
  timestamp: string
}

// Buffer to batch log entries (avoid spamming the backend)
let buffer: LogEntry[] = []
let flushTimer: ReturnType<typeof setTimeout> | null = null
const FLUSH_INTERVAL_MS = 2000
const MAX_BUFFER_SIZE = 20

// Store original console methods
const originalConsole = {
  log: console.log.bind(console),
  warn: console.warn.bind(console),
  error: console.error.bind(console),
}

function isNoise(message: string): boolean {
  return NOISE_PATTERNS.some(pattern => pattern.test(message))
}

function isAppLog(message: string): boolean {
  return APP_LOG_PREFIXES.some(prefix => message.startsWith(prefix))
}

function stringifyArgs(args: unknown[]): string {
  return args
    .map(arg => {
      if (typeof arg === 'string') return arg
      // Error objects don't serialize with JSON.stringify — extract message + stack
      if (arg instanceof Error) {
        return `${arg.name}: ${arg.message}${arg.stack ? '\n' + arg.stack : ''}`
      }
      try {
        const json = JSON.stringify(arg)
        // If JSON.stringify returns '{}' for a non-empty object, fall back to String()
        if (json === '{}' && arg && typeof arg === 'object' && Object.keys(arg as object).length === 0) {
          return String(arg)
        }
        return json
      } catch {
        return String(arg)
      }
    })
    .join(' ')
}

function addEntry(level: string, args: unknown[]) {
  const message = stringifyArgs(args)

  // Filter noise (but never filter network/error entries)
  if (level !== 'network' && level !== 'error' && isNoise(message)) return

  // For console.log, only capture app-prefixed messages
  if (level === 'log' && !isAppLog(message)) return

  // Cap message length: full for errors, truncated for others
  const maxLen = level === 'error' ? 10000 : 2000

  buffer.push({
    level,
    message: message.slice(0, maxLen),
    timestamp: new Date().toISOString(),
  })

  // Flush if buffer is full
  if (buffer.length >= MAX_BUFFER_SIZE) {
    flush()
  } else if (!flushTimer) {
    flushTimer = setTimeout(flush, FLUSH_INTERVAL_MS)
  }
}

function flush() {
  if (flushTimer) {
    clearTimeout(flushTimer)
    flushTimer = null
  }

  if (buffer.length === 0) return

  const entries = [...buffer]
  buffer = []

  // Send to backend — fire and forget, don't block the UI
  fetch(`${BACKEND_URL}/api/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entries }),
  }).catch(() => {
    // Silently ignore — backend might not be running yet
    // Use original console to avoid recursion
    originalConsole.log('[ConsoleCapture] Failed to send logs to backend')
  })
}

/**
 * Start capturing console output.
 * Call once at app startup (e.g., in main.tsx).
 */
export function startConsoleCapture() {
  console.log = (...args: unknown[]) => {
    originalConsole.log(...args)
    addEntry('log', args)
  }

  console.warn = (...args: unknown[]) => {
    originalConsole.warn(...args)
    addEntry('warn', args)
  }

  console.error = (...args: unknown[]) => {
    originalConsole.error(...args)
    addEntry('error', args)
  }

  // Also capture unhandled errors
  window.addEventListener('error', (event) => {
    addEntry('error', [`Unhandled error: ${event.message} at ${event.filename}:${event.lineno}:${event.colno}`])
  })

  // Capture unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    addEntry('error', [`Unhandled promise rejection: ${event.reason}`])
  })

  // Intercept fetch for network request/response logging
  const originalFetch = window.fetch.bind(window)
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const method = init?.method || 'GET'
    const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
    const requestBody = init?.body ? String(init.body) : undefined

    // Skip logging our own log endpoint to avoid recursion
    if (url.includes('/api/logs')) {
      return originalFetch(input, init)
    }

    const startTime = performance.now()

    try {
      const response = await originalFetch(input, init)
      const duration = Math.round(performance.now() - startTime)
      const clonedResponse = response.clone()

      let responseBody = ''
      try {
        responseBody = await clonedResponse.text()
      } catch {
        responseBody = '(could not read response body)'
      }

      const isError = response.status >= 400
      const truncate = (s: string, max: number) => s.length > max ? s.slice(0, max) + '...(truncated)' : s

      const logParts = [
        `${method} ${url} → ${response.status} (${duration}ms)`,
      ]
      if (requestBody) {
        logParts.push(`  Request: ${isError ? requestBody : truncate(requestBody, 1000)}`)
      }
      if (responseBody) {
        logParts.push(`  Response: ${isError ? responseBody : truncate(responseBody, 1000)}`)
      }

      addEntry(isError ? 'error' : 'network', [logParts.join('\n')])

      return response
    } catch (error) {
      const duration = Math.round(performance.now() - startTime)
      const errMsg = error instanceof Error ? `${error.name}: ${error.message}` : String(error)

      const logParts = [
        `${method} ${url} → FAILED (${duration}ms): ${errMsg}`,
      ]
      if (requestBody) {
        logParts.push(`  Request: ${requestBody}`)
      }

      addEntry('error', [logParts.join('\n')])

      throw error
    }
  }

  // Flush on page unload
  window.addEventListener('beforeunload', flush)

  originalConsole.log('[ConsoleCapture] Started — capturing errors, warnings, app logs, and network requests')
}
