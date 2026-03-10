import React from 'react'
import styles from './StatusIndicator.module.css'
import type { ActionStatus, AgentState } from '../../types'

interface StatusIndicatorProps {
  status: ActionStatus | AgentState
  size?: 'sm' | 'md' | 'lg'
  pulse?: boolean
  className?: string
}

export function StatusIndicator({
  status,
  size = 'md',
  pulse = false,
  className = '',
}: StatusIndicatorProps) {
  const shouldPulse = pulse || status === 'running' || status === 'thinking' || status === 'working'

  const classes = [
    styles.indicator,
    styles[size],
    styles[status],
    shouldPulse ? styles.pulse : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return <span className={classes} />
}
