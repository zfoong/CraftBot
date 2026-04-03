import React, { useState, useRef, useEffect, useCallback } from 'react'
import { X, Loader2, Reply } from 'lucide-react'
import { useWebSocket } from '../../contexts/WebSocketContext'
import { IconButton, StatusIndicator } from '../../components/ui'
import { Chat } from '../../components/Chat'
import styles from './ChatPage.module.css'

// Panel width limits
const DEFAULT_PANEL_WIDTH = 380
const MIN_PANEL_WIDTH = 200
const MAX_PANEL_WIDTH = 800

export function ChatPage() {
  const { messages, actions, connected, sendMessage, cancelTask, cancellingTaskId, openFile, openFolder, lastSeenMessageId, markMessagesAsSeen, replyTarget, setReplyTarget, clearReplyTarget, loadOlderMessages, hasMoreMessages, loadingOlderMessages } = useWebSocket()

  // Derive agent status from actions and messages
  const status = useDerivedAgentStatus({
    actions,
    messages,
    connected,
  })
  const [input, setInput] = useState('')
  const [pendingAttachments, setPendingAttachments] = useState<PendingAttachment[]>([])
  const [attachmentError, setAttachmentError] = useState<string | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Input history (terminal-style up/down arrow navigation)
  const inputHistoryRef = useRef<string[]>([])
  const historyIndexRef = useRef(-1)
  const draftRef = useRef('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Virtualization refs
  const parentRef = useRef<HTMLDivElement>(null)
  const hasScrolledRef = useRef(false)
  const prevMessageCountRef = useRef(0)
  const prevPathRef = useRef<string | null>(null)
  const wasNearBottomRef = useRef(true)
  const location = useLocation()

  // Resizable panel state
  const [panelWidth, setPanelWidth] = useState(DEFAULT_PANEL_WIDTH)
  const [isResizing, setIsResizing] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Handle resize drag
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }, [])

  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      const containerRect = containerRef.current.getBoundingClientRect()
      const newWidth = containerRect.right - e.clientX
      const clampedWidth = Math.min(Math.max(newWidth, MIN_PANEL_WIDTH), MAX_PANEL_WIDTH)
      setPanelWidth(clampedWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  // Handle reply from task panel
  const handleTaskReply = useCallback((taskId: string, taskName: string) => {
    setReplyTarget({
      type: 'task',
      sessionId: taskId,
      displayName: taskName,
      originalContent: `Task: ${taskName}`,
    })
  }, [setReplyTarget])

  const handleSend = () => {
    // Don't send if there are validation errors
    if (!attachmentValidation.valid) return

    if (input.trim() || pendingAttachments.length > 0) {
      // Save to input history
      if (input.trim()) {
        inputHistoryRef.current.push(input.trim())
      }
      historyIndexRef.current = -1
      draftRef.current = ''

      // Include reply context if replying to a message/task
      const replyContext = replyTarget ? {
        sessionId: replyTarget.sessionId,
        originalMessage: replyTarget.originalContent,
      } : undefined

      sendMessage(
        input.trim(),
        pendingAttachments.length > 0 ? pendingAttachments : undefined,
        replyContext
      )
      setInput('')
      setPendingAttachments([])
      setAttachmentError(null)
      clearReplyTarget()  // Clear reply target after sending
      // Reset textarea height after clearing input
      if (inputRef.current) {
        inputRef.current.style.height = 'auto'
      }
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      const history = inputHistoryRef.current
      // Only navigate history when input is empty (or already navigating history)
      if (history.length === 0) return
      if (historyIndexRef.current === -1 && input.trim() !== '') return

      if (e.key === 'ArrowUp') {
        e.preventDefault()
        if (historyIndexRef.current === -1) {
          historyIndexRef.current = history.length - 1
        } else if (historyIndexRef.current > 0) {
          historyIndexRef.current--
        }
        setInput(history[historyIndexRef.current])
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        if (historyIndexRef.current === -1) return
        if (historyIndexRef.current < history.length - 1) {
          historyIndexRef.current++
          setInput(history[historyIndexRef.current])
        } else {
          // Back to empty
          historyIndexRef.current = -1
          setInput('')
        }
      }
    }
  }

  const handleAttachClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    // Check if adding these files would exceed the count limit
    const totalFileCount = pendingAttachments.length + files.length
    if (totalFileCount > MAX_ATTACHMENT_COUNT) {
      setAttachmentError(`Maximum ${MAX_ATTACHMENT_COUNT} files allowed. You have ${pendingAttachments.length} file(s) and are trying to add ${files.length} more.`)
      e.target.value = ''
      return
    }

    const newAttachments: PendingAttachment[] = []
    let newTotalSize = pendingAttachments.reduce((sum, att) => sum + att.size, 0)

    for (let i = 0; i < files.length; i++) {
      const file = files[i]

      // Check individual file size (for very large files, recommend manual copy)
      if (file.size > MAX_TOTAL_SIZE_BYTES) {
        setAttachmentError(`File "${file.name}" (${formatFileSize(file.size)}) exceeds the 70MB limit. For very large files, please copy them directly to the agent workspace folder.`)
        e.target.value = ''
        return
      }

      // Check if adding this file would exceed total size limit
      if (newTotalSize + file.size > MAX_TOTAL_SIZE_BYTES) {
        setAttachmentError(`Adding "${file.name}" would exceed the 70MB total size limit. Current total: ${formatFileSize(newTotalSize)}. For large files, please copy them directly to the agent workspace folder.`)
        e.target.value = ''
        return
      }

      try {
        // Read file as base64
        const content = await readFileAsBase64(file)
        newAttachments.push({
          name: file.name,
          type: file.type || 'application/octet-stream',
          size: file.size,
          content,
        })
        newTotalSize += file.size
      } catch (error) {
        console.error('Failed to read file:', error)
        setAttachmentError(`Failed to read file "${file.name}". The file may be too large or inaccessible.`)
        e.target.value = ''
        return
      }
    }

    // Clear any previous error and add the attachments
    setAttachmentError(null)
    setPendingAttachments(prev => [...prev, ...newAttachments])

    // Reset file input so the same file can be selected again
    e.target.value = ''
  }

  const removeAttachment = (index: number) => {
    setPendingAttachments(prev => prev.filter((_, i) => i !== index))
    // Clear any error when removing files
    setAttachmentError(null)
  }

  // Helper to read file as base64
  const readFileAsBase64 = (file: globalThis.File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result as string
        // Remove data URL prefix (e.g., "data:image/png;base64,")
        const base64 = result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  }

  // Group actions by task
  const tasks = actions.filter(a => a.itemType === 'task')
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  const getActionsForTask = (taskId: string) =>
    actions.filter(a => a.itemType === 'action' && a.parentId === taskId)

  return (
    <div className={`${styles.chatPage} ${isResizing ? styles.resizing : ''}`} ref={containerRef}>
      {/* Chat Component */}
      <div className={styles.chatPanel}>
        <Chat />
      </div>

      {/* Resize Handle */}
      <div
        className={styles.resizeHandle}
        onMouseDown={handleMouseDown}
      />

      {/* Task/Action Panel */}
      <div className={styles.actionPanel} style={{ width: panelWidth, flexShrink: 0 }}>
        <div className={styles.panelHeader}>
          <h3>Tasks & Actions</h3>
        </div>
        <div className={styles.actionList}>
          {tasks.length === 0 ? (
            <div className={styles.emptyActions}>
              <p>No active tasks</p>
            </div>
          ) : (
            tasks.map(task => (
              <div key={task.id} className={styles.taskGroup}>
                <div
                  className={`${styles.taskItem} ${selectedTaskId === task.id ? styles.selected : ''}`}
                  onClick={() => setSelectedTaskId(
                    selectedTaskId === task.id ? null : task.id
                  )}
                >
                  <StatusIndicator status={task.status} size="sm" />
                  <span className={styles.taskName}>{task.name}</span>
                  {(task.status === 'running' || task.status === 'waiting') && (
                    <>
                      <IconButton
                        size="sm"
                        variant="ghost"
                        className={styles.taskReplyBtn}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleTaskReply(task.id, task.name)
                        }}
                        title="Reply to Task"
                        icon={<Reply size={12} />}
                      />
                      <IconButton
                        size="sm"
                        variant="ghost"
                        className={styles.taskCancelBtn}
                        onClick={(e) => {
                          e.stopPropagation()
                          cancelTask(task.id)
                        }}
                        disabled={cancellingTaskId === task.id}
                        title="Cancel Task"
                        icon={
                          cancellingTaskId === task.id ? (
                            <Loader2 size={12} className={styles.spinning} />
                          ) : (
                            <X size={12} />
                          )
                        }
                      />
                    </>
                  )}
                </div>
                {selectedTaskId === task.id && (
                  <div className={styles.actionsList}>
                    {getActionsForTask(task.id).map(action => (
                      <div key={action.id} className={styles.actionItem}>
                        <StatusIndicator status={action.status} size="sm" />
                        <span className={styles.actionName}>{action.name}</span>
                      </div>
                    ))}
                    {getActionsForTask(task.id).length === 0 && (
                      <div className={styles.noActions}>No actions yet</div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
