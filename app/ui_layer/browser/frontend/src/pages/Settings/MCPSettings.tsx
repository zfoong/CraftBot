import { useState, useEffect } from 'react'
import {
  RotateCcw,
  X,
  Loader2,
  Plus,
  Edit2,
  Trash2,
} from 'lucide-react'
import { Button, Badge, ConfirmModal } from '../../components/ui'
import { useToast } from '../../contexts/ToastContext'
import { useConfirmModal } from '../../hooks'
import styles from './SettingsPage.module.css'
import { useSettingsWebSocket } from './useSettingsWebSocket'

// MCP Server config type
interface MCPServerConfig {
  name: string
  description: string
  enabled: boolean
  transport: string
  command?: string
  action_set: string
  env: Record<string, string>
}

// MCP item type for display
interface MCPItem {
  name: string
  description: string
  enabled: boolean
  transport?: string
  action_set?: string
  env?: Record<string, string>
  needsConfig?: boolean  // has empty env vars
}

export function MCPSettings() {
  const { send, onMessage, isConnected } = useSettingsWebSocket()
  const { showToast } = useToast()

  // State
  const [servers, setServers] = useState<MCPServerConfig[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Search and reload
  const [searchQuery, setSearchQuery] = useState('')
  const [isReloading, setIsReloading] = useState(false)

  // Add custom server modal state
  const [showAddModal, setShowAddModal] = useState(false)
  const [customJsonConfig, setCustomJsonConfig] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const [addError, setAddError] = useState('')

  // Configure env state
  const [configServer, setConfigServer] = useState<MCPServerConfig | null>(null)
  const [envValues, setEnvValues] = useState<Record<string, string>>({})
  const [isSavingEnv, setIsSavingEnv] = useState(false)

  // Confirm modal
  const { modalProps: confirmModalProps, confirm } = useConfirmModal()

  // Load data when connected
  useEffect(() => {
    if (!isConnected) return

    const cleanups = [
      onMessage('mcp_list', (data: unknown) => {
        const d = data as { success: boolean; servers?: MCPServerConfig[]; error?: string }
        setIsLoading(false)
        if (d.success && d.servers) {
          setServers(d.servers)
        } else if (d.error) {
          showToast('error', d.error)
        }
      }),
      onMessage('mcp_enable', (data: unknown) => {
        const d = data as { success: boolean; message?: string; error?: string }
        if (!d.success) {
          showToast('error', d.error || 'Failed to enable server')
        }
      }),
      onMessage('mcp_disable', (data: unknown) => {
        const d = data as { success: boolean; message?: string; error?: string }
        if (!d.success) {
          showToast('error', d.error || 'Failed to disable server')
        }
      }),
      onMessage('mcp_remove', (data: unknown) => {
        const d = data as { success: boolean; message?: string; error?: string }
        if (d.success) {
          showToast('success', d.message || 'Server removed')
          // Refresh list
          send('mcp_list')
        } else {
          showToast('error', d.error || 'Failed to remove server')
        }
      }),
      onMessage('mcp_add_json', (data: unknown) => {
        const d = data as { success: boolean; message?: string; error?: string }
        setIsAdding(false)
        if (d.success) {
          showToast('success', d.message || 'Server added')
          setShowAddModal(false)
          setCustomJsonConfig('')
          setAddError('')
          // Refresh list
          send('mcp_list')
        } else {
          setAddError(d.error || 'Failed to add server')
        }
      }),
      onMessage('mcp_get_env', (data: unknown) => {
        const d = data as { success: boolean; name: string; env?: Record<string, string> }
        if (d.success && d.env) {
          setEnvValues(d.env)
        }
      }),
      onMessage('mcp_update_env', (data: unknown) => {
        const d = data as { success: boolean; message?: string; error?: string }
        setIsSavingEnv(false)
        if (d.success) {
          showToast('success', d.message || 'Configuration saved')
          setConfigServer(null)
          // Refresh list
          send('mcp_list')
        } else {
          showToast('error', d.error || 'Failed to update configuration')
        }
      }),
    ]

    // Load initial data
    send('mcp_list')

    return () => cleanups.forEach(c => c())
  }, [isConnected, send, onMessage])

  // Build MCP list from configured servers, filter and sort
  const mcpList: MCPItem[] = servers
    .filter(s => {
      if (!searchQuery) return true
      return s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.description && s.description.toLowerCase().includes(searchQuery.toLowerCase()))
    })
    .map(s => ({
      name: s.name,
      description: s.description,
      enabled: s.enabled,
      transport: s.transport,
      action_set: s.action_set,
      env: s.env,
      needsConfig: s.env && Object.keys(s.env).length > 0 && Object.values(s.env).some(v => !v || v.trim() === '')
    }))
    .sort((a, b) => a.name.localeCompare(b.name))

  // Stats
  const totalServers = servers.length
  const enabledServers = servers.filter(s => s.enabled).length

  // Handlers
  const handleReloadServers = () => {
    setIsReloading(true)
    send('mcp_list')
    // Reset after a short delay since mcp_list doesn't have a specific "reload" response
    setTimeout(() => {
      setIsReloading(false)
      showToast('success', 'MCP servers reloaded')
    }, 500)
  }

  const handleToggleServer = (name: string, enabled: boolean) => {
    if (enabled) {
      send('mcp_enable', { name })
    } else {
      send('mcp_disable', { name })
    }
    // Optimistic update
    setServers(prev => prev.map(s => s.name === name ? { ...s, enabled } : s))
  }

  const handleRemoveServer = (name: string) => {
    confirm({
      title: 'Remove Server',
      message: `Remove "${name}" from configured servers?`,
      confirmText: 'Remove',
      variant: 'danger',
    }, () => {
      send('mcp_remove', { name })
      // Optimistic update
      setServers(prev => prev.filter(s => s.name !== name))
    })
  }

  const handleConfigureServer = (server: MCPServerConfig) => {
    setConfigServer(server)
    setEnvValues({ ...server.env })
    send('mcp_get_env', { name: server.name })
  }

  const handleSaveEnv = () => {
    if (!configServer) return
    setIsSavingEnv(true)

    // Update each env var
    const envEntries = Object.entries(envValues)
    if (envEntries.length === 0) {
      setIsSavingEnv(false)
      setConfigServer(null)
      return
    }

    envEntries.forEach(([key, value]) => {
      send('mcp_update_env', { name: configServer.name, key, value })
    })
  }

  const handleAddCustomServer = () => {
    setAddError('')
    try {
      const config = JSON.parse(customJsonConfig)
      if (!config.name) {
        setAddError('Configuration must include a "name" field')
        return
      }
      setIsAdding(true)
      send('mcp_add_json', { name: config.name, config: customJsonConfig })
    } catch {
      setAddError('Invalid JSON format')
    }
  }

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTitleRow}>
          <h3>MCP Servers</h3>
          <Badge variant={enabledServers > 0 ? 'success' : 'default'}>
            {enabledServers}/{totalServers}
          </Badge>
        </div>
        <p>Manage Model Context Protocol server connections</p>
      </div>

      {/* Toolbar */}
      <div className={styles.mcpToolbar}>
        <div className={styles.mcpSearch}>
          <input
            type="text"
            placeholder="Search servers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleReloadServers}
          disabled={isReloading}
          icon={isReloading ? <Loader2 size={14} className={styles.spinning} /> : <RotateCcw size={14} />}
        >
          Reload
        </Button>
      </div>

      {isLoading ? (
        <div className={styles.loadingState}>
          <Loader2 size={20} className={styles.spinning} />
          <span>Loading MCP servers...</span>
        </div>
      ) : mcpList.length === 0 ? (
        <div className={styles.emptyState}>
          {searchQuery ? (
            <p>No servers match your search.</p>
          ) : (
            <p>No MCP servers configured. Add a custom server to get started.</p>
          )}
        </div>
      ) : (
        <div className={styles.mcpList}>
          {mcpList.map(item => (
            <div
              key={item.name}
              className={`${styles.mcpItem} ${!item.enabled ? styles.mcpItemDisabled : ''}`}
            >
              <div className={styles.mcpItemMain}>
                <div className={styles.mcpItemHeader}>
                  <span className={styles.mcpItemName}>{item.name}</span>
                  <Badge variant={item.enabled ? 'success' : 'default'}>
                    {item.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                  {item.needsConfig && (
                    <Badge variant="warning">Needs Config</Badge>
                  )}
                </div>
                <p className={styles.mcpItemDesc}>{item.description}</p>
              </div>
              <div className={styles.mcpItemActions}>
                {item.env && Object.keys(item.env).length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      const server = servers.find(s => s.name === item.name)
                      if (server) handleConfigureServer(server)
                    }}
                    icon={<Edit2 size={14} />}
                    title="Configure"
                  />
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveServer(item.name)}
                  icon={<Trash2 size={14} />}
                  title="Remove"
                />
                <input
                  type="checkbox"
                  className={styles.toggle}
                  checked={item.enabled}
                  onChange={(e) => handleToggleServer(item.name, e.target.checked)}
                  title={item.enabled ? 'Disable' : 'Enable'}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Server Section */}
      <div className={styles.mcpAddSection}>
        <Button
          variant="secondary"
          onClick={() => setShowAddModal(true)}
          icon={<Plus size={14} />}
        >
          Add Server
        </Button>
        <span className={styles.hint}>Add a new MCP server with JSON configuration</span>
      </div>

      {/* Add Custom Server Modal */}
      {showAddModal && (
        <div className={styles.modalOverlay} onClick={() => { setShowAddModal(false); setAddError('') }}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>Add Custom MCP Server</h3>
              <button className={styles.modalClose} onClick={() => { setShowAddModal(false); setAddError('') }}>
                <X size={18} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <p className={styles.hint}>
                Enter the MCP server configuration in JSON format. This will be added to mcp_config.json.
              </p>
              <div className={styles.formGroup}>
                <label>Server Configuration (JSON)</label>
                <textarea
                  value={customJsonConfig}
                  onChange={(e) => setCustomJsonConfig(e.target.value)}
                  placeholder={`{
  "name": "my-server",
  "description": "My custom MCP server",
  "transport": "stdio",
  "command": "npx @my-org/my-mcp-server",
  "action_set": "default",
  "env": {}
}`}
                  rows={10}
                  style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}
                />
              </div>
              {addError && (
                <div className={styles.errorText}>{addError}</div>
              )}
            </div>
            <div className={styles.modalFooter}>
              <Button variant="secondary" onClick={() => { setShowAddModal(false); setAddError('') }}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleAddCustomServer}
                disabled={isAdding || !customJsonConfig.trim()}
              >
                {isAdding ? 'Adding...' : 'Add Server'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Environment Configuration Modal */}
      {configServer && (
        <div className={styles.modalOverlay} onClick={() => setConfigServer(null)}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>Configure {configServer.name}</h3>
              <button className={styles.modalClose} onClick={() => setConfigServer(null)}>
                <X size={18} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <p className={styles.hint}>
                Set the required environment variables for this MCP server.
              </p>
              {Object.keys(configServer.env).length === 0 ? (
                <p>No environment variables to configure.</p>
              ) : (
                Object.entries(configServer.env).map(([key]) => (
                  <div key={key} className={styles.formGroup}>
                    <label>{key}</label>
                    <input
                      type={key.toLowerCase().includes('key') || key.toLowerCase().includes('token') || key.toLowerCase().includes('secret') ? 'password' : 'text'}
                      value={envValues[key] || ''}
                      onChange={(e) => setEnvValues(prev => ({ ...prev, [key]: e.target.value }))}
                      placeholder={`Enter ${key}...`}
                    />
                  </div>
                ))
              )}
            </div>
            <div className={styles.modalFooter}>
              <Button variant="secondary" onClick={() => setConfigServer(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSaveEnv}
                disabled={isSavingEnv}
              >
                {isSavingEnv ? 'Saving...' : 'Save'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal {...confirmModalProps} />
    </div>
  )
}
