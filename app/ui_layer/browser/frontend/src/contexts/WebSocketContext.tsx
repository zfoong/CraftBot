import React, { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react'
import type { ChatMessage, ActionItem, AgentStatus, InitialState, WSMessage, DashboardMetrics, TaskCancelResponse, FilteredDashboardMetrics, MetricsTimePeriod, OnboardingStep, OnboardingStepResponse, OnboardingSubmitResponse, OnboardingCompleteResponse, LocalLLMState, LocalLLMCheckResponse, LocalLLMTestResponse, LocalLLMInstallResponse, LocalLLMProgressResponse, LocalLLMPullProgressResponse, SuggestedModel } from '../types'
import { getWsUrl } from '../utils/connection'

// Pending attachment type for upload
interface PendingAttachment {
  name: string
  type: string
  size: number
  content: string  // base64
}

// Reply target for reply-to-chat/task feature
interface ReplyTarget {
  type: 'chat' | 'task'
  sessionId?: string       // May be undefined for old messages without session tracking
  displayName: string      // Truncated preview for UI display
  originalContent: string  // Full content for agent context
}

// Reply context sent with message
interface ReplyContext {
  sessionId?: string
  originalMessage: string
}

interface WebSocketState {
  connected: boolean
  version: string
  messages: ChatMessage[]
  actions: ActionItem[]
  status: AgentStatus
  guiMode: boolean
  currentTask: { id: string; name: string } | null
  footageUrl: string | null
  dashboardMetrics: DashboardMetrics | null
  filteredMetricsCache: Record<MetricsTimePeriod, FilteredDashboardMetrics | null>
  cancellingTaskId: string | null
  // Demo mode
  demoMode: boolean
  // Onboarding state
  needsHardOnboarding: boolean
  agentName: string
  agentProfilePictureUrl: string
  agentProfilePictureHasCustom: boolean
  onboardingStep: OnboardingStep | null
  onboardingError: string | null
  onboardingLoading: boolean
  // Unread message tracking
  lastSeenMessageId: string | null
  // Reply state for reply-to-chat/task feature
  replyTarget: ReplyTarget | null
  // Chat pagination
  hasMoreMessages: boolean
  loadingOlderMessages: boolean
  // Action pagination
  hasMoreActions: boolean
  loadingOlderActions: boolean
  // Local LLM (Ollama) state
  localLLM: LocalLLMState
}

interface WebSocketContextType extends WebSocketState {
  sendMessage: (content: string, attachments?: PendingAttachment[], replyContext?: ReplyContext) => void
  sendCommand: (command: string) => void
  clearMessages: () => void
  cancelTask: (taskId: string) => void
  openFile: (path: string) => void
  openFolder: (path: string) => void
  requestFilteredMetrics: (period: MetricsTimePeriod) => void
  subscribeDashboardMetrics: () => void
  unsubscribeDashboardMetrics: () => void
  // Onboarding methods
  requestOnboardingStep: () => void
  submitOnboardingStep: (value: string | string[]) => void
  skipOnboardingStep: () => void
  goBackOnboardingStep: () => void
  // Unread message tracking
  markMessagesAsSeen: () => void
  // Reply-to-chat/task methods
  setReplyTarget: (target: ReplyTarget) => void
  clearReplyTarget: () => void
  // Chat pagination
  loadOlderMessages: () => void
  // Action pagination
  loadOlderActions: () => void
  // Local LLM (Ollama) methods
  checkLocalLLM: () => void
  testLocalLLMConnection: (url: string) => void
  installLocalLLM: () => void
  startLocalLLM: () => void
  requestSuggestedModels: () => void
  pullOllamaModel: (model: string) => void
  // Option click (interactive buttons in chat)
  sendOptionClick: (value: string, sessionId?: string, messageId?: string) => void
  // Agent profile picture
  uploadAgentProfilePicture: (name: string, mimeType: string, contentBase64: string) => void
  removeAgentProfilePicture: () => void
}

// Initialize lastSeenMessageId from localStorage
const getInitialLastSeenMessageId = (): string | null => {
  try {
    return localStorage.getItem('lastSeenMessageId')
  } catch {
    return null
  }
}

const defaultState: WebSocketState = {
  connected: false,
  version: '',
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
  dashboardMetrics: null,
  filteredMetricsCache: {
    '1h': null,
    '1d': null,
    '1w': null,
    '1m': null,
    'total': null,
  },
  cancellingTaskId: null,
  // Demo mode
  demoMode: false,
  // Onboarding state
  needsHardOnboarding: false,
  agentName: 'Agent',
  agentProfilePictureUrl: '/api/agent-profile-picture',
  agentProfilePictureHasCustom: false,
  onboardingStep: null,
  onboardingError: null,
  onboardingLoading: false,
  // Unread message tracking
  lastSeenMessageId: getInitialLastSeenMessageId(),
  // Reply state
  replyTarget: null,
  // Chat pagination
  hasMoreMessages: true,
  loadingOlderMessages: false,
  // Action pagination
  hasMoreActions: true,
  loadingOlderActions: false,
  // Local LLM (Ollama) state
  localLLM: {
    phase: 'idle',
    defaultUrl: 'http://localhost:11434',
    installProgress: [],
    pullProgress: [],
    pullBytes: null,
    suggestedModels: [],
  },
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WebSocketState>(defaultState)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const isConnectingRef = useRef<boolean>(false)
  const reconnectCountRef = useRef<number>(0)
  const maxReconnectAttemptsRef = useRef<number>(10)

  const connect = useCallback(() => {
    // Prevent duplicate connections (React StrictMode calls useEffect twice)
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    isConnectingRef.current = true

    // Close any existing connection before creating new one
    if (wsRef.current) {
      try {
        wsRef.current.close()
      } catch (e) {
        // Connection already closed
      }
      wsRef.current = null
    }

    const wsUrl = getWsUrl()

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[WS] Connected')
        isConnectingRef.current = false
        reconnectCountRef.current = 0  // Reset reconnect counter on successful connection
        setState(prev => ({ ...prev, connected: true }))
      }

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data)
          handleMessage(msg)
        } catch (err) {
          console.error('[WS] Failed to parse message:', err, 'Raw:', event.data)
        }
      }

      ws.onclose = (event) => {
        console.log('[WS] Disconnected, code:', event.code, 'reason:', event.reason, 'wasClean:', event.wasClean, 'reconnectCount:', reconnectCountRef.current)
        isConnectingRef.current = false
        setState(prev => ({
          ...prev,
          connected: false,
          status: { ...prev.status, message: 'Disconnected. Reconnecting...' },
        }))

        // Immediate first retry, then exponential backoff
        let reconnectDelay = 500
        if (reconnectCountRef.current > 0) {
          // Exponential backoff after first disconnect
          reconnectDelay = Math.min(1000 * Math.pow(1.5, reconnectCountRef.current - 1), 30000)
        }
        reconnectCountRef.current += 1

        if (reconnectCountRef.current <= maxReconnectAttemptsRef.current) {
          console.log(`[WS] Reconnection attempt ${reconnectCountRef.current}/${maxReconnectAttemptsRef.current} in ${reconnectDelay}ms`)
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect()
          }, reconnectDelay)
        } else {
          console.error(`[WS] Failed to reconnect after ${maxReconnectAttemptsRef.current} attempts`)
          setState(prev => ({
            ...prev,
            status: { ...prev.status, message: 'Connection failed - please refresh the page' },
          }))
        }
      }

      ws.onerror = (err) => {
        console.error('[WS] Error:', err, '(Error object might be limited on some browsers)')
        // Note: On some browsers, WebSocket error events don't contain detailed info
        // The onclose handler will be called after onerror
      }
    } catch (err) {
      console.error('[WS] Failed to create WebSocket:', err)
      isConnectingRef.current = false
      // Retry connection
      reconnectCountRef.current += 1
      const reconnectDelay = Math.min(1000 * Math.pow(1.5, reconnectCountRef.current), 30000)
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, reconnectDelay)
    }
  }, [])

  const handleMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'init': {
        const data = msg.data as unknown as InitialState
        const initMessages = data.messages || []
        const initActions = data.actions || []
        setState(prev => ({
          ...prev,
          version: data.version || '',
          messages: initMessages,
          actions: initActions,
          status: {
            state: data.agentState || 'idle',
            message: data.status || 'Ready',
            loading: false,
          },
          guiMode: data.guiMode || false,
          currentTask: data.currentTask || null,
          dashboardMetrics: data.dashboardMetrics || null,
          demoMode: data.demoMode || false,
          needsHardOnboarding: data.needsHardOnboarding || false,
          agentName: data.agentName || 'Agent',
          agentProfilePictureUrl:
            (data as InitialState & { agentProfilePictureUrl?: string }).agentProfilePictureUrl
            || '/api/agent-profile-picture',
          agentProfilePictureHasCustom:
            (data as InitialState & { agentProfilePictureHasCustom?: boolean }).agentProfilePictureHasCustom
            || false,
          hasMoreMessages: initMessages.length >= 50,
          hasMoreActions: initActions.filter((a: ActionItem) => a.itemType === 'task').length >= 15,
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

      case 'chat_history': {
        const data = msg.data as unknown as { messages: ChatMessage[]; hasMore: boolean }
        setState(prev => ({
          ...prev,
          messages: [...(data.messages || []), ...prev.messages],
          hasMoreMessages: data.hasMore,
          loadingOlderMessages: false,
        }))
        break
      }

      case 'chat_clear':
        setState(prev => ({ ...prev, messages: [], hasMoreMessages: false }))
        break

      case 'action_history': {
        const data = msg.data as unknown as { actions: ActionItem[]; hasMore: boolean }
        setState(prev => ({
          ...prev,
          actions: [...(data.actions || []), ...prev.actions],
          hasMoreActions: data.hasMore,
          loadingOlderActions: false,
        }))
        break
      }

      case 'action_add': {
        const action = msg.data as unknown as ActionItem
        setState(prev => {
          // Prevent duplicate items by ID only
          const existingItem = prev.actions.find(a => a.id === action.id)
          if (existingItem) {
            // Update existing item's status if different
            if (existingItem.status !== action.status) {
              return {
                ...prev,
                actions: prev.actions.map(a =>
                  a.id === action.id ? { ...a, status: action.status } : a
                ),
              }
            }
            return prev // No change needed
          }
          return {
            ...prev,
            actions: [...prev.actions, action],
          }
        })
        break
      }

      case 'action_update': {
        const { id, status, duration, output, error } = msg.data as {
          id: string
          status: string
          duration?: number
          output?: string
          error?: string
        }
        setState(prev => ({
          ...prev,
          actions: prev.actions.map(a =>
            a.id === id
              ? { ...a, status: status as ActionItem['status'], duration, output, error }
              : a
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

      case 'dashboard_metrics': {
        const metrics = msg.data as unknown as DashboardMetrics
        setState(prev => ({ ...prev, dashboardMetrics: metrics }))
        break
      }

      case 'dashboard_filtered_metrics': {
        const metrics = msg.data as unknown as FilteredDashboardMetrics
        // Cache by period so each card can have independent data
        setState(prev => ({
          ...prev,
          filteredMetricsCache: {
            ...prev.filteredMetricsCache,
            [metrics.period]: metrics,
          },
        }))
        break
      }

      case 'task_cancel_response': {
        const response = msg.data as unknown as TaskCancelResponse
        if (response.success) {
          // Update the task status to cancelled
          setState(prev => ({
            ...prev,
            cancellingTaskId: null,
            actions: prev.actions.map(a =>
              a.id === response.taskId
                ? { ...a, status: 'cancelled' as const }
                : a
            ),
          }))
        } else {
          // Cancel failed, reset cancelling state
          setState(prev => ({ ...prev, cancellingTaskId: null }))
        }
        break
      }

      // Onboarding message handlers
      case 'onboarding_step': {
        const response = msg.data as unknown as OnboardingStepResponse
        if (response.success) {
          if (response.completed) {
            // Onboarding already complete
            setState(prev => ({
              ...prev,
              needsHardOnboarding: false,
              onboardingStep: null,
              onboardingLoading: false,
              onboardingError: null,
            }))
          } else if (response.step) {
            setState(prev => ({
              ...prev,
              onboardingStep: response.step!,
              onboardingLoading: false,
              onboardingError: null,
            }))
          }
        } else {
          setState(prev => ({
            ...prev,
            onboardingError: response.error || 'Failed to get step',
            onboardingLoading: false,
          }))
        }
        break
      }

      case 'onboarding_submit': {
        const response = msg.data as unknown as OnboardingSubmitResponse
        if (response.success && response.nextStep) {
          setState(prev => ({
            ...prev,
            onboardingStep: response.nextStep!,
            onboardingLoading: false,
            onboardingError: null,
          }))
        } else if (!response.success) {
          setState(prev => ({
            ...prev,
            onboardingError: response.error || 'Failed to submit',
            onboardingLoading: false,
          }))
        }
        break
      }

      case 'onboarding_skip': {
        const response = msg.data as unknown as OnboardingSubmitResponse
        if (response.success && response.nextStep) {
          setState(prev => ({
            ...prev,
            onboardingStep: response.nextStep!,
            onboardingLoading: false,
            onboardingError: null,
          }))
        } else if (!response.success) {
          setState(prev => ({
            ...prev,
            onboardingError: response.error || 'Cannot skip this step',
            onboardingLoading: false,
          }))
        }
        break
      }

      case 'onboarding_back': {
        const response = msg.data as unknown as { success: boolean; step?: OnboardingStep; error?: string }
        if (response.success && response.step) {
          setState(prev => ({
            ...prev,
            onboardingStep: response.step!,
            onboardingLoading: false,
            onboardingError: null,
          }))
        } else if (!response.success) {
          setState(prev => ({
            ...prev,
            onboardingError: response.error || 'Cannot go back',
            onboardingLoading: false,
          }))
        }
        break
      }

      case 'onboarding_complete': {
        const response = msg.data as unknown as OnboardingCompleteResponse & {
          agentProfilePictureUrl?: string
          agentProfilePictureHasCustom?: boolean
        }
        if (response.success) {
          setState(prev => ({
            ...prev,
            needsHardOnboarding: false,
            onboardingStep: null,
            onboardingLoading: false,
            onboardingError: null,
            agentName: response.agentName || 'Agent',
            agentProfilePictureUrl:
              response.agentProfilePictureUrl || prev.agentProfilePictureUrl,
            agentProfilePictureHasCustom:
              response.agentProfilePictureHasCustom ?? prev.agentProfilePictureHasCustom,
          }))
        }
        break
      }

      case 'agent_profile_picture_upload': {
        const r = msg.data as unknown as {
          success: boolean
          url?: string
          has_custom?: boolean
          error?: string
        }
        if (r.success && r.url) {
          setState(prev => ({
            ...prev,
            agentProfilePictureUrl: r.url!,
            agentProfilePictureHasCustom: r.has_custom ?? true,
          }))
        }
        break
      }

      case 'agent_profile_picture_remove': {
        const r = msg.data as unknown as {
          success: boolean
          url?: string
          has_custom?: boolean
        }
        if (r.success) {
          setState(prev => ({
            ...prev,
            agentProfilePictureUrl: r.url || '/api/agent-profile-picture',
            agentProfilePictureHasCustom: r.has_custom ?? false,
          }))
        }
        break
      }

      // ── Local LLM (Ollama) ───────────────────────────────────────────────
      case 'local_llm_check': {
        const r = msg.data as unknown as LocalLLMCheckResponse
        // Phases that must not be overridden by a background check result
        const BUSY_PHASES: LocalLLMState['phase'][] = ['installing', 'starting', 'pulling_model']
        if (!r.success) {
          setState(prev => {
            if (BUSY_PHASES.includes(prev.localLLM.phase)) return prev
            return { ...prev, localLLM: { ...prev.localLLM, phase: 'error', error: r.error } }
          })
          break
        }
        let phase: LocalLLMState['phase']
        if (r.running) {
          phase = 'running'
        } else if (r.installed) {
          phase = 'not_running'
        } else {
          phase = 'not_installed'
        }
        setState(prev => {
          if (BUSY_PHASES.includes(prev.localLLM.phase)) return prev
          return {
            ...prev,
            localLLM: {
              ...prev.localLLM,
              phase,
              version: r.version,
              defaultUrl: r.default_url || 'http://localhost:11434',
              error: undefined,
              testResult: undefined,
            },
          }
        })
        break
      }

      case 'local_llm_test': {
        const r = msg.data as unknown as LocalLLMTestResponse
        if (r.success && (!r.models || r.models.length === 0)) {
          // Connected but no models — ask user to pick one
          setState(prev => ({
            ...prev,
            localLLM: {
              ...prev.localLLM,
              phase: 'selecting_model',
              testResult: { success: r.success, message: r.message, error: r.error, models: r.models },
            },
          }))
          wsRef.current?.send(JSON.stringify({ type: 'local_llm_suggested_models' }))
        } else {
          setState(prev => ({
            ...prev,
            localLLM: {
              ...prev.localLLM,
              phase: r.success ? 'connected' : prev.localLLM.phase,
              testResult: { success: r.success, message: r.message, error: r.error, models: r.models },
            },
          }))
        }
        break
      }

      case 'local_llm_install_progress': {
        const r = msg.data as unknown as LocalLLMProgressResponse
        setState(prev => ({
          ...prev,
          localLLM: {
            ...prev.localLLM,
            installProgress: [...prev.localLLM.installProgress, r.message],
          },
        }))
        break
      }

      case 'local_llm_install': {
        const r = msg.data as unknown as LocalLLMInstallResponse
        if (r.success) {
          // Trigger a status check instead of assuming 'not_running' —
          // the installer may have auto-launched Ollama already
          setState(prev => ({ ...prev, localLLM: { ...prev.localLLM, phase: 'checking', installProgress: [] } }))
          wsRef.current?.send(JSON.stringify({ type: 'local_llm_check' }))
        } else {
          setState(prev => ({
            ...prev,
            localLLM: { ...prev.localLLM, phase: 'error', error: r.error ?? 'Installation failed' },
          }))
        }
        break
      }

      case 'local_llm_start': {
        const r = msg.data as unknown as LocalLLMInstallResponse
        setState(prev => ({
          ...prev,
          localLLM: {
            ...prev.localLLM,
            phase: r.success ? 'running' : 'error',
            error: r.success ? undefined : (r.error ?? 'Failed to start Ollama'),
            testResult: undefined,
          },
        }))
        break
      }

      case 'local_llm_suggested_models': {
        const r = msg.data as unknown as { models: SuggestedModel[] }
        setState(prev => ({ ...prev, localLLM: { ...prev.localLLM, suggestedModels: r.models } }))
        break
      }

      case 'local_llm_pull_progress': {
        const r = msg.data as unknown as LocalLLMPullProgressResponse
        setState(prev => {
          // Only append to the log for non-byte-progress status lines
          const isDownloading = r.total > 0
          const newLog = isDownloading
            ? prev.localLLM.pullProgress  // don't spam log with repeated byte updates
            : r.message && !prev.localLLM.pullProgress.includes(r.message)
              ? [...prev.localLLM.pullProgress, r.message]
              : prev.localLLM.pullProgress
          return {
            ...prev,
            localLLM: {
              ...prev.localLLM,
              pullProgress: newLog,
              pullBytes: isDownloading
                ? { completed: r.completed, total: r.total, percent: r.percent }
                : prev.localLLM.pullBytes,
            },
          }
        })
        break
      }

      case 'local_llm_pull_model': {
        const r = msg.data as unknown as LocalLLMInstallResponse & { model?: string }
        if (r.success) {
          // Re-test to refresh model count and advance to 'connected'
          setState(prev => {
            wsRef.current?.send(JSON.stringify({ type: 'local_llm_test', url: prev.localLLM.defaultUrl }))
            return { ...prev, localLLM: { ...prev.localLLM, pullProgress: [], error: undefined } }
          })
        } else {
          setState(prev => ({
            ...prev,
            localLLM: { ...prev.localLLM, phase: 'error', error: r.error ?? 'Model download failed' },
          }))
        }
        break
      }
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      // Reset connecting flag on cleanup
      isConnectingRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  const loadOlderMessages = useCallback(() => {
    if (!state.hasMoreMessages || state.loadingOlderMessages || state.messages.length === 0) return
    if (wsRef.current?.readyState !== WebSocket.OPEN) return

    const oldestTimestamp = state.messages[0]?.timestamp
    if (!oldestTimestamp) return

    setState(prev => ({ ...prev, loadingOlderMessages: true }))
    wsRef.current.send(JSON.stringify({
      type: 'chat_history',
      beforeTimestamp: oldestTimestamp,
      limit: 50,
    }))
  }, [state.hasMoreMessages, state.loadingOlderMessages, state.messages])

  const loadOlderActions = useCallback(() => {
    if (!state.hasMoreActions || state.loadingOlderActions || state.actions.length === 0) return
    if (wsRef.current?.readyState !== WebSocket.OPEN) return

    // Find the oldest task's createdAt (not action) for the before_timestamp
    const oldestTask = state.actions.find(a => a.itemType === 'task')
    const oldestCreatedAt = oldestTask?.createdAt || state.actions[0]?.createdAt
    if (!oldestCreatedAt) return

    setState(prev => ({ ...prev, loadingOlderActions: true }))
    wsRef.current.send(JSON.stringify({
      type: 'action_history',
      beforeTimestamp: oldestCreatedAt,
      limit: 15,
    }))
  }, [state.hasMoreActions, state.loadingOlderActions, state.actions])

  const sendMessage = useCallback((content: string, attachments?: PendingAttachment[], replyContext?: ReplyContext) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const payload = {
          type: 'message',
          content,
          attachments: attachments || [],
          replyContext: replyContext || null,
        }
        const payloadStr = JSON.stringify(payload)
        console.log('[WebSocket] Sending message, payload size:', payloadStr.length, 'bytes, attachments:', attachments?.length || 0)
        wsRef.current.send(payloadStr)
        console.log('[WebSocket] Message sent successfully')
      } catch (error) {
        console.error('[WebSocket] Error sending message:', error)
      }
    } else {
      console.warn('[WebSocket] Cannot send message - WebSocket not open, state:', wsRef.current?.readyState)
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

  const cancelTask = useCallback((taskId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({ ...prev, cancellingTaskId: taskId }))
      wsRef.current.send(JSON.stringify({ type: 'task_cancel', taskId }))
    }
  }, [])

  const sendOptionClick = useCallback((value: string, sessionId?: string, messageId?: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'option_click', value, sessionId, messageId }))
    }
  }, [])

  const uploadAgentProfilePicture = useCallback(
    (name: string, mimeType: string, contentBase64: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'agent_profile_picture_upload',
          name,
          mimeType,
          content: contentBase64,
        }))
      }
    },
    []
  )

  const removeAgentProfilePicture = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'agent_profile_picture_remove' }))
    }
  }, [])

  const openFile = useCallback((path: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'open_file', path }))
    }
  }, [])

  const openFolder = useCallback((path: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'open_folder', path }))
    }
  }, [])

  const requestFilteredMetrics = useCallback((period: MetricsTimePeriod) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'dashboard_metrics_filter',
        period
      }))
    }
  }, [])

  const subscribeDashboardMetrics = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe_dashboard_metrics' }))
    }
  }, [])

  const unsubscribeDashboardMetrics = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'unsubscribe_dashboard_metrics' }))
    }
  }, [])

  // Onboarding methods
  const requestOnboardingStep = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({ ...prev, onboardingLoading: true, onboardingError: null }))
      wsRef.current.send(JSON.stringify({ type: 'onboarding_step_get' }))
    }
  }, [])

  const submitOnboardingStep = useCallback((value: string | string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({ ...prev, onboardingLoading: true, onboardingError: null }))
      wsRef.current.send(JSON.stringify({ type: 'onboarding_step_submit', value }))
    }
  }, [])

  const skipOnboardingStep = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({ ...prev, onboardingLoading: true, onboardingError: null }))
      wsRef.current.send(JSON.stringify({ type: 'onboarding_skip' }))
    }
  }, [])

  const goBackOnboardingStep = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({ ...prev, onboardingLoading: true, onboardingError: null }))
      wsRef.current.send(JSON.stringify({ type: 'onboarding_back' }))
    }
  }, [])

  // Mark all current messages as seen
  const markMessagesAsSeen = useCallback(() => {
    setState(prev => {
      if (prev.messages.length > 0) {
        const lastId = prev.messages[prev.messages.length - 1].messageId
        if (lastId && lastId !== prev.lastSeenMessageId) {
          try {
            localStorage.setItem('lastSeenMessageId', lastId)
          } catch {
            // localStorage may be unavailable
          }
          return { ...prev, lastSeenMessageId: lastId }
        }
      }
      return prev
    })
  }, [])

  // Set reply target for reply-to-chat/task feature
  const setReplyTarget = useCallback((target: ReplyTarget) => {
    setState(prev => ({ ...prev, replyTarget: target }))
  }, [])

  // Clear reply target
  const clearReplyTarget = useCallback(() => {
    setState(prev => ({ ...prev, replyTarget: null }))
  }, [])

  // Local LLM (Ollama) methods
  const checkLocalLLM = useCallback(() => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return
    const BUSY_PHASES: LocalLLMState['phase'][] = ['installing', 'starting', 'pulling_model']
    setState(prev => {
      if (BUSY_PHASES.includes(prev.localLLM.phase)) return prev  // Don't interrupt active ops
      return { ...prev, localLLM: { ...prev.localLLM, phase: 'checking', error: undefined } }
    })
    wsRef.current.send(JSON.stringify({ type: 'local_llm_check' }))
  }, [])

  const testLocalLLMConnection = useCallback((url: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'local_llm_test', url }))
    }
  }, [])

  const installLocalLLM = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({
        ...prev,
        localLLM: { ...prev.localLLM, phase: 'installing', installProgress: [], error: undefined },
      }))
      wsRef.current.send(JSON.stringify({ type: 'local_llm_install' }))
    } else {
      setState(prev => ({
        ...prev,
        localLLM: { ...prev.localLLM, phase: 'error', error: 'Not connected — please wait a moment and retry.' },
      }))
    }
  }, [])

  const startLocalLLM = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({ ...prev, localLLM: { ...prev.localLLM, phase: 'starting', error: undefined } }))
      wsRef.current.send(JSON.stringify({ type: 'local_llm_start' }))
    }
  }, [])

  const requestSuggestedModels = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'local_llm_suggested_models' }))
    }
  }, [])

  const pullOllamaModel = useCallback((model: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setState(prev => ({
        ...prev,
        localLLM: { ...prev.localLLM, phase: 'pulling_model', pullProgress: [], pullBytes: null, error: undefined },
      }))
      wsRef.current.send(JSON.stringify({ type: 'local_llm_pull_model', model }))
    }
  }, [])

  return (
    <WebSocketContext.Provider
      value={{
        ...state,
        sendMessage,
        sendCommand,
        clearMessages,
        cancelTask,
        openFile,
        openFolder,
        requestFilteredMetrics,
        subscribeDashboardMetrics,
        unsubscribeDashboardMetrics,
        requestOnboardingStep,
        submitOnboardingStep,
        skipOnboardingStep,
        goBackOnboardingStep,
        markMessagesAsSeen,
        setReplyTarget,
        clearReplyTarget,
        loadOlderMessages,
        loadOlderActions,
        checkLocalLLM,
        testLocalLLMConnection,
        installLocalLLM,
        startLocalLLM,
        requestSuggestedModels,
        pullOllamaModel,
        sendOptionClick,
        uploadAgentProfilePicture,
        removeAgentProfilePicture,
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
