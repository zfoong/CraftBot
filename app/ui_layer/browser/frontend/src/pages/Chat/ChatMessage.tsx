import React, { memo, useState, useMemo } from 'react'
import { Reply } from 'lucide-react'
import { MarkdownContent, AttachmentDisplay, IconButton } from '../../components/ui'
import type { ChatMessage as ChatMessageType } from '../../types'
import styles from './ChatPage.module.css'

interface ChatMessageProps {
  message: ChatMessageType
  onOpenFile: (path: string) => void
  onOpenFolder: (path: string) => void
  onReply?: (
    sessionId: string | undefined,
    displayName: string,
    fullContent: string
  ) => void
}

// Parse reply context from message content
const REPLY_MARKER = '[REPLYING TO PREVIOUS AGENT MESSAGE]:'

function parseReplyContext(content: string): { userMessage: string; replyContext: string | null } {
  const markerIndex = content.indexOf(REPLY_MARKER)
  if (markerIndex === -1) {
    return { userMessage: content, replyContext: null }
  }
  const userMessage = content.slice(0, markerIndex).trim()
  const replyContext = content.slice(markerIndex + REPLY_MARKER.length).trim()
  return { userMessage, replyContext }
}

export const ChatMessageItem = memo(function ChatMessageItem({
  message,
  onOpenFile,
  onOpenFolder,
  onReply,
}: ChatMessageProps) {
  const [isHovered, setIsHovered] = useState(false)

  // Show reply for ALL agent messages
  const canReply = message.style === 'agent' && onReply

  // Parse reply context for user messages
  const { userMessage, replyContext } = useMemo(() => {
    if (message.style === 'user') {
      return parseReplyContext(message.content)
    }
    return { userMessage: message.content, replyContext: null }
  }, [message.content, message.style])

  const handleReply = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (canReply) {
      // Truncate content for display preview
      const displayName = message.content.length > 50
        ? message.content.slice(0, 50) + '...'
        : message.content
      onReply(message.taskSessionId, displayName, message.content)
    }
  }

  return (
    <div
      className={`${styles.messageWrapper} ${styles[message.style + 'Wrapper']}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Message bubble container - for positioning reply button outside */}
      <div className={styles.messageBubbleContainer}>
        <div className={`${styles.message} ${styles[message.style]}`}>
          <div className={styles.messageHeader}>
            <span className={styles.sender}>{message.sender}</span>
            <span className={styles.timestamp}>
              {new Date(message.timestamp * 1000).toLocaleTimeString()}
            </span>
          </div>
          {/* Reply context callout - shown above user message when replying */}
          {replyContext && (
            <div className={styles.replyContextCallout}>
              <MarkdownContent content={replyContext} />
            </div>
          )}
          <div className={styles.messageContent}>
            <MarkdownContent content={userMessage} />
          </div>
        </div>
        {/* Reply button - positioned outside the bubble at top-right */}
        {canReply && isHovered && (
          <IconButton
            icon={<Reply size={14} />}
            variant="ghost"
            size="sm"
            onClick={handleReply}
            tooltip="Reply to this message"
            className={styles.replyButtonOutside}
          />
        )}
      </div>
      {message.attachments && message.attachments.length > 0 && (
        <div className={styles.messageAttachments}>
          <AttachmentDisplay
            attachments={message.attachments}
            onOpenFile={onOpenFile}
            onOpenFolder={onOpenFolder}
          />
        </div>
      )}
    </div>
  )
}, (prev, next) => prev.message.messageId === next.message.messageId)
