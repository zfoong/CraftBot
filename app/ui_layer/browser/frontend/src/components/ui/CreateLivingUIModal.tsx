import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { X, Sparkles, Download, Loader2, Package, FolderInput, Upload, Check } from 'lucide-react'
import { Button } from './Button'
import { useSettingsWebSocket } from '../../pages/Settings/useSettingsWebSocket'
import type { LivingUICreateRequest } from '../../types'
import styles from './CreateLivingUIModal.module.css'

export interface CreateLivingUIModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: LivingUICreateRequest) => void
  onInstalled?: (projectId: string) => void
}

interface CustomField {
  key: string
  label: string
  type: string
  default: string
  placeholder?: string
}

interface MarketplaceApp {
  id: string
  name: string
  description: string
  preview?: string
  folder: string
  tags?: string[]
  version?: string
  customizable?: CustomField[]
}

const MAX_WORDS = 5000

function countWords(text: string): number {
  const trimmed = text.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).length
}

export function CreateLivingUIModal({ isOpen, onClose, onSubmit, onInstalled }: CreateLivingUIModalProps) {
  const [activeTab, setActiveTab] = useState<'marketplace' | 'custom' | 'import'>('marketplace')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({})

  // Import tab state
  const [importSource, setImportSource] = useState('')
  const [importing, setImporting] = useState(false)

  // Marketplace state
  const { send, onMessage, isConnected } = useSettingsWebSocket()

  // Upload ZIP → stage on server → send to agent via WebSocket
  const handleZipUpload = async (file: File) => {
    setImporting(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const zipName = file.name.replace('.zip', '').replace(/^livingui_/, '').replace(/_[a-f0-9]+$/, '')
      formData.append('name', zipName)
      const resp = await fetch('/api/living-ui/import', { method: 'POST', body: formData })
      const result = await resp.json()
      if (result.success && result.path) {
        // File staged — send to agent flow
        send('living_ui_import', { source: result.path, name: result.name || zipName })
        onClose()
      } else {
        alert(result.error || 'Upload failed')
      }
    } catch (err) {
      alert('Upload failed: ' + (err instanceof Error ? err.message : err))
    } finally {
      setImporting(false)
    }
  }
  const [apps, setApps] = useState<MarketplaceApp[]>([])
  const [marketplaceLoading, setMarketplaceLoading] = useState(false)
  const [marketplaceError, setMarketplaceError] = useState<string | null>(null)
  const [installingIds, setInstallingIds] = useState<Set<string>>(new Set())
  const [installCounts, setInstallCounts] = useState<Map<string, number>>(new Map())
  const [configuringApp, setConfiguringApp] = useState<MarketplaceApp | null>(null)
  const installTimeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())
  const [customValues, setCustomValues] = useState<Record<string, string>>({})

  const nameInputRef = useRef<HTMLInputElement>(null)
  const wordCount = useMemo(() => countWords(description), [description])

  const onCloseRef = useRef(onClose)
  const onInstalledRef = useRef(onInstalled)
  useEffect(() => { onCloseRef.current = onClose }, [onClose])
  useEffect(() => { onInstalledRef.current = onInstalled }, [onInstalled])
  useEffect(() => () => { installTimeoutsRef.current.forEach(t => clearTimeout(t)) }, [])
  // Accumulate projectIds from completed installs — navigate only when all installs finish
  const pendingNavigationsRef = useRef<string[]>([])

  // Reset form fields on open — intentionally NOT resetting installingIds/completedIds
  // so ongoing installs remain visible when user closes and reopens the modal
  useEffect(() => {
    if (isOpen) {
      setName('')
      setDescription('')
      setErrors({})
      setConfiguringApp(null)
      setCustomValues({})
      // Fetch marketplace if on that tab
      if (activeTab === 'marketplace' && apps.length === 0) {
        fetchMarketplace()
      }
      if (activeTab === 'custom') {
        setTimeout(() => nameInputRef.current?.focus(), 100)
      }
    }
  }, [isOpen])

  // Fetch marketplace when tab changes
  useEffect(() => {
    if (isOpen && activeTab === 'marketplace' && apps.length === 0 && isConnected) {
      fetchMarketplace()
    }
    if (activeTab === 'custom') {
      setTimeout(() => nameInputRef.current?.focus(), 100)
    }
  }, [activeTab, isConnected])

  // Listen for marketplace responses
  useEffect(() => {
    const cleanups = [
      onMessage('living_ui_marketplace_list', (data: any) => {
        setMarketplaceLoading(false)
        if (data.success) {
          const appsWithThumbnails = (data.apps || []).map((app: any) => ({
            ...app,
            preview: app.preview || (app.folder ? `https://raw.githubusercontent.com/CraftOS-dev/living-ui-marketplace/main/${app.folder}/thumbnail.png` : undefined),
          }))
          setApps(appsWithThumbnails)
          setMarketplaceError(null)
        } else {
          setMarketplaceError(data.error || 'Failed to load marketplace')
        }
      }),
      onMessage('living_ui_marketplace_install', (data: any) => {
        console.log('[CreateLivingUIModal] received living_ui_marketplace_install:', data)
        const finishedId = data.appId as string | undefined
        if (data.status === 'success') {
          // Queue navigation — don't interrupt the user until all installs are done
          const projectId = data.project?.id
          if (projectId) pendingNavigationsRef.current.push(projectId)

          if (finishedId) {
            const t = installTimeoutsRef.current.get(finishedId)
            if (t) { clearTimeout(t); installTimeoutsRef.current.delete(finishedId) }
            setInstallCounts(prev => {
              const next = new Map(prev)
              next.set(finishedId, (next.get(finishedId) || 0) + 1)
              return next
            })
          }

          setInstallingIds(prev => {
            const next = new Set(prev)
            if (finishedId) next.delete(finishedId)
            else next.clear()
            if (next.size === 0) {
              // All done — navigate to the last completed project then close
              const lastProjectId = pendingNavigationsRef.current.at(-1)
              pendingNavigationsRef.current = []
              if (lastProjectId && onInstalledRef.current) {
                onInstalledRef.current(lastProjectId)
              }
              setTimeout(() => onCloseRef.current(), 800)
            }
            return next
          })
        } else {
          if (finishedId) {
            const t = installTimeoutsRef.current.get(finishedId)
            if (t) { clearTimeout(t); installTimeoutsRef.current.delete(finishedId) }
            setInstallingIds(prev => { const n = new Set(prev); n.delete(finishedId); return n })
          } else {
            installTimeoutsRef.current.forEach(t => clearTimeout(t))
            installTimeoutsRef.current.clear()
            setInstallingIds(new Set())
          }
          setMarketplaceError(data.error || 'Installation failed')
        }
      }),
    ]
    return () => cleanups.forEach(c => c())
  }, [onMessage])

  const fetchMarketplace = useCallback(() => {
    setMarketplaceLoading(true)
    setMarketplaceError(null)
    send('living_ui_marketplace_list')
  }, [send])

  const handleAddClick = (app: MarketplaceApp) => {
    if (app.customizable && app.customizable.length > 0) {
      // Show config form
      setConfiguringApp(app)
      const defaults: Record<string, string> = {}
      app.customizable.forEach(f => { defaults[f.key] = f.default })
      setCustomValues(defaults)
    } else {
      // Install directly
      doInstall(app, {})
    }
  }

  const doInstall = (app: MarketplaceApp, fields: Record<string, string>) => {
    const appKey = app.folder || app.id
    setConfiguringApp(null)
    setInstallingIds(prev => new Set([...prev, appKey]))
    setMarketplaceError(null)

    // Stuck-install timeout: clear installing state after 3 minutes
    const timeout = setTimeout(() => {
      setInstallingIds(prev => { const n = new Set(prev); n.delete(appKey); return n })
      setMarketplaceError(`Installation of "${app.name}" timed out. Please try again.`)
      installTimeoutsRef.current.delete(appKey)
    }, 3 * 60 * 1000)
    installTimeoutsRef.current.set(appKey, timeout)

    send('living_ui_marketplace_install', {
      appId: appKey,
      appName: fields.APP_TITLE || app.name,
      appDescription: app.description,
      customFields: fields,
    })
  }

  // Escape key intentionally does NOT close this modal — user must use the X button

  const validate = (): boolean => {
    const newErrors: { name?: string; description?: string } = {}
    if (!name.trim()) newErrors.name = 'Name is required'
    else if (name.length > 50) newErrors.name = 'Name must be 50 characters or less'
    if (!description.trim()) newErrors.description = 'Description is required'
    else if (description.length < 10) newErrors.description = 'Please provide more detail (at least 10 characters)'
    else if (wordCount > MAX_WORDS) newErrors.description = `Description exceeds ${MAX_WORDS} word limit`
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    onSubmit({ name: name.trim(), description: description.trim() })
  }

  // Fully unmount when closed and no installs pending; stay mounted (invisible) while installs run
  if (!isOpen && installingIds.size === 0) return null
  if (!isOpen) return <></> // mounted but invisible — keeps onMessage listeners alive

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent} style={{ maxWidth: '640px' }}>
        <div className={styles.modalHeader}>
          <div className={styles.headerTitle}>
            <Sparkles size={20} className={styles.headerIcon} />
            <h3>Add Living UI</h3>
          </div>
          <button className={styles.modalClose} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-primary)', padding: '0 var(--space-4)' }}>
          {([
            { id: 'marketplace' as const, label: 'Marketplace', icon: <Package size={14} /> },
            { id: 'custom' as const, label: 'Create Custom', icon: <Sparkles size={14} /> },
            { id: 'import' as const, label: 'Import', icon: <FolderInput size={14} /> },
          ]).map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                background: 'none', border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid var(--color-primary)' : '2px solid transparent',
                color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: activeTab === tab.id ? 'var(--font-semibold)' : 'var(--font-normal)',
                fontSize: 'var(--text-sm)', fontFamily: 'inherit',
                display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
              }}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Marketplace Tab */}
        {activeTab === 'marketplace' && !configuringApp && (
          <div className={styles.modalBody} style={{ minHeight: '300px', maxHeight: '60vh', overflowY: 'auto' }}>
            {marketplaceLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
                <Loader2 size={24} style={{ animation: 'spin 1s linear infinite' }} />
              </div>
            ) : marketplaceError ? (
              <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                <p style={{ marginBottom: 'var(--space-3)' }}>{marketplaceError}</p>
                <Button size="sm" variant="secondary" onClick={fetchMarketplace}>Retry</Button>
              </div>
            ) : apps.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-muted)' }}>
                <Package size={32} style={{ marginBottom: 'var(--space-3)', opacity: 0.5 }} />
                <p>No apps available yet.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {apps.map(app => {
                  const appKey = app.folder || app.id
                  return (
                  <div key={app.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-3)',
                    padding: 'var(--space-3)',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-primary)',
                  }}>
                    {app.preview ? (
                      <img src={app.preview} alt={app.name} referrerPolicy="no-referrer"
                        style={{ width: 80, height: 60, borderRadius: 'var(--radius-sm)', objectFit: 'cover', background: 'var(--bg-secondary)' }}
                        onError={(e) => { (e.target as HTMLImageElement).src = ''; (e.target as HTMLImageElement).style.display = 'none' }} />
                    ) : (
                      <div style={{ width: 80, height: 60, borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Package size={24} style={{ color: 'var(--text-muted)' }} />
                      </div>
                    )}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'var(--font-semibold)', fontSize: 'var(--text-sm)', marginBottom: '2px' }}>{app.name}</div>
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', lineHeight: 1.4 }}>{app.description}</div>
                      {app.tags && app.tags.length > 0 && (
                        <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                          {app.tags.map(tag => (
                            <span key={tag} style={{ fontSize: '10px', padding: '1px 6px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)' }}>{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', flexShrink: 0 }}>
                      {(installCounts.get(appKey) || 0) > 0 && !installingIds.has(appKey) && (
                        <span style={{ fontSize: '10px', color: 'var(--color-success, #22c55e)', display: 'flex', alignItems: 'center', gap: '3px', whiteSpace: 'nowrap' }}>
                          <Check size={10} />
                          {(installCounts.get(appKey) || 0) === 1 ? 'Installed' : `Installed ×${installCounts.get(appKey)}`}
                        </span>
                      )}
                      <Button
                        size="sm"
                        variant="primary"
                        icon={installingIds.has(appKey) ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Download size={14} />}
                        onClick={() => !installingIds.has(appKey) && handleAddClick(app)}
                        disabled={installingIds.has(appKey)}
                      >
                        {installingIds.has(appKey) ? 'Installing...' : 'Add'}
                      </Button>
                    </div>
                  </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Marketplace Config Form (shown when app has customizable fields) */}
        {configuringApp && (
          <div className={styles.modalBody}>
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <h4 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-semibold)', marginBottom: 'var(--space-1)' }}>
                Configure: {configuringApp.name}
              </h4>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                Customize before installing
              </p>
            </div>
            {configuringApp.customizable?.map(field => (
              <div key={field.key} style={{ marginBottom: 'var(--space-3)' }}>
                <label style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  {field.label}
                </label>
                <input
                  type={field.type || 'text'}
                  value={customValues[field.key] || ''}
                  onChange={(e) => setCustomValues(prev => ({ ...prev, [field.key]: e.target.value }))}
                  placeholder={field.placeholder || field.default}
                  style={{
                    width: '100%',
                    padding: 'var(--space-2) var(--space-3)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontSize: 'var(--text-sm)',
                    fontFamily: 'inherit',
                  }}
                />
              </div>
            ))}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
              <Button variant="secondary" onClick={() => setConfiguringApp(null)}>Back</Button>
              <Button variant="primary" icon={<Download size={14} />} onClick={() => doInstall(configuringApp, customValues)}>
                Install
              </Button>
            </div>
          </div>
        )}

        {/* Custom Tab */}
        {activeTab === 'custom' && (
          <form onSubmit={handleSubmit}>
            <div className={styles.modalBody}>
              <div className={styles.formGroup}>
                <label htmlFor="living-ui-name" className={styles.label}>
                  Project Name <span className={styles.required}>*</span>
                </label>
                <input
                  ref={nameInputRef}
                  id="living-ui-name"
                  type="text"
                  className={`${styles.input} ${errors.name ? styles.inputError : ''}`}
                  placeholder="e.g., World News Dashboard"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  maxLength={50}
                />
                {errors.name && <span className={styles.errorText}>{errors.name}</span>}
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="living-ui-description" className={styles.label}>
                  What should this UI do? <span className={styles.required}>*</span>
                </label>
                <textarea
                  id="living-ui-description"
                  className={`${styles.textareaLarge} ${errors.description ? styles.inputError : ''}`}
                  placeholder="Describe what you want the Living UI to display and do. Be specific about the data, layout, interactions, styling preferences, and any external APIs or data sources to use..."
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  rows={10}
                />
                <div className={styles.descriptionFooter}>
                  <span className={styles.hint}>
                    The clearer and more detailed your requirements, the more accurate the Living UI will be.
                  </span>
                  <span className={`${styles.wordCount} ${wordCount > MAX_WORDS ? styles.wordCountError : ''}`}>
                    {wordCount.toLocaleString()} / {MAX_WORDS.toLocaleString()} words
                  </span>
                </div>
                {errors.description && <span className={styles.errorText}>{errors.description}</span>}
              </div>
            </div>

            <div className={styles.modalFooter}>
              <Button variant="secondary" type="button" onClick={onClose}>
                Cancel
              </Button>
              <Button variant="primary" type="submit" icon={<Sparkles size={16} />}>
                Create Living UI
              </Button>
            </div>
          </form>
        )}

        {/* Import Tab — URL/path + ZIP upload */}
        {activeTab === 'import' && (
          <div>
            <div className={styles.modalBody}>
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  GitHub URL or Local Path
                </label>
                <input
                  type="text"
                  className={styles.input}
                  placeholder="https://github.com/user/repo or /path/to/local/app"
                  value={importSource}
                  onChange={e => setImportSource(e.target.value)}
                />
                <span className={styles.hint}>
                  Go · Node.js · Python · Rust · Docker · Static sites
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', margin: 'var(--space-3) 0', color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>
                <div style={{ flex: 1, height: 1, background: 'var(--border-primary)' }} />
                <span>or</span>
                <div style={{ flex: 1, height: 1, background: 'var(--border-primary)' }} />
              </div>

              <div
                style={{
                  border: '2px dashed var(--border-primary)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 'var(--space-6) var(--space-4)',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'border-color 0.2s, background 0.2s',
                }}
                onClick={() => {
                  const input = document.createElement('input')
                  input.type = 'file'
                  input.accept = '.zip'
                  input.onchange = (e) => {
                    const file = (e.target as HTMLInputElement).files?.[0]
                    if (file) handleZipUpload(file)
                  }
                  input.click()
                }}
                onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.background = 'var(--bg-tertiary)' }}
                onDragLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-primary)'; e.currentTarget.style.background = '' }}
                onDrop={(e) => {
                  e.preventDefault()
                  e.currentTarget.style.borderColor = 'var(--border-primary)'
                  e.currentTarget.style.background = ''
                  const file = e.dataTransfer.files[0]
                  if (file && file.name.endsWith('.zip')) handleZipUpload(file)
                }}
              >
                {importing ? (
                  <>
                    <Loader2 size={24} style={{ color: 'var(--color-primary)', animation: 'spin 1s linear infinite', marginBottom: 'var(--space-2)' }} />
                    <p style={{ margin: 0, fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>Importing...</p>
                  </>
                ) : (
                  <>
                    <Upload size={24} style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }} />
                    <p style={{ margin: 0, fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)', color: 'var(--text-primary)' }}>
                      Drop a ZIP file here or click to browse
                    </p>
                    <p style={{ margin: 'var(--space-1) 0 0', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                      Import a previously exported Living UI
                    </p>
                  </>
                )}
              </div>
            </div>

            <div className={styles.modalFooter}>
              <Button variant="secondary" type="button" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="primary"
                icon={importing ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <FolderInput size={16} />}
                disabled={!importSource.trim() || importing}
                onClick={async () => {
                  setImporting(true)
                  send('living_ui_import', {
                    source: importSource.trim(),
                    name: importSource.trim().split('/').pop()?.replace('.git', '') || 'External App',
                  })
                  setImporting(false)
                  setImportSource('')
                  onClose()
                }}
              >
                {importing ? 'Importing...' : 'Import App'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
