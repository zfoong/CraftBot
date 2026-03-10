import React, { useState } from 'react'
import { ChevronRight, Clock, CheckCircle, XCircle, Loader } from 'lucide-react'
import { useWebSocket } from '../../contexts/WebSocketContext'
import { StatusIndicator, Badge } from '../../components/ui'
import type { ActionItem } from '../../types'
import styles from './TasksPage.module.css'

export function TasksPage() {
  const { actions } = useWebSocket()
  const [selectedItem, setSelectedItem] = useState<ActionItem | null>(null)

  const tasks = actions.filter(a => a.itemType === 'task')

  const getActionsForTask = (taskId: string) =>
    actions.filter(a => a.itemType === 'action' && a.parentId === taskId)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={14} />
      case 'error':
        return <XCircle size={14} />
      case 'running':
        return <Loader size={14} className={styles.spinning} />
      default:
        return <Clock size={14} />
    }
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return '-'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  return (
    <div className={styles.tasksPage}>
      {/* Task List - Left Side */}
      <div className={styles.taskList}>
        <div className={styles.listHeader}>
          <h3>All Tasks</h3>
          <Badge variant="default">{tasks.length}</Badge>
        </div>

        <div className={styles.listContent}>
          {tasks.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No tasks yet</p>
            </div>
          ) : (
            tasks.map(task => {
              const taskActions = getActionsForTask(task.id)
              const isExpanded = selectedItem?.id === task.id ||
                taskActions.some(a => a.id === selectedItem?.id)

              return (
                <div key={task.id} className={styles.taskGroup}>
                  <button
                    className={`${styles.taskItem} ${selectedItem?.id === task.id ? styles.selected : ''}`}
                    onClick={() => setSelectedItem(task)}
                  >
                    <ChevronRight
                      size={14}
                      className={`${styles.chevron} ${isExpanded ? styles.expanded : ''}`}
                    />
                    <StatusIndicator status={task.status} size="sm" />
                    <span className={styles.itemName}>{task.name}</span>
                    <Badge
                      variant={
                        task.status === 'completed' ? 'success' :
                        task.status === 'error' ? 'error' :
                        task.status === 'running' ? 'primary' : 'default'
                      }
                    >
                      {taskActions.length} actions
                    </Badge>
                  </button>

                  {isExpanded && taskActions.length > 0 && (
                    <div className={styles.actionsList}>
                      {taskActions.map(action => (
                        <button
                          key={action.id}
                          className={`${styles.actionItem} ${selectedItem?.id === action.id ? styles.selected : ''}`}
                          onClick={() => setSelectedItem(action)}
                        >
                          <span className={styles.statusIcon}>
                            {getStatusIcon(action.status)}
                          </span>
                          <span className={styles.itemName}>{action.name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Detail Panel - Right Side */}
      <div className={styles.detailPanel}>
        {selectedItem ? (
          <>
            <div className={styles.detailHeader}>
              <div className={styles.detailTitle}>
                <StatusIndicator status={selectedItem.status} size="md" />
                <h2>{selectedItem.name}</h2>
              </div>
              <Badge
                variant={
                  selectedItem.status === 'completed' ? 'success' :
                  selectedItem.status === 'error' ? 'error' :
                  selectedItem.status === 'running' ? 'primary' : 'default'
                }
              >
                {selectedItem.status}
              </Badge>
            </div>

            <div className={styles.detailContent}>
              <div className={styles.detailSection}>
                <h4>Details</h4>
                <dl className={styles.detailList}>
                  <dt>Type</dt>
                  <dd>{selectedItem.itemType}</dd>
                  <dt>ID</dt>
                  <dd className={styles.mono}>{selectedItem.id}</dd>
                  {selectedItem.parentId && (
                    <>
                      <dt>Parent Task</dt>
                      <dd className={styles.mono}>{selectedItem.parentId}</dd>
                    </>
                  )}
                  <dt>Duration</dt>
                  <dd>{formatDuration(selectedItem.duration)}</dd>
                </dl>
              </div>

              {selectedItem.input && (
                <div className={styles.detailSection}>
                  <h4>Input</h4>
                  <pre className={styles.codeBlock}>{selectedItem.input}</pre>
                </div>
              )}

              {selectedItem.output && (
                <div className={styles.detailSection}>
                  <h4>Output</h4>
                  <pre className={styles.codeBlock}>{selectedItem.output}</pre>
                </div>
              )}

              {selectedItem.error && (
                <div className={styles.detailSection}>
                  <h4>Error</h4>
                  <pre className={`${styles.codeBlock} ${styles.errorBlock}`}>
                    {selectedItem.error}
                  </pre>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className={styles.emptyDetail}>
            <p>Select a task or action to view details</p>
          </div>
        )}
      </div>
    </div>
  )
}
