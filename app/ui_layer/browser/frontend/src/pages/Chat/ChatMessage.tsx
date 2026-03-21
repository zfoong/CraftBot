import React, { memo } from 'react'
import { MarkdownContent, AttachmentDisplay } from '../../components/ui'
import type { ChatMessage as ChatMessageType } from '../../types'
import styles from './ChatPage.module.css'

interface ChatMessageProps {
  message: ChatMessageType
  onOpenFile: (path: string) => void
  onOpenFolder: (path: string) => void
}

export const ChatMessageItem = memo(function ChatMessageItem({
  message,
  onOpenFile,
  onOpenFolder
}: ChatMessageProps) {
  return (
    <div className={`${styles.messageWrapper} ${styles[message.style + 'Wrapper']}`}>
      <div className={`${styles.message} ${styles[message.style]}`}>
        <div className={styles.messageHeader}>
          <span className={styles.sender}>{message.sender}</span>
          <span className={styles.timestamp}>
            {new Date(message.timestamp * 1000).toLocaleTimeString()}
          </span>
        </div>
        <div className={styles.messageContent}>
          <MarkdownContent content={message.content} />
        </div>
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
