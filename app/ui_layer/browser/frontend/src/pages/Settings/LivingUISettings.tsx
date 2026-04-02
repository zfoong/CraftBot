import { useState, useEffect } from 'react'
import {
  Play,
  Square,
  Trash2,
  Loader2,
  FolderOpen,
  RefreshCw,
} from 'lucide-react'
import { Button, Badge, ConfirmModal } from '../../components/ui'
import { useConfirmModal } from '../../hooks'
import styles from './SettingsPage.module.css'
import { useSettingsWebSocket } from './useSettingsWebSocket'

interface LivingUIProject {
  id: string
  name: string
  status: string
  port: number | null
  backendPort: number | null
  path: string
  autoLaunch: boolean
  logCleanup: boolean
}

export function LivingUISettings() {
  const { send, onMessage, isConnected } = useSettingsWebSocket()
  const [projects, setProjects] = useState<LivingUIProject[]>([])
  const [loading, setLoading] = useState(true)
  const [actionInProgress, setActionInProgress] = useState<string | null>(null)
  const { modalProps: confirmModalProps, confirm } = useConfirmModal()

  // Load projects on mount (re-runs when WebSocket connects)
  useEffect(() => {
    const cleanup = onMessage('living_ui_settings_get', (data: any) => {
      if (data.success !== undefined) {
        setProjects(data.projects || [])
      }
      setLoading(false)
    })

    if (isConnected) {
      send('living_ui_settings_get')
    }
    return cleanup
  }, [isConnected, send, onMessage])

  // Handle project action responses
  useEffect(() => {
    const cleanup = onMessage('living_ui_project_action', (data: any) => {
      setActionInProgress(null)
      if (data.success) {
        // Refresh project list
        send('living_ui_settings_get')
      }
    })
    return cleanup
  }, [send, onMessage])

  // Handle setting toggle responses
  useEffect(() => {
    const cleanup = onMessage('living_ui_project_setting_update', (data: any) => {
      if (data.success) {
        send('living_ui_settings_get')
      }
    })
    return cleanup
  }, [send, onMessage])

  const handleLaunch = (projectId: string) => {
    setActionInProgress(projectId)
    send('living_ui_project_action', { projectId, action: 'launch' })
  }

  const handleStop = (projectId: string) => {
    setActionInProgress(projectId)
    send('living_ui_project_action', { projectId, action: 'stop' })
  }

  const handleDelete = async (project: LivingUIProject) => {
    const confirmed = await confirm({
      title: 'Delete Living UI',
      message: `Are you sure you want to delete "${project.name}"? This will remove all project files and cannot be undone.`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (confirmed) {
      setActionInProgress(project.id)
      send('living_ui_project_action', { projectId: project.id, action: 'delete' })
    }
  }

  const handleToggleAutoLaunch = (projectId: string, value: boolean) => {
    send('living_ui_project_setting_update', { projectId, setting: 'autoLaunch', value })
  }

  const handleToggleLogCleanup = (projectId: string, value: boolean) => {
    send('living_ui_project_setting_update', { projectId, setting: 'logCleanup', value })
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'running': return 'success'
      case 'stopped': return 'default'
      case 'error': return 'error'
      case 'creating': return 'warning'
      default: return 'default'
    }
  }

  if (loading) {
    return (
      <div className={styles.settingsSection}>
        <div className={styles.sectionHeader}>
          <h3>Living UI</h3>
          <p>Manage your Living UI projects</p>
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-8)' }}>
          <Loader2 size={24} style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      </div>
    )
  }

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Living UI</h3>
        <p>Manage your Living UI projects</p>
      </div>

      {projects.length === 0 ? (
        <div className={styles.formGroup}>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
            No Living UI projects yet. Create one from the main chat.
          </p>
        </div>
      ) : (
        <div className={styles.settingsForm}>
          {projects.map(project => (
            <div key={project.id} className={styles.formGroup} style={{
              padding: 'var(--space-4)',
              background: 'var(--bg-tertiary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-primary)',
            }}>
              {/* Project header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span style={{ fontWeight: 'var(--font-semibold)', fontSize: 'var(--text-sm)' }}>
                    {project.name}
                  </span>
                  <Badge variant={getStatusVariant(project.status)}>
                    {project.status}
                  </Badge>
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                  {project.status === 'running' ? (
                    <Button
                      size="sm"
                      variant="secondary"
                      icon={actionInProgress === project.id ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Square size={14} />}
                      onClick={() => handleStop(project.id)}
                      disabled={actionInProgress === project.id}
                    >
                      Stop
                    </Button>
                  ) : project.status === 'stopped' || project.status === 'error' ? (
                    <Button
                      size="sm"
                      variant="primary"
                      icon={actionInProgress === project.id ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />}
                      onClick={() => handleLaunch(project.id)}
                      disabled={actionInProgress === project.id}
                    >
                      Launch
                    </Button>
                  ) : null}
                  <Button
                    size="sm"
                    variant="ghost"
                    icon={<Trash2 size={14} />}
                    onClick={() => handleDelete(project)}
                    disabled={actionInProgress === project.id}
                  />
                </div>
              </div>

              {/* Project info */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>
                <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
                  {project.port && <span>Frontend: {project.port}</span>}
                  {project.backendPort && <span>Backend: {project.backendPort}</span>}
                  <span>ID: {project.id}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                  <FolderOpen size={12} />
                  <span style={{ wordBreak: 'break-all' }}>{project.path}</span>
                </div>
              </div>

              {/* Project toggles */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                <div className={styles.toggleGroup}>
                  <div className={styles.toggleInfo}>
                    <span className={styles.toggleLabel}>Auto-launch on startup</span>
                    <span className={styles.toggleDesc}>Automatically launch when CraftBot starts</span>
                  </div>
                  <input
                    type="checkbox"
                    className={styles.toggle}
                    checked={project.autoLaunch}
                    onChange={(e) => handleToggleAutoLaunch(project.id, e.target.checked)}
                  />
                </div>
                <div className={styles.toggleGroup}>
                  <div className={styles.toggleInfo}>
                    <span className={styles.toggleLabel}>Clean logs on restart</span>
                    <span className={styles.toggleDesc}>Delete old log files when launching</span>
                  </div>
                  <input
                    type="checkbox"
                    className={styles.toggle}
                    checked={project.logCleanup}
                    onChange={(e) => handleToggleLogCleanup(project.id, e.target.checked)}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmModal {...confirmModalProps} />
    </div>
  )
}
