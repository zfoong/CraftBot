import { useState, useEffect, useRef } from 'react'
import {
  Play,
  Square,
  Trash2,
  Loader2,
  FolderOpen,
  RotateCcw,
  Save,
  Plus,
  Check,
  ChevronRight,
  Download,
  Share2,
  Copy,
  Globe,
  Wifi,
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

interface ParsedRule {
  enabled: boolean
  text: string
  lineIndex: number
}

interface ParsedPref {
  key: string
  value: string
  lineIndex: number
}

interface ParsedSection {
  title: string
  rules: ParsedRule[]
  prefs: ParsedPref[]
}

function parseGlobalConfig(content: string): { sections: ParsedSection[]; rawLines: string[] } {
  const lines = content.split('\n')
  const sections: ParsedSection[] = []
  let currentSection: ParsedSection | null = null

  lines.forEach((line, i) => {
    const sectionMatch = line.match(/^##\s+(.+)/)
    if (sectionMatch) {
      currentSection = { title: sectionMatch[1], rules: [], prefs: [] }
      sections.push(currentSection)
      return
    }
    const ruleMatch = line.match(/^- \[(x| )\]\s+(.+)/)
    if (ruleMatch && currentSection) {
      currentSection.rules.push({ enabled: ruleMatch[1] === 'x', text: ruleMatch[2], lineIndex: i })
      return
    }
    const prefMatch = line.match(/^- \*\*(.+?):\*\*\s*(.*)/)
    if (prefMatch && currentSection) {
      currentSection.prefs.push({ key: prefMatch[1], value: prefMatch[2], lineIndex: i })
    }
  })

  return { sections, rawLines: lines }
}

function rebuildConfig(rawLines: string[], changes: Map<number, string>): string {
  return rawLines.map((line, i) => {
    if (changes.has(i)) {
      const newVal = changes.get(i)!
      if (newVal === 'true' || newVal === 'false') {
        return line.replace(/^- \[(x| )\]/, newVal === 'true' ? '- [x]' : '- [ ]')
      }
      const prefMatch = line.match(/^(- \*\*.+?:\*\*\s*)(.*)/)
      if (prefMatch) return prefMatch[1] + newVal
    }
    return line
  }).join('\n')
}

export function LivingUISettings() {
  const { send, onMessage, isConnected } = useSettingsWebSocket()
  const [projects, setProjects] = useState<LivingUIProject[]>([])
  const [loading, setLoading] = useState(true)
  const [actionInProgress, setActionInProgress] = useState<string | null>(null)
  const { modalProps: confirmModalProps, confirm } = useConfirmModal()

  const [globalConfig, setGlobalConfig] = useState('')
  const [originalConfig, setOriginalConfig] = useState('')
  const [globalLoading, setGlobalLoading] = useState(true)
  const [globalSaving, setGlobalSaving] = useState(false)
  const [globalSaveStatus, setGlobalSaveStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [newRule, setNewRule] = useState('')
  const [expandedSection, setExpandedSection] = useState<string | null>('design')
  const [lineChanges, setLineChanges] = useState<Map<number, string>>(new Map())
  const globalConfigRef = useRef(globalConfig)
  globalConfigRef.current = globalConfig

  const isGlobalDirty = globalConfig !== originalConfig

  // Load projects
  useEffect(() => {
    const cleanup = onMessage('living_ui_settings_get', (data: any) => {
      if (data.success !== undefined) setProjects(data.projects || [])
      setLoading(false)
    })
    if (isConnected) send('living_ui_settings_get')
    return cleanup
  }, [isConnected, send, onMessage])

  // Load global config
  useEffect(() => {
    const cleanups = [
      onMessage('agent_file_read', (data: any) => {
        const d = data as { filename: string; content: string; success: boolean }
        if (d.filename === 'GLOBAL_LIVING_UI.md' && d.success) {
          setGlobalConfig(d.content)
          setOriginalConfig(d.content)
          setGlobalLoading(false)
        }
      }),
      onMessage('agent_file_write', (data: any) => {
        const d = data as { filename: string; success: boolean }
        if (d.filename === 'GLOBAL_LIVING_UI.md') {
          setGlobalSaving(false)
          if (d.success) {
            setOriginalConfig(globalConfigRef.current)
            setGlobalSaveStatus('success')
            setTimeout(() => setGlobalSaveStatus('idle'), 2000)
          } else {
            setGlobalSaveStatus('error')
            setTimeout(() => setGlobalSaveStatus('idle'), 3000)
          }
        }
      }),
      onMessage('agent_file_restore', (data: any) => {
        const d = data as { filename: string; content: string; success: boolean }
        if (d.filename === 'GLOBAL_LIVING_UI.md' && d.success) {
          setGlobalConfig(d.content)
          setOriginalConfig(d.content)
          setLineChanges(new Map())
        }
      }),
    ]
    if (isConnected) send('agent_file_read', { filename: 'GLOBAL_LIVING_UI.md' })
    return () => cleanups.forEach(c => c())
  }, [isConnected, send, onMessage])

  useEffect(() => {
    const cleanup = onMessage('living_ui_project_action', (data: any) => {
      setActionInProgress(null)
      if (data.success) send('living_ui_settings_get')
    })
    return cleanup
  }, [send, onMessage])

  useEffect(() => {
    const cleanup = onMessage('living_ui_project_setting_update', (data: any) => {
      if (data.success) send('living_ui_settings_get')
    })
    return cleanup
  }, [send, onMessage])

  const handleToggleRule = (lineIndex: number, enabled: boolean) => {
    const newChanges = new Map<number, string>(lineChanges)
    newChanges.set(lineIndex, String(enabled))
    setLineChanges(newChanges)
    setGlobalConfig(rebuildConfig(parseGlobalConfig(originalConfig).rawLines, newChanges))
  }

  const handlePrefChange = (lineIndex: number, value: string) => {
    const newChanges = new Map<number, string>(lineChanges)
    newChanges.set(lineIndex, value)
    setLineChanges(newChanges)
    setGlobalConfig(rebuildConfig(parseGlobalConfig(originalConfig).rawLines, newChanges))
  }

  const handleAddRule = () => {
    if (!newRule.trim()) return
    setGlobalConfig(prev => prev.trimEnd() + '\n- [x] ' + newRule.trim() + '\n')
    setNewRule('')
  }

  const handleDeleteRule = (lineIndex: number) => {
    const lines = globalConfig.split('\n')
    lines.splice(lineIndex, 1)
    setGlobalConfig(lines.join('\n'))
  }

  const handleSaveGlobal = () => {
    setGlobalSaving(true)
    send('agent_file_write', { filename: 'GLOBAL_LIVING_UI.md', content: globalConfig })
  }

  const handleRestoreGlobal = () => {
    confirm({
      title: 'Restore Defaults',
      message: 'Reset global Living UI configuration to defaults? Your custom rules and changes will be lost.',
      confirmText: 'Restore',
      variant: 'danger',
    }, () => {
      send('agent_file_restore', { filename: 'GLOBAL_LIVING_UI.md' })
    })
  }

  const handleLaunch = (projectId: string) => {
    setActionInProgress(projectId)
    send('living_ui_project_action', { projectId, action: 'launch' })
  }

  const handleStop = (projectId: string) => {
    setActionInProgress(projectId)
    send('living_ui_project_action', { projectId, action: 'stop' })
  }

  const handleDelete = (project: LivingUIProject) => {
    confirm({
      title: 'Delete Living UI',
      message: `Are you sure you want to delete "${project.name}"? This will remove all project files and cannot be undone.`,
      confirmText: 'Delete',
      variant: 'danger',
    }, () => {
      setActionInProgress(project.id)
      send('living_ui_project_action', { projectId: project.id, action: 'delete' })
    })
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'running': return 'success'
      case 'stopped': return 'default'
      case 'error': return 'error'
      case 'creating': return 'warning'
      case 'launching': return 'warning'
      default: return 'default'
    }
  }

  const { sections } = parseGlobalConfig(globalConfig)
  const toggleSection = (id: string) => setExpandedSection(prev => prev === id ? null : id)

  const sectionHeader = (id: string, label: string) => (
    <div
      onClick={() => toggleSection(id)}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-tertiary)',
        borderRadius: 'var(--radius-md)', cursor: 'pointer', border: '1px solid var(--border-primary)',
      }}
    >
      <span style={{ fontWeight: 'var(--font-semibold)', fontSize: 'var(--text-sm)' }}>{label}</span>
      <ChevronRight size={14} style={{ transform: expandedSection === id ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }} />
    </div>
  )

  const inputStyle = { flex: 1, padding: 'var(--space-1) var(--space-2)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }

  if (loading && globalLoading) {
    return (
      <div className={styles.settingsSection}>
        <div className={styles.sectionHeader}>
          <h3>Living UI</h3>
          <p>Global design, rules, and project management</p>
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
        <p>Global design, rules, and project management</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>

        {/* ── Design ── */}
        {sectionHeader('design', 'Design')}
        {expandedSection === 'design' && (
          <div className={styles.settingsForm}>
            {sections.filter(s => s.prefs.length > 0).map(section =>
              section.prefs.filter(p => {
                const k = p.key.toLowerCase()
                return k.includes('color') || k.includes('font')
              }).map(pref => {
                const val = lineChanges.has(pref.lineIndex) ? lineChanges.get(pref.lineIndex)! : pref.value
                const isColor = pref.key.toLowerCase().includes('color')
                const isFont = pref.key.toLowerCase().includes('font')
                return (
                  <div key={pref.lineIndex} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', padding: 'var(--space-2) var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                    <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)', minWidth: '120px', flexShrink: 0 }}>{pref.key}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flex: 1 }}>
                      {isColor ? (
                        <>
                          <input type="color" value={val.startsWith('#') ? val : '#000000'} onChange={e => handlePrefChange(pref.lineIndex, e.target.value)} style={{ width: 32, height: 32, border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', background: 'transparent', padding: 0 }} />
                          <input type="text" value={val} onChange={e => handlePrefChange(pref.lineIndex, e.target.value)} style={inputStyle} />
                        </>
                      ) : isFont ? (
                        <select value={val} onChange={e => handlePrefChange(pref.lineIndex, e.target.value)} style={{ ...inputStyle, cursor: 'pointer' }}>
                          <option value="System default (Segoe UI, sans-serif)">System Default</option>
                          <option value="Inter, sans-serif">Inter</option>
                          <option value="Roboto, sans-serif">Roboto</option>
                          <option value="Open Sans, sans-serif">Open Sans</option>
                          <option value="Poppins, sans-serif">Poppins</option>
                          <option value="Lato, sans-serif">Lato</option>
                          <option value="Nunito, sans-serif">Nunito</option>
                          <option value="Source Sans Pro, sans-serif">Source Sans Pro</option>
                          <option value="JetBrains Mono, monospace">JetBrains Mono</option>
                          <option value="Fira Code, monospace">Fira Code</option>
                        </select>
                      ) : (
                        <input type="text" value={val} onChange={e => handlePrefChange(pref.lineIndex, e.target.value)} style={inputStyle} />
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        )}

        {/* ── Rules ── */}
        {sectionHeader('rules', 'Rules')}
        {expandedSection === 'rules' && (
          <div className={styles.settingsForm}>
            {sections.filter(s => s.rules.length > 0).map(section => (
              <div key={section.title} style={{ marginBottom: 'var(--space-2)' }}>
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--font-semibold)', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {section.title}
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', marginTop: 'var(--space-2)' }}>
                  {section.rules.map(rule => (
                    <div key={rule.lineIndex} className={styles.toggleGroup} style={{ padding: 'var(--space-2) var(--space-3)' }}>
                      <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)', flex: 1 }}>{rule.text}</span>
                      <input type="checkbox" className={styles.toggle} checked={lineChanges.has(rule.lineIndex) ? lineChanges.get(rule.lineIndex) === 'true' : rule.enabled} onChange={e => handleToggleRule(rule.lineIndex, e.target.checked)} />
                      {section.title === 'Custom Rules' && (
                        <button onClick={() => handleDeleteRule(rule.lineIndex)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '2px', marginLeft: 'var(--space-1)', display: 'flex', alignItems: 'center' }} title="Delete rule">
                          <Trash2 size={12} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
              <input type="text" value={newRule} onChange={e => setNewRule(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleAddRule()} placeholder="Add a custom rule..." style={{ ...inputStyle, padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-md)' }} />
              <Button size="sm" variant="secondary" icon={<Plus size={14} />} onClick={handleAddRule} disabled={!newRule.trim()}>Add</Button>
            </div>
          </div>
        )}

        {/* Save / Restore */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)' }}>
          <Button size="sm" variant="ghost" icon={<RotateCcw size={14} />} onClick={handleRestoreGlobal}>Restore Defaults</Button>
          <Button size="sm" variant="primary" icon={globalSaving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : globalSaveStatus === 'success' ? <Check size={14} /> : <Save size={14} />} onClick={handleSaveGlobal} disabled={!isGlobalDirty || globalSaving}>
            {globalSaveStatus === 'success' ? 'Saved' : 'Save'}
          </Button>
        </div>

        {/* ── Projects ── */}
        {sectionHeader('projects', 'Projects')}
        {expandedSection === 'projects' && (
          <div className={styles.settingsForm}>
            {projects.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', padding: 'var(--space-2)' }}>
                No Living UI projects yet. Create one from the main chat.
              </p>
            ) : (
              projects.map(project => (
                <div key={project.id} className={styles.formGroup} style={{ padding: 'var(--space-4)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-primary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <span style={{ fontWeight: 'var(--font-semibold)', fontSize: 'var(--text-sm)' }}>{project.name}</span>
                      <Badge variant={getStatusVariant(project.status)}>{project.status}</Badge>
                    </div>
                    <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                      {project.status === 'running' ? (
                        <Button size="sm" variant="secondary" icon={actionInProgress === project.id ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Square size={14} />} onClick={() => handleStop(project.id)} disabled={actionInProgress === project.id}>Stop</Button>
                      ) : (project.status === 'stopped' || project.status === 'error') ? (
                        <Button size="sm" variant="primary" icon={actionInProgress === project.id ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />} onClick={() => handleLaunch(project.id)} disabled={actionInProgress === project.id}>Launch</Button>
                      ) : null}
                      <Button size="sm" variant="ghost" icon={<Download size={14} />} onClick={() => {
                        const link = document.createElement('a')
                        link.href = `/api/living-ui/${project.id}/export`
                        link.download = ''
                        document.body.appendChild(link)
                        link.click()
                        document.body.removeChild(link)
                      }}>Export</Button>
                      <Button size="sm" variant="ghost" icon={<Trash2 size={14} />} onClick={() => handleDelete(project)} disabled={actionInProgress === project.id} />
                    </div>
                  </div>
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
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                    <div className={styles.toggleGroup}>
                      <div className={styles.toggleInfo}>
                        <span className={styles.toggleLabel}>Auto-launch on startup</span>
                        <span className={styles.toggleDesc}>Automatically launch when CraftBot starts</span>
                      </div>
                      <input type="checkbox" className={styles.toggle} checked={project.autoLaunch} onChange={e => send('living_ui_project_setting_update', { projectId: project.id, setting: 'autoLaunch', value: e.target.checked })} />
                    </div>
                    <div className={styles.toggleGroup}>
                      <div className={styles.toggleInfo}>
                        <span className={styles.toggleLabel}>Clean logs on restart</span>
                        <span className={styles.toggleDesc}>Delete old log files when launching</span>
                      </div>
                      <input type="checkbox" className={styles.toggle} checked={project.logCleanup} onChange={e => send('living_ui_project_setting_update', { projectId: project.id, setting: 'logCleanup', value: e.target.checked })} />
                    </div>
                  </div>

                  {/* Sharing Section */}
                  {project.status === 'running' && (
                    <ShareSection projectId={project.id} port={project.port} send={send} onMessage={onMessage} />
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <ConfirmModal {...confirmModalProps} />
    </div>
  )
}


// ── Share Section (per-project) ──────────────────────────────────

function ShareSection({ projectId, port, send, onMessage }: {
  projectId: string
  port: number | null
  send: (type: string, data: any) => void
  onMessage: (type: string, handler: (data: any) => void) => () => void
}) {
  const [lanUrl, setLanUrl] = useState<string | null>(null)
  const [tunnelUrl, setTunnelUrl] = useState<string | null>(null)
  const [tunnelLoading, setTunnelLoading] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)

  // Fetch sharing info on mount
  useEffect(() => {
    send('living_ui_sharing_info', { projectId })

    const unsub1 = onMessage('living_ui_sharing_info', (data: any) => {
      if (data.projectId === projectId) {
        setLanUrl(data.lanUrl)
        setTunnelUrl(data.tunnelUrl)
      }
    })
    const unsub2 = onMessage('living_ui_tunnel_status', (data: any) => {
      if (data.projectId === projectId) {
        setTunnelUrl(data.tunnelUrl)
        setTunnelLoading(false)
      }
    })
    return () => { unsub1(); unsub2() }
  }, [projectId, send, onMessage])

  const handleCopy = (url: string, label: string) => {
    navigator.clipboard.writeText(url)
    setCopied(label)
    setTimeout(() => setCopied(null), 2000)
  }

  const handleStartTunnel = (provider: string) => {
    console.log('[ShareSection] Starting tunnel:', projectId, provider)
    setTunnelLoading(true)
    send('living_ui_tunnel_start', { projectId, provider })
  }

  const handleStopTunnel = () => {
    send('living_ui_tunnel_stop', { projectId })
    setTunnelUrl(null)
  }

  return (
    <div style={{ marginTop: 'var(--space-3)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--border-primary)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
        <Share2 size={14} style={{ color: 'var(--text-muted)' }} />
        <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-semibold)', color: 'var(--text-primary)' }}>Share</span>
      </div>

      {/* LAN URL */}
      {lanUrl && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
          <Wifi size={12} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', flexShrink: 0 }}>LAN:</span>
          <code style={{ fontSize: 'var(--text-xs)', color: 'var(--color-primary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{lanUrl}</code>
          <Button size="sm" variant="ghost" onClick={() => handleCopy(lanUrl, 'lan')} style={{ padding: '2px 6px' }}>
            {copied === 'lan' ? <Check size={12} /> : <Copy size={12} />}
          </Button>
        </div>
      )}

      {/* Tunnel URL */}
      {tunnelUrl ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
          <Globe size={12} style={{ color: 'var(--color-success)', flexShrink: 0 }} />
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', flexShrink: 0 }}>Public:</span>
          <code style={{ fontSize: 'var(--text-xs)', color: 'var(--color-primary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{tunnelUrl}</code>
          <Button size="sm" variant="ghost" onClick={() => handleCopy(tunnelUrl, 'tunnel')} style={{ padding: '2px 6px' }}>
            {copied === 'tunnel' ? <Check size={12} /> : <Copy size={12} />}
          </Button>
          <Button size="sm" variant="ghost" onClick={handleStopTunnel} style={{ padding: '2px 6px', color: 'var(--color-error)' }}>
            <Square size={12} />
          </Button>
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Globe size={12} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Public:</span>
          <button
            onClick={() => handleStartTunnel('cloudflared')}
            disabled={tunnelLoading}
            style={{
              fontSize: 'var(--text-xs)', padding: '4px 12px',
              background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-md)', cursor: 'pointer', color: 'var(--text-primary)',
              fontFamily: 'inherit',
            }}
          >
            {tunnelLoading ? 'Starting...' : 'Create Tunnel'}
          </button>
        </div>
      )}
    </div>
  )
}
