import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send, Paperclip } from 'lucide-react'
import { useWebSocket } from '../../contexts/WebSocketContext'
import { Button, IconButton, StatusIndicator } from '../../components/ui'
import styles from './ChatPage.module.css'

export function ChatPage() {
  const { messages, actions, status, sendMessage } = useWebSocket()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input.trim())
      setInput('')
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Group actions by task
  const tasks = actions.filter(a => a.itemType === 'task')
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  const getActionsForTask = (taskId: string) =>
    actions.filter(a => a.itemType === 'action' && a.parentId === taskId)

  return (
    <div className={styles.chatPage}>
      {/* Chat Panel - 2/3 width */}
      <div className={styles.chatPanel}>
        <div className={styles.messagesContainer}>
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
            messages.map((msg, idx) => (
              <div
                key={msg.messageId || idx}
                className={`${styles.message} ${styles[msg.style]}`}
              >
                <div className={styles.messageHeader}>
                  <span className={styles.sender}>{msg.sender}</span>
                  <span className={styles.timestamp}>
                    {new Date(msg.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <div className={styles.messageContent}>
                  {msg.content}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Status bar */}
        <div className={styles.statusBar}>
          <StatusIndicator status={status.state} size="sm" />
          <span>{status.message}</span>
        </div>

        {/* Input area */}
        <div className={styles.inputArea}>
          <IconButton
            icon={<Paperclip size={18} />}
            variant="ghost"
            tooltip="Attach file"
          />
          <textarea
            ref={inputRef}
            className={styles.input}
            placeholder="Type a message..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <Button
            icon={<Send size={16} />}
            onClick={handleSend}
            disabled={!input.trim()}
          />
        </div>
      </div>

      {/* Task/Action Panel - 1/3 width */}
      <div className={styles.actionPanel}>
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
                <button
                  className={`${styles.taskItem} ${selectedTaskId === task.id ? styles.selected : ''}`}
                  onClick={() => setSelectedTaskId(
                    selectedTaskId === task.id ? null : task.id
                  )}
                >
                  <StatusIndicator status={task.status} size="sm" />
                  <span className={styles.taskName}>{task.name}</span>
                </button>
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
