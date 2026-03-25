import { useEffect, useRef } from 'react'
import { AgentBridge } from './AgentBridge'

/**
 * useAgentAware - React hook to make a component agent-aware
 *
 * Registers the component with the StateReporter so the CraftBot agent
 * can "see" this component's state.
 *
 * @param componentName - Unique name for this component
 * @param state - Current state to report to agent
 * @returns The same state (for convenience)
 *
 * @example
 * function TodoList() {
 *   const [todos, setTodos] = useState([])
 *
 *   // Make todos visible to agent
 *   useAgentAware('TodoList', {
 *     todoCount: todos.length,
 *     items: todos.map(t => t.title)
 *   })
 *
 *   return <ul>...</ul>
 * }
 */
export function useAgentAware<T extends Record<string, unknown>>(
  componentName: string,
  state: T
): T {
  const previousState = useRef<T | null>(null)

  useEffect(() => {
    try {
      const bridge = AgentBridge.getInstance()
      const reporter = bridge.getStateReporter()

      // Register component on mount
      reporter.registerComponent(componentName, state)

      return () => {
        // Unregister component on unmount
        reporter.unregisterComponent(componentName)
      }
    } catch (error) {
      // AgentBridge not initialized yet - this is fine during SSR or initial render
      console.debug(`[useAgentAware] AgentBridge not ready for ${componentName}`)
    }
  }, [componentName])

  // Update state when it changes
  useEffect(() => {
    // Only update if state actually changed
    if (JSON.stringify(state) === JSON.stringify(previousState.current)) {
      return
    }

    previousState.current = state

    try {
      const bridge = AgentBridge.getInstance()
      const reporter = bridge.getStateReporter()
      reporter.updateComponentState(componentName, state)
    } catch (error) {
      // Ignore if not initialized
    }
  }, [componentName, state])

  return state
}

/**
 * useAgentCommand - React hook to listen for agent commands
 *
 * @param handler - Callback function when command is received
 *
 * @example
 * function MyComponent() {
 *   useAgentCommand((command) => {
 *     if (command.type === 'refresh') {
 *       fetchData()
 *     }
 *   })
 * }
 */
export function useAgentCommand(
  handler: (command: { type: string; payload: Record<string, unknown> }) => void
): void {
  useEffect(() => {
    try {
      const bridge = AgentBridge.getInstance()
      const unsubscribe = bridge.onCommand(handler)
      return unsubscribe
    } catch (error) {
      console.debug('[useAgentCommand] AgentBridge not ready')
      return () => {}
    }
  }, [handler])
}

/**
 * useAgentConnection - React hook to get agent connection status
 *
 * @returns boolean indicating if connected to CraftBot
 *
 * @example
 * function StatusIndicator() {
 *   const isConnected = useAgentConnection()
 *   return <span>{isConnected ? '🟢' : '🔴'}</span>
 * }
 */
export function useAgentConnection(): boolean {
  try {
    return AgentBridge.getInstance().isConnected()
  } catch {
    return false
  }
}
