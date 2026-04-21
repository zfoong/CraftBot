import React, { useState, useRef, useEffect, useLayoutEffect, KeyboardEvent, useCallback, ChangeEvent, useMemo } from 'react'
import ReactDOM from 'react-dom'
import { Send, Paperclip, X, Loader2, File, AlertCircle, Reply, Mic, MicOff } from 'lucide-react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { useLocation, useNavigate } from 'react-router-dom'
import { useWebSocket } from '../../contexts/WebSocketContext'
import { Button, IconButton, StatusIndicator } from '../../components/ui'
import { useDerivedAgentStatus } from '../../hooks'
import { ChatMessageItem } from './ChatMessage'
import styles from './ChatPage.module.css'

// Pending attachment type
interface PendingAttachment {
  name: string
  type: string
  size: number
  content: string  // base64
}

const MIC_LANGUAGES = [
  { code: 'en-US', label: 'EN', full: 'English' },
  { code: 'ja-JP', label: 'JA', full: '日本語' },
  { code: 'zh-CN', label: 'ZH', full: '中文 (简体)' },
  { code: 'zh-TW', label: 'ZH-TW', full: '中文 (繁體)' },
  { code: 'ko-KR', label: 'KO', full: '한국어' },
  { code: 'ar-SA', label: 'AR', full: 'العربية' },
  { code: 'es-ES', label: 'ES', full: 'Español' },
  { code: 'fr-FR', label: 'FR', full: 'Français' },
  { code: 'de-DE', label: 'DE', full: 'Deutsch' },
  { code: 'pt-BR', label: 'PT', full: 'Português' },
  { code: 'hi-IN', label: 'HI', full: 'हिन्दी' },
  { code: 'ru-RU', label: 'RU', full: 'Русский' },
  { code: 'it-IT', label: 'IT', full: 'Italiano' },
]

// Panel width limits
const DEFAULT_PANEL_WIDTH = 380
const MIN_PANEL_WIDTH = 200
const MAX_PANEL_WIDTH = 800

// Attachment limits
// Backend WebSocket has 100MB limit, base64 encoding adds ~33% overhead
// So raw file limit should be ~70MB to stay safely under the WebSocket limit
const MAX_ATTACHMENT_COUNT = 10
const MAX_TOTAL_SIZE_BYTES = 70 * 1024 * 1024  // 70MB (leaves room for base64 encoding + JSON overhead)

// Format file size for display
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function ChatPage() {
  const { messages, actions, connected, sendMessage, cancelTask, cancellingTaskId, openFile, openFolder, lastSeenMessageId, markMessagesAsSeen, replyTarget, setReplyTarget, clearReplyTarget, loadOlderMessages, hasMoreMessages, loadingOlderMessages, sendOptionClick } = useWebSocket()
  const navigate = useNavigate()

  const handleOptionClick = useCallback((value: string, sessionId?: string, messageId?: string) => {
    if (value === 'llm_change_model') {
      navigate('/settings')
      return
    }
    sendOptionClick(value, sessionId, messageId)
  }, [navigate, sendOptionClick])

  // Derive agent status from actions and messages
  const status = useDerivedAgentStatus({
    actions,
    messages,
    connected,
  })
  const [input, setInput] = useState('')
  const [pendingAttachments, setPendingAttachments] = useState<PendingAttachment[]>([])
  const [attachmentError, setAttachmentError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [previewAttachment, setPreviewAttachment] = useState<PendingAttachment | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Input history (terminal-style up/down arrow navigation)
  const inputHistoryRef = useRef<string[]>([])
  const historyIndexRef = useRef(-1)
  const draftRef = useRef('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const [micLang, setMicLang] = useState(() => {
    const saved = localStorage.getItem('micLang')
    if (saved && MIC_LANGUAGES.some(l => l.code === saved)) return saved
    const browserLang = navigator.language || 'en-US'
    return MIC_LANGUAGES.some(l => l.code === browserLang) ? browserLang : 'en-US'
  })
  const [langOpen, setLangOpen] = useState(false)
  const langDropdownRef = useRef<HTMLDivElement>(null)

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

  // Compute attachment validation status
  const attachmentValidation = useMemo(() => {
    const totalSize = pendingAttachments.reduce((sum, att) => sum + att.size, 0)
    const count = pendingAttachments.length

    if (count > MAX_ATTACHMENT_COUNT) {
      return {
        valid: false,
        error: `Maximum ${MAX_ATTACHMENT_COUNT} files allowed. You have ${count} files.`
      }
    }
    if (totalSize > MAX_TOTAL_SIZE_BYTES) {
      return {
        valid: false,
        error: `Total size (${formatFileSize(totalSize)}) exceeds 70MB limit. Please remove some files or copy large files directly to the agent workspace.`
      }
    }
    return { valid: true, error: null }
  }, [pendingAttachments])

  // Setup virtualizer for efficient message rendering
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
    overscan: 5,
  })

  // Find first unread message index, returns -1 if no unread messages
  const getFirstUnreadIndex = useCallback(() => {
    if (!lastSeenMessageId) return -1  // No history, no unread tracking
    const lastSeenIdx = messages.findIndex(m => m.messageId === lastSeenMessageId)
    if (lastSeenIdx === -1) {
      return 0  // ID not found (stale) - treat all as unread, start from beginning
    }
    if (lastSeenIdx === messages.length - 1) {
      return -1  // Already at end, no unread
    }
    return lastSeenIdx + 1  // First unread is after last seen
  }, [messages, lastSeenMessageId])

  // Close language dropdown when clicking outside
  useEffect(() => {
    if (!langOpen) return
    const handler = (e: MouseEvent) => {
      if (langDropdownRef.current && !langDropdownRef.current.contains(e.target as Node)) {
        setLangOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [langOpen])

  // Close preview on Escape
  useEffect(() => {
    if (!previewAttachment) return
    const handler = (e: globalThis.KeyboardEvent) => { if (e.key === 'Escape') setPreviewAttachment(null) }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [previewAttachment])


  // Check if user is scrolled near the bottom
  const isNearBottom = useCallback(() => {
    const container = parentRef.current
    if (!container) return true
    const threshold = 100 // pixels from bottom
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold
  }, [])

  // Track scroll position continuously so we know where user was BEFORE new messages arrive
  // Also detect scroll-to-top to load older messages
  useEffect(() => {
    const container = parentRef.current
    if (!container) return

    const handleScroll = () => {
      wasNearBottomRef.current = isNearBottom()

      // Load older messages when scrolled near top
      if (container.scrollTop < 100 && hasMoreMessages && !loadingOlderMessages) {
        loadOlderMessages()
      }
    }

    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [isNearBottom, hasMoreMessages, loadingOlderMessages, loadOlderMessages])

  // Scroll to unread messages when entering chat page, smooth scroll for new messages only if near bottom
  useEffect(() => {
    if (messages.length === 0) return

    const isNavigatingToChat = prevPathRef.current !== null && prevPathRef.current !== '/' && location.pathname === '/'
    const isFirstLoad = prevPathRef.current === null
    const isNewMessage = messages.length > prevMessageCountRef.current
    const shouldScrollToUnread = (isFirstLoad || isNavigatingToChat) && !hasScrolledRef.current

    prevPathRef.current = location.pathname
    prevMessageCountRef.current = messages.length

    if (shouldScrollToUnread) {
      hasScrolledRef.current = true
      const firstUnreadIdx = getFirstUnreadIndex()
      const hasUnreadMessages = firstUnreadIdx !== -1
      // Wait for virtualizer to measure elements before scrolling
      setTimeout(() => {
        if (hasUnreadMessages) {
          // Scroll to first unread message at the top
          virtualizer.scrollToIndex(firstUnreadIdx, { align: 'start', behavior: 'auto' })
        } else {
          // All messages seen - scroll to bottom
          virtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'auto' })
        }
        markMessagesAsSeen()
      }, 50)
    } else if (isNewMessage && location.pathname === '/' && wasNearBottomRef.current) {
      // Only auto-scroll if user WAS near the bottom before new message arrived
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'smooth' })
      markMessagesAsSeen()
    }
  }, [messages.length, location.pathname, virtualizer, getFirstUnreadIndex, markMessagesAsSeen])

  // Reset scroll flag when navigating away from chat
  useEffect(() => {
    if (location.pathname !== '/') {
      hasScrolledRef.current = false
    }
  }, [location.pathname])

  // Auto-resize textarea based on content
  const adjustTextareaHeight = useCallback(() => {
    const textarea = inputRef.current
    if (textarea) {
      // Reset height to auto to get accurate scrollHeight
      textarea.style.height = 'auto'
      // Set height to scrollHeight (CSS max-height will clamp it)
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [])

  // Adjust textarea height when input changes (useLayoutEffect for synchronous DOM updates)
  useLayoutEffect(() => {
    adjustTextareaHeight()
  }, [input, adjustTextareaHeight])

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
      // Calculate width from right edge (since panel is on the right)
      const newWidth = containerRect.right - e.clientX
      // Clamp to min/max limits
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

  // Handle reply from chat message
  const handleChatReply = useCallback((
    sessionId: string | undefined,
    displayName: string,
    fullContent: string
  ) => {
    setReplyTarget({
      type: 'chat',
      sessionId,
      displayName,
      originalContent: fullContent,
    })
    inputRef.current?.focus()
  }, [setReplyTarget])

  // Handle reply from task panel
  const handleTaskReply = useCallback((taskId: string, taskName: string) => {
    setReplyTarget({
      type: 'task',
      sessionId: taskId,
      displayName: taskName,
      originalContent: `Task: ${taskName}`,
    })
    inputRef.current?.focus()
  }, [setReplyTarget])

  const toggleListening = useCallback(() => {
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }

    const SpeechRecognitionAPI = (window as typeof window & { SpeechRecognition?: typeof SpeechRecognition; webkitSpeechRecognition?: typeof SpeechRecognition }).SpeechRecognition
      || (window as typeof window & { SpeechRecognition?: typeof SpeechRecognition; webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition

    if (!SpeechRecognitionAPI) {
      alert('Speech recognition is not supported in this browser.')
      return
    }

    const recognition = new SpeechRecognitionAPI()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = micLang

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript
        }
      }
      if (finalTranscript) {
        setInput(prev => prev + (prev.endsWith(' ') || prev === '' ? '' : ' ') + finalTranscript)
        if (inputRef.current) {
          inputRef.current.style.height = 'auto'
          inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
        }
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setIsListening(false)
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        alert('Microphone access denied. Please allow microphone permission in your browser settings.')
      }
    }
    recognition.onend = () => setIsListening(false)

    recognitionRef.current = recognition
    recognition.start()
    setIsListening(true)
    inputRef.current?.focus()
  }, [isListening, micLang])

  // Stop mic if component unmounts while listening
  useEffect(() => {
    return () => { recognitionRef.current?.abort() }
  }, [])

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

      // Stop mic if still listening when message is sent
      if (isListening) {
        recognitionRef.current?.stop()
        setIsListening(false)
      }

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

  // Shared file processing used by file picker, paste, and drag-and-drop
  const processFiles = async (files: File[]) => {
    if (files.length === 0) return

    const totalFileCount = pendingAttachments.length + files.length
    if (totalFileCount > MAX_ATTACHMENT_COUNT) {
      setAttachmentError(`Maximum ${MAX_ATTACHMENT_COUNT} files allowed. You have ${pendingAttachments.length} file(s) and are trying to add ${files.length} more.`)
      return
    }

    const newAttachments: PendingAttachment[] = []
    let newTotalSize = pendingAttachments.reduce((sum, att) => sum + att.size, 0)

    for (const file of files) {
      if (file.size > MAX_TOTAL_SIZE_BYTES) {
        setAttachmentError(`File "${file.name}" (${formatFileSize(file.size)}) exceeds the 70MB limit. For very large files, please copy them directly to the agent workspace folder.`)
        return
      }

      if (newTotalSize + file.size > MAX_TOTAL_SIZE_BYTES) {
        setAttachmentError(`Adding "${file.name}" would exceed the 70MB total size limit. Current total: ${formatFileSize(newTotalSize)}. For large files, please copy them directly to the agent workspace folder.`)
        return
      }

      try {
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
        return
      }
    }

    setAttachmentError(null)
    setPendingAttachments(prev => [...prev, ...newAttachments])
  }

  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    await processFiles(Array.from(files))
    e.target.value = ''
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOver(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    await processFiles(files)
  }

  const handlePaste = async (e: React.ClipboardEvent) => {
    const files = Array.from(e.clipboardData.files)
    if (files.length === 0) return
    e.preventDefault()
    await processFiles(files)
  }


  const removeAttachment = (index: number) => {
    setPendingAttachments(prev => prev.filter((_, i) => i !== index))
    setAttachmentError(null)
  }

  const openPreview = (att: PendingAttachment) => {
    setPreviewAttachment(att)
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

  // Stable blob URL for PDF preview — only rebuilt when the attachment changes
  const pdfBlobUrl = useMemo(() => {
    if (!previewAttachment) return null
    const isPdf = previewAttachment.type === 'application/pdf' || previewAttachment.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) return null
    try {
      const bytes = Uint8Array.from(atob(previewAttachment.content), c => c.charCodeAt(0))
      const blob = new Blob([bytes], { type: 'application/pdf' })
      return URL.createObjectURL(blob)
    } catch { return null }
  }, [previewAttachment])

  // Revoke PDF blob URL when attachment changes or modal closes
  useEffect(() => {
    return () => { if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl) }
  }, [pdfBlobUrl])

  // Group actions by task
  const tasks = actions.filter(a => a.itemType === 'task')
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  const getActionsForTask = (taskId: string) =>
    actions.filter(a => a.itemType === 'action' && a.parentId === taskId)

  return (
    <div className={`${styles.chatPage} ${isResizing ? styles.resizing : ''}`} ref={containerRef}>

      {/* Chat Panel - flexible width */}
      <div className={styles.chatPanel}>
        <div className={styles.messagesContainer} ref={parentRef}>
          {messages.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
                  <rect width="32" height="32" rx="6" fill="var(--color-primary-light)"/>
                  <path d="M8 12h16M8 16h12M8 20h8" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
              <h3>Start a conversation</h3>
              <p>Send a message to begin interacting with CraftBot</p>
            </div>
          ) : (
            <div
              style={{
                height: `${virtualizer.getTotalSize()}px`,
                width: '100%',
                position: 'relative',
              }}
            >
              {loadingOlderMessages && (
                <div style={{ textAlign: 'center', padding: '8px 0', color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)' }}>
                  <Loader2 size={14} style={{ display: 'inline', animation: 'spin 1s linear infinite' }} /> Loading older messages...
                </div>
              )}
              {virtualizer.getVirtualItems().map((virtualItem) => {
                const message = messages[virtualItem.index]
                return (
                  <div
                    key={message.messageId || virtualItem.index}
                    data-index={virtualItem.index}
                    ref={virtualizer.measureElement}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                  >
                    <ChatMessageItem
                      message={message}
                      onOpenFile={openFile}
                      onOpenFolder={openFolder}
                      onReply={handleChatReply}
                      onOptionClick={handleOptionClick}
                    />
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Status bar */}
        <div className={styles.statusBar}>
          <StatusIndicator status={status.state} size="sm" variant="dot" />
          <span>{status.message}</span>
        </div>

        {/* Input area */}
        <div className={styles.inputArea}>
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className={styles.hiddenFileInput}
            onChange={handleFileSelect}
          />

          <IconButton
            icon={<Paperclip size={18} />}
            variant="ghost"
            tooltip="Attach file"
            onClick={handleAttachClick}
          />

          <div className={styles.micGroup} ref={langDropdownRef}>
            <button
              className={`${styles.micCombo} ${isListening ? styles.micComboActive : ''}`}
              onClick={toggleListening}
              title={isListening ? 'Stop listening' : 'Voice input'}
            >
              <span className={styles.micIconWrap}>
                {isListening && <span className={styles.micPulseRing} />}
                {isListening ? <MicOff size={16} /> : <Mic size={16} />}
              </span>
            </button>
            <button
              className={`${styles.langBtn} ${isListening ? styles.langBtnActive : ''}`}
              onClick={() => !isListening && setLangOpen(o => !o)}
              title="Speech language"
              disabled={isListening}
            >
              {MIC_LANGUAGES.find(l => l.code === micLang)?.label ?? 'EN'}
            </button>
            {langOpen && (
              <div className={styles.langDropdown}>
                {MIC_LANGUAGES.map(lang => (
                  <button
                    key={lang.code}
                    className={`${styles.langOption}${micLang === lang.code ? ` ${styles.langOptionActive}` : ''}`}
                    onClick={() => { localStorage.setItem('micLang', lang.code); setMicLang(lang.code); setLangOpen(false) }}
                  >
                    <span className={styles.langCode}>{lang.label}</span>
                    <span className={styles.langFull}>{lang.full}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div
            className={`${styles.inputWrapper}${isDragOver ? ` ${styles.inputWrapperDragOver}` : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {/* Attachment error message */}
            {(attachmentError || !attachmentValidation.valid) && (
              <div className={styles.attachmentError}>
                <AlertCircle size={14} />
                <span>{attachmentError || attachmentValidation.error}</span>
                <button
                  className={styles.dismissError}
                  onClick={() => setAttachmentError(null)}
                  title="Dismiss"
                >
                  <X size={12} />
                </button>
              </div>
            )}

            {/* Reply bar - shows when replying to a message/task */}
            {replyTarget && (
              <div className={styles.replyBar}>
                <Reply size={14} />
                <span className={styles.replyText}>
                  Replying to: <em>{replyTarget.displayName}</em>
                </span>
                <button
                  className={styles.replyCancel}
                  onClick={clearReplyTarget}
                  title="Cancel reply"
                >
                  <X size={14} />
                </button>
              </div>
            )}

            {/* Pending attachments preview */}
            {pendingAttachments.length > 0 && (
              <div className={styles.pendingAttachments}>
                {pendingAttachments.map((att, idx) => (
                  <div key={idx} className={styles.pendingAttachment}>
                    <button
                      className={styles.pendingAttachmentBody}
                      onClick={() => openPreview(att)}
                      title="Click to preview"
                    >
                      {att.type.startsWith('image/') ? (
                        <img
                          src={`data:${att.type};base64,${att.content}`}
                          alt={att.name}
                          className={styles.pendingImageThumb}
                        />
                      ) : (
                        <File size={12} />
                      )}
                      <span className={styles.pendingFileName} title={att.name}>
                        {att.name}
                      </span>
                      <span className={styles.pendingFileSize}>
                        ({formatFileSize(att.size)})
                      </span>
                    </button>
                    <button
                      className={styles.removeAttachment}
                      onClick={() => removeAttachment(idx)}
                      title="Remove"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}



            <textarea
              ref={inputRef}
              className={`${styles.input}${isListening ? ` ${styles.inputListening}` : ''}`}
              placeholder={isListening ? 'Listening... speak now' : 'Type a message...'}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              rows={1}
              lang={micLang}
              inputMode="text"
            />
          </div>

          <Button
            icon={<Send size={16} />}
            onClick={handleSend}
            disabled={(!input.trim() && pendingAttachments.length === 0) || !attachmentValidation.valid}
          />
        </div>
      </div>

      {/* Attachment preview modal — portal so it's always on top */}
      {previewAttachment && ReactDOM.createPortal(
        (() => {
          const isImage = previewAttachment.type.startsWith('image/')
          const isPdf = previewAttachment.type === 'application/pdf' || previewAttachment.name.toLowerCase().endsWith('.pdf')
          const isText = !isPdf && (previewAttachment.type.startsWith('text/') ||
            ['application/json', 'application/xml', 'application/javascript',
             'application/typescript', 'application/yaml', 'application/toml',
             'application/csv', 'application/x-sh'].includes(previewAttachment.type) ||
            /\.(txt|md|csv|json|xml|yaml|yml|toml|sh|py|js|ts|jsx|tsx|css|html|htm|env|log|ini|cfg|conf)$/i.test(previewAttachment.name))

          let textContent = ''
          let lineCount = 0
          if (isText) {
            try {
              const bytes = Uint8Array.from(atob(previewAttachment.content), c => c.charCodeAt(0))
              textContent = new TextDecoder('utf-8').decode(bytes)
              lineCount = textContent.split('\n').length
            } catch { textContent = '' }
          }

          return (
            <div className={styles.previewOverlay} onClick={() => setPreviewAttachment(null)}>
              <div className={styles.previewModal} onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className={styles.previewHeader}>
                  <div className={styles.previewHeaderLeft}>
                    <span className={styles.previewFileName} title={previewAttachment.name}>
                      {previewAttachment.name}
                    </span>
                    <span className={styles.previewMeta}>
                      {formatFileSize(previewAttachment.size)}
                      {isText && lineCount > 0 && <> · {lineCount} line{lineCount !== 1 ? 's' : ''}</>}
                      {isText && <> · Formatting may be inconsistent from source</>}
                    </span>
                  </div>
                  <button className={styles.previewClose} onClick={() => setPreviewAttachment(null)} title="Close (Esc)">
                    <X size={18} />
                  </button>
                </div>

                {/* Body */}
                {isImage ? (
                  <img
                    src={`data:${previewAttachment.type};base64,${previewAttachment.content}`}
                    alt={previewAttachment.name}
                    className={styles.previewImage}
                  />
                ) : isPdf && pdfBlobUrl ? (
                  <iframe
                    src={pdfBlobUrl}
                    className={styles.previewPdf}
                    title={previewAttachment.name}
                  />
                ) : isText && textContent ? (
                  <pre className={styles.previewTextContent}>{textContent}</pre>
                ) : (
                  <div className={styles.previewFileInfo}>
                    <p className={styles.previewUnavailableText}>
                      Preview isn't available for {previewAttachment.name} ({formatFileSize(previewAttachment.size)}).
                    </p>
                  </div>
                )}
              </div>
            </div>
          )
        })(),
        document.body
      )}

      {/* Resize Handle */}
      <div
        className={styles.resizeHandle}
        onMouseDown={handleMouseDown}
      />

      {/* Task/Action Panel - resizable width */}
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
