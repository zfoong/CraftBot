import React, { useState, useRef, useEffect, useLayoutEffect, KeyboardEvent, useCallback, ChangeEvent, useMemo } from 'react'
import { Send, Paperclip, X, Loader2, File, AlertCircle, Reply, Mic, MicOff } from 'lucide-react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { useWebSocket } from '../../contexts/WebSocketContext'
import { Button, IconButton, StatusIndicator } from '../ui'
import { useDerivedAgentStatus } from '../../hooks'
import { ChatMessageItem } from '../../pages/Chat/ChatMessage'
import styles from './Chat.module.css'

// Pending attachment type
interface PendingAttachment {
  name: string
  type: string
  size: number
  content: string  // base64
}

interface ChatProps {
  /** Optional Living UI project ID — auto-included in messages sent from this chat */
  livingUIId?: string
  /** Optional placeholder text for the input */
  placeholder?: string
  /** Optional empty state message */
  emptyMessage?: string
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

// Attachment limits
const MAX_ATTACHMENT_COUNT = 10
const MAX_TOTAL_SIZE_BYTES = 70 * 1024 * 1024  // 70MB

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function Chat({ livingUIId, placeholder, emptyMessage }: ChatProps) {
  const {
    messages,
    actions,
    connected,
    sendMessage,
    openFile,
    openFolder,
    lastSeenMessageId,
    markMessagesAsSeen,
    replyTarget,
    setReplyTarget,
    clearReplyTarget,
    loadOlderMessages,
    hasMoreMessages,
    loadingOlderMessages,
  } = useWebSocket()

  const status = useDerivedAgentStatus({ actions, messages, connected })
  const [input, setInput] = useState('')
  const [pendingAttachments, setPendingAttachments] = useState<PendingAttachment[]>([])
  const [attachmentError, setAttachmentError] = useState<string | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Voice input state
  const [isListening, setIsListening] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null)
  const [micLang, setMicLang] = useState(() => {
    const browserLang = navigator.language || 'en-US'
    return MIC_LANGUAGES.some(l => l.code === browserLang) ? browserLang : 'en-US'
  })
  const [langOpen, setLangOpen] = useState(false)
  const langDropdownRef = useRef<HTMLDivElement>(null)

  // Input history (terminal-style up/down arrow navigation)
  const inputHistoryRef = useRef<string[]>([])
  const historyIndexRef = useRef(-1)
  const parentRef = useRef<HTMLDivElement>(null)
  const wasNearBottomRef = useRef(true)
  const prevMessageCountRef = useRef(0)
  const hasInitialScrolled = useRef(false)

  const attachmentValidation = useMemo(() => {
    const totalSize = pendingAttachments.reduce((sum, att) => sum + att.size, 0)
    const count = pendingAttachments.length
    if (count > MAX_ATTACHMENT_COUNT) {
      return { valid: false, error: `Maximum ${MAX_ATTACHMENT_COUNT} files allowed. You have ${count} files.` }
    }
    if (totalSize > MAX_TOTAL_SIZE_BYTES) {
      return { valid: false, error: `Total size (${formatFileSize(totalSize)}) exceeds 70MB limit.` }
    }
    return { valid: true, error: null }
  }, [pendingAttachments])

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
    overscan: 5,
  })

  const getFirstUnreadIndex = useCallback(() => {
    if (!lastSeenMessageId) return -1
    const lastSeenIdx = messages.findIndex(m => m.messageId === lastSeenMessageId)
    if (lastSeenIdx === -1) return 0
    if (lastSeenIdx === messages.length - 1) return -1
    return lastSeenIdx + 1
  }, [messages, lastSeenMessageId])

  const isNearBottom = useCallback(() => {
    const container = parentRef.current
    if (!container) return true
    return container.scrollHeight - container.scrollTop - container.clientHeight < 100
  }, [])

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

  // Track scroll position + load older messages on scroll-to-top
  useEffect(() => {
    const container = parentRef.current
    if (!container) return
    const handleScroll = () => {
      wasNearBottomRef.current = isNearBottom()
      if (container.scrollTop < 100 && hasMoreMessages && !loadingOlderMessages) {
        loadOlderMessages()
      }
    }
    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [isNearBottom, hasMoreMessages, loadingOlderMessages, loadOlderMessages])

  // Scroll to unread on mount, auto-scroll on new messages if near bottom
  useEffect(() => {
    if (messages.length === 0) return

    const isNewMessage = messages.length > prevMessageCountRef.current
    prevMessageCountRef.current = messages.length

    if (!hasInitialScrolled.current) {
      hasInitialScrolled.current = true
      const firstUnreadIdx = getFirstUnreadIndex()
      setTimeout(() => {
        if (firstUnreadIdx !== -1) {
          virtualizer.scrollToIndex(firstUnreadIdx, { align: 'start', behavior: 'auto' })
        } else {
          virtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'auto' })
        }
        markMessagesAsSeen()
      }, 50)
    } else if (isNewMessage && wasNearBottomRef.current) {
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'smooth' })
      markMessagesAsSeen()
    }
  }, [messages.length, virtualizer, getFirstUnreadIndex, markMessagesAsSeen])

  const adjustTextareaHeight = useCallback(() => {
    const textarea = inputRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [])

  useLayoutEffect(() => {
    adjustTextareaHeight()
  }, [input, adjustTextareaHeight])

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

  const toggleListening = useCallback(() => {
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any
    const SpeechRecognitionAPI = w.SpeechRecognition || w.webkitSpeechRecognition

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
    if (!attachmentValidation.valid) return
    if (input.trim() || pendingAttachments.length > 0) {
      // Save to input history
      if (input.trim()) {
        inputHistoryRef.current.push(input.trim())
      }
      historyIndexRef.current = -1

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
        replyContext,
        livingUIId
      )
      setInput('')
      setPendingAttachments([])
      setAttachmentError(null)
      clearReplyTarget()
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

    const totalFileCount = pendingAttachments.length + files.length
    if (totalFileCount > MAX_ATTACHMENT_COUNT) {
      setAttachmentError(`Maximum ${MAX_ATTACHMENT_COUNT} files allowed.`)
      e.target.value = ''
      return
    }

    const newAttachments: PendingAttachment[] = []
    let newTotalSize = pendingAttachments.reduce((sum, att) => sum + att.size, 0)

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      if (file.size > MAX_TOTAL_SIZE_BYTES) {
        setAttachmentError(`File "${file.name}" (${formatFileSize(file.size)}) exceeds the 70MB limit.`)
        e.target.value = ''
        return
      }
      if (newTotalSize + file.size > MAX_TOTAL_SIZE_BYTES) {
        setAttachmentError(`Adding "${file.name}" would exceed the 70MB total size limit.`)
        e.target.value = ''
        return
      }
      try {
        const content = await readFileAsBase64(file)
        newAttachments.push({ name: file.name, type: file.type || 'application/octet-stream', size: file.size, content })
        newTotalSize += file.size
      } catch {
        setAttachmentError(`Failed to read file "${file.name}".`)
        e.target.value = ''
        return
      }
    }

    setAttachmentError(null)
    setPendingAttachments(prev => [...prev, ...newAttachments])
    e.target.value = ''
  }

  const removeAttachment = (index: number) => {
    setPendingAttachments(prev => prev.filter((_, i) => i !== index))
    setAttachmentError(null)
  }

  const readFileAsBase64 = (file: globalThis.File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result as string
        resolve(result.split(',')[1])
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  }

  return (
    <div className={styles.chat}>
      <div className={styles.messagesContainer} ref={parentRef}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
                <rect width="32" height="32" rx="6" fill="var(--color-primary-light)"/>
                <path d="M8 12h16M8 16h12M8 20h8" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <h3>{emptyMessage || 'Start a conversation'}</h3>
            <p>{livingUIId ? 'Ask the agent about this UI' : 'Send a message to begin interacting with CraftBot'}</p>
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
        <input ref={fileInputRef} type="file" multiple className={styles.hiddenFileInput} onChange={handleFileSelect} />
        <IconButton icon={<Paperclip size={18} />} variant="ghost" tooltip="Attach file" onClick={handleAttachClick} />

        <div className={styles.micGroup} ref={langDropdownRef}>
          <IconButton
            icon={isListening ? <MicOff size={18} /> : <Mic size={18} />}
            variant="ghost"
            active={isListening}
            tooltip={isListening ? 'Stop listening' : 'Voice input'}
            onClick={toggleListening}
            className={isListening ? styles.micListening : undefined}
          />
          <button
            className={styles.langBtn}
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
                  onClick={() => { setMicLang(lang.code); setLangOpen(false) }}
                >
                  <span className={styles.langCode}>{lang.label}</span>
                  <span className={styles.langFull}>{lang.full}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className={styles.inputWrapper}>
          {(attachmentError || !attachmentValidation.valid) && (
            <div className={styles.attachmentError}>
              <AlertCircle size={14} />
              <span>{attachmentError || attachmentValidation.error}</span>
              <button className={styles.dismissError} onClick={() => setAttachmentError(null)} title="Dismiss">
                <X size={12} />
              </button>
            </div>
          )}

          {replyTarget && (
            <div className={styles.replyBar}>
              <Reply size={14} />
              <span className={styles.replyText}>Replying to: <em>{replyTarget.displayName}</em></span>
              <button className={styles.replyCancel} onClick={clearReplyTarget} title="Cancel reply">
                <X size={14} />
              </button>
            </div>
          )}

          {pendingAttachments.length > 0 && (
            <div className={styles.pendingAttachments}>
              {pendingAttachments.map((att, idx) => (
                <div key={idx} className={styles.pendingAttachment}>
                  <File size={12} />
                  <span className={styles.pendingFileName} title={att.name}>{att.name}</span>
                  <span className={styles.pendingFileSize}>({formatFileSize(att.size)})</span>
                  <button className={styles.removeAttachment} onClick={() => removeAttachment(idx)} title="Remove">
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {isListening && (
            <div className={styles.listeningDots}>
              <span /><span /><span />
            </div>
          )}

          <textarea
            ref={inputRef}
            className={`${styles.input}${isListening ? ` ${styles.inputListening}` : ''}`}
            placeholder={isListening ? 'Listening... speak now' : (placeholder || 'Type a message...')}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
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
  )
}
