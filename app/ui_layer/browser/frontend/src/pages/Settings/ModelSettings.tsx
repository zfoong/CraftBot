import { useState, useEffect, useRef } from 'react'
import {
  Check,
  X,
  Loader2,
} from 'lucide-react'
import { Button, Badge } from '../../components/ui'
import { useToast } from '../../contexts/ToastContext'
import styles from './SettingsPage.module.css'
import { useSettingsWebSocket } from './useSettingsWebSocket'

// Types
interface ProviderInfo {
  id: string
  name: string
  requires_api_key: boolean
  api_key_env?: string
  base_url_env?: string
  llm_model: string | null
  vlm_model: string | null
  has_vlm: boolean
}

interface ApiKeyStatus {
  has_key: boolean
  masked_key: string
}

interface TestResult {
  success: boolean
  message: string
  error?: string
}

interface SuggestedModel {
  name: string
  label: string
  size: string
  recommended: boolean
}

export function ModelSettings() {
  const { send, onMessage, isConnected } = useSettingsWebSocket()
  const { showToast } = useToast()

  // Provider list state
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const hasInitialized = useRef(false)

  // Current settings state
  const [provider, setProvider] = useState('anthropic')
  const [apiKeys, setApiKeys] = useState<Record<string, ApiKeyStatus>>({})
  const [baseUrls, setBaseUrls] = useState<Record<string, string>>({})
  const [currentLlmModel, setCurrentLlmModel] = useState('')
  const [currentVlmModel, setCurrentVlmModel] = useState('')

  // Form state
  const [newApiKey, setNewApiKey] = useState('')
  const [newBaseUrl, setNewBaseUrl] = useState('')
  const [newLlmModel, setNewLlmModel] = useState('')
  const [newVlmModel, setNewVlmModel] = useState('')

  // Slow mode state
  const [slowModeEnabled, setSlowModeEnabled] = useState(false)
  const [isLoadingSlowMode, setIsLoadingSlowMode] = useState(true)

  // UI state
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [testBeforeSave, setTestBeforeSave] = useState(false)

  // Ollama model list state
  const [ollamaModels, setOllamaModels] = useState<string[]>([])
  const [ollamaModelsLoading, setOllamaModelsLoading] = useState(false)

  // Ollama model download state
  const [pullPhase, setPullPhase] = useState<'idle' | 'selecting' | 'pulling'>('idle')
  const [suggestedModels, setSuggestedModels] = useState<SuggestedModel[]>([])
  const [selectedPullModel, setSelectedPullModel] = useState('')
  const [modelSearch, setModelSearch] = useState('')
  const [pullBytes, setPullBytes] = useState<{ completed: number; total: number; percent: number } | null>(null)
  const [pullStatus, setPullStatus] = useState('')

  const fmtBytes = (n: number) => {
    if (n >= 1_073_741_824) return `${(n / 1_073_741_824).toFixed(1)} GB`
    if (n >= 1_048_576) return `${(n / 1_048_576).toFixed(0)} MB`
    return `${(n / 1024).toFixed(0)} KB`
  }

  // Set up message handlers
  useEffect(() => {
    if (!isConnected) return

    const cleanups = [
      onMessage('model_providers_get', (data: unknown) => {
        const d = data as { success: boolean; providers: ProviderInfo[] }
        if (d.success && d.providers) {
          setProviders(d.providers)
        }
        setIsLoading(false)
      }),
      onMessage('model_settings_get', (data: unknown) => {
        const d = data as {
          success: boolean
          llm_provider: string
          llm_model: string | null
          vlm_model: string | null
          api_keys: Record<string, ApiKeyStatus>
          base_urls: Record<string, string>
        }
        if (d.success && !hasInitialized.current) {
          setProvider(d.llm_provider || 'anthropic')
          setApiKeys(d.api_keys || {})
          setBaseUrls(d.base_urls || {})

          const currentProv = providers.find(p => p.id === (d.llm_provider || 'anthropic'))
          setCurrentLlmModel(d.llm_model || currentProv?.llm_model || '')
          setCurrentVlmModel(d.vlm_model || currentProv?.vlm_model || '')
          setNewLlmModel('')
          setNewVlmModel('')
          hasInitialized.current = true
        }
      }),
      onMessage('model_settings_update', (data: unknown) => {
        const d = data as {
          success: boolean
          llm_provider?: string
          llm_model?: string | null
          vlm_model?: string | null
          api_keys?: Record<string, ApiKeyStatus>
          base_urls?: Record<string, string>
          error?: string
        }
        setIsSaving(false)
        if (d.success) {
          if (d.llm_provider) setProvider(d.llm_provider)
          if (d.api_keys) setApiKeys(d.api_keys)
          if (d.base_urls) setBaseUrls(d.base_urls)
          if (d.llm_model !== undefined) setCurrentLlmModel(d.llm_model || '')
          if (d.vlm_model !== undefined) setCurrentVlmModel(d.vlm_model || '')
          setNewApiKey('')
          setNewBaseUrl('')
          setNewLlmModel('')
          setNewVlmModel('')
          setHasChanges(false)
          showToast('success', 'Settings saved')
        } else {
          showToast('error', d.error || 'Failed to save')
        }
      }),
      onMessage('model_connection_test', (data: unknown) => {
        const d = data as { success: boolean; message: string; error?: string }
        setIsTesting(false)
        setTestResult({
          success: d.success,
          message: d.message,
          error: d.error,
        })

        if (testBeforeSave && d.success) {
          setTestBeforeSave(false)
          setIsSaving(true)
          send('model_settings_update', {
            llmProvider: provider,
            vlmProvider: provider,
            llmModel: newLlmModel || currentLlmModel || undefined,
            vlmModel: newVlmModel || currentVlmModel || undefined,
            apiKey: newApiKey || undefined,
            providerForKey: newApiKey ? provider : undefined,
            baseUrl: newBaseUrl || undefined,
            providerForUrl: newBaseUrl ? provider : undefined,
          })
        } else if (testBeforeSave && !d.success) {
          setTestBeforeSave(false)
        }
      }),
      onMessage('ollama_models_get', (data: unknown) => {
        const d = data as { success: boolean; models: string[]; error?: string }
        setOllamaModelsLoading(false)
        if (d.success && d.models && d.models.length > 0) {
          setOllamaModels(d.models)
        } else {
          setOllamaModels([])
        }
      }),
      onMessage('local_llm_suggested_models', (data: unknown) => {
        const d = data as { models: SuggestedModel[] }
        setSuggestedModels(d.models || [])
        const rec = d.models?.find(m => m.recommended)
        if (rec) setSelectedPullModel(rec.name)
      }),
      onMessage('local_llm_pull_progress', (data: unknown) => {
        const d = data as { message: string; total: number; completed: number; percent: number }
        setPullStatus(d.message || '')
        if (d.total > 0) setPullBytes({ completed: d.completed, total: d.total, percent: d.percent })
      }),
      onMessage('local_llm_pull_model', (data: unknown) => {
        const d = data as { success: boolean; model?: string; error?: string }
        if (d.success) {
          setPullPhase('idle')
          setPullBytes(null)
          setPullStatus('')
          setOllamaModelsLoading(true)
          send('ollama_models_get', { baseUrl: baseUrls['remote'] || undefined })
          showToast('success', `Model ${d.model} downloaded successfully`)
        } else {
          setPullPhase('idle')
          showToast('error', d.error || 'Model download failed')
        }
      }),
      onMessage('slow_mode_get', (data: unknown) => {
        const d = data as { success: boolean; enabled: boolean; tpm_limit: number }
        setIsLoadingSlowMode(false)
        if (d.success) {
          setSlowModeEnabled(d.enabled)
        }
      }),
      onMessage('slow_mode_set', (data: unknown) => {
        const d = data as { success: boolean; enabled: boolean; error?: string }
        if (d.success) {
          setSlowModeEnabled(d.enabled)
          showToast('success', `Slow mode ${d.enabled ? 'enabled' : 'disabled'}`)
        } else {
          showToast('error', d.error || 'Failed to update slow mode')
        }
      }),
    ]

    return () => cleanups.forEach(cleanup => cleanup())
  }, [isConnected, onMessage, send, testBeforeSave, provider, newApiKey, newBaseUrl, baseUrls])

  // Load initial data only once when connected
  useEffect(() => {
    if (!isConnected || hasInitialized.current) return

    send('model_providers_get')
    send('model_settings_get')
    send('slow_mode_get')
  }, [isConnected, send])

  // Fetch Ollama models whenever the active provider is 'remote'
  useEffect(() => {
    if (!isConnected || provider !== 'remote') return
    setOllamaModelsLoading(true)
    send('ollama_models_get', { baseUrl: baseUrls['remote'] || undefined })
  }, [provider, isConnected])

  const currentProvider = providers.find(p => p.id === provider)
  const hasKey = apiKeys[provider]?.has_key || newApiKey.length > 0
  const needsKey = currentProvider?.requires_api_key && !hasKey

  // Update models when provider changes
  useEffect(() => {
    const selectedProvider = providers.find(p => p.id === provider)
    if (selectedProvider && !newLlmModel) {
      setCurrentLlmModel(selectedProvider.llm_model || '')
    }
    if (selectedProvider && !newVlmModel) {
      setCurrentVlmModel(selectedProvider.vlm_model || '')
    }
  }, [provider, providers])

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider)
    setNewApiKey('')
    setNewBaseUrl('')
    setNewLlmModel('')
    setNewVlmModel('')
    setHasChanges(true)
  }

  const handleTestConnection = () => {
    setIsTesting(true)
    send('model_connection_test', {
      provider,
      apiKey: newApiKey || undefined,
      baseUrl: newBaseUrl || baseUrls[provider],
    })
  }

  const handleSave = () => {
    const isChangingApiKey = newApiKey.length > 0
    const isChangingBaseUrl = newBaseUrl.length > 0

    if (isChangingApiKey || isChangingBaseUrl) {
      setTestBeforeSave(true)
      setIsTesting(true)
      send('model_connection_test', {
        provider,
        apiKey: newApiKey || undefined,
        baseUrl: newBaseUrl || baseUrls[provider],
      })
    } else {
      setIsSaving(true)
      send('model_settings_update', {
        llmProvider: provider,
        vlmProvider: provider,
        llmModel: newLlmModel || currentLlmModel || undefined,
        vlmModel: newVlmModel || currentVlmModel || undefined,
      })
    }
  }

  const handleDownloadModelClick = () => {
    setPullPhase('selecting')
    setPullBytes(null)
    setPullStatus('')
    setModelSearch('')
    if (suggestedModels.length === 0) {
      send('local_llm_suggested_models')
    }
  }

  const handleStartPull = () => {
    if (!selectedPullModel) return
    setPullPhase('pulling')
    send('local_llm_pull_model', { model: selectedPullModel, baseUrl: newBaseUrl || baseUrls['remote'] || undefined })
  }

  return (
    <div className={styles.settingsSection}>
      <div className={styles.sectionHeader}>
        <h3>Model Configuration</h3>
        <p>Configure AI provider and API key</p>
      </div>

      {isLoading ? (
        <div className={styles.loadingState}>
          <Loader2 size={20} className={styles.spinning} />
          <span>Loading...</span>
        </div>
      ) : (
        <div className={styles.settingsForm}>
          {/* Provider Selection */}
          <div className={styles.formGroup}>
            <label>Provider</label>
            <select value={provider} onChange={(e) => handleProviderChange(e.target.value)}>
              {providers.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Model Configuration */}
          {currentProvider && (
            <>
              <div className={styles.formGroup}>
                <label>LLM Model</label>
                {provider === 'remote' && ollamaModels.length > 0 ? (
                  <select
                    value={newLlmModel || currentLlmModel || ''}
                    onChange={(e) => { setNewLlmModel(e.target.value); setHasChanges(true) }}
                  >
                    {ollamaModels.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={newLlmModel || currentLlmModel || ''}
                    onChange={(e) => { setNewLlmModel(e.target.value); setHasChanges(true) }}
                    placeholder={
                      provider === 'remote' && ollamaModelsLoading
                        ? 'Loading models...'
                        : currentLlmModel || 'Enter LLM model name...'
                    }
                  />
                )}
              </div>

              {/* Download new Ollama model */}
              {provider === 'remote' && (
                <div className={styles.ollamaDownloadSection}>
                  {pullPhase === 'idle' && (
                    <button className={styles.downloadModelBtn} onClick={handleDownloadModelClick}>
                      + Download New Model
                    </button>
                  )}

                  {pullPhase === 'selecting' && (
                    <div className={styles.pullModelPanel}>
                      <div className={styles.pullPanelHeader}>
                        <span>Select model to download</span>
                        <button onClick={() => setPullPhase('idle')}>&#x2715;</button>
                      </div>
                      <input
                        className={styles.pullModelSearch}
                        placeholder="Search models..."
                        value={modelSearch}
                        onChange={e => setModelSearch(e.target.value)}
                      />
                      <div className={styles.pullModelList}>
                        {suggestedModels
                          .filter(m =>
                            m.name.toLowerCase().includes(modelSearch.toLowerCase()) ||
                            m.label.toLowerCase().includes(modelSearch.toLowerCase())
                          )
                          .map(m => (
                            <label
                              key={m.name}
                              className={`${styles.pullModelItem} ${selectedPullModel === m.name ? styles.pullModelItemSelected : ''}`}
                            >
                              <input
                                type="radio"
                                checked={selectedPullModel === m.name}
                                onChange={() => setSelectedPullModel(m.name)}
                              />
                              <span className={styles.pullModelName}>{m.label}</span>
                              <span className={styles.pullModelSize}>{m.size}</span>
                              {m.recommended && <span className={styles.pullModelBadge}>Recommended</span>}
                            </label>
                          ))}
                      </div>
                      <div className={styles.pullPanelFooter}>
                        <button
                          className={styles.pullStartBtn}
                          onClick={handleStartPull}
                          disabled={!selectedPullModel}
                        >
                          Download
                        </button>
                      </div>
                    </div>
                  )}

                  {pullPhase === 'pulling' && (
                    <div className={styles.pullProgressPanel}>
                      <span>Downloading {selectedPullModel}...</span>
                      {pullBytes && pullBytes.total > 0 ? (
                        <>
                          <div className={styles.pullProgressBar}>
                            <div className={styles.pullProgressFill} style={{ width: `${pullBytes.percent}%` }} />
                          </div>
                          <div className={styles.pullProgressInfo}>
                            <span>{fmtBytes(pullBytes.completed)} / {fmtBytes(pullBytes.total)}</span>
                            <span>{pullBytes.percent}%</span>
                          </div>
                        </>
                      ) : (
                        <div className={styles.pullProgressBar}>
                          <div className={styles.pullProgressFill} style={{ width: '0%' }} />
                        </div>
                      )}
                      <p className={styles.pullStatusText}>{pullStatus || 'Starting...'}</p>
                    </div>
                  )}
                </div>
              )}

              {currentProvider.has_vlm && (
                <div className={styles.formGroup}>
                  <label>VLM Model</label>
                  {(() => {
                    const visionKeywords = ['llava', 'vision', 'moondream', 'bakllava']
                    const visionModels = ollamaModels.filter(m =>
                      visionKeywords.some(kw => m.toLowerCase().includes(kw))
                    )
                    const vlmOptions = provider === 'remote' && ollamaModels.length > 0
                      ? (visionModels.length > 0 ? visionModels : ollamaModels)
                      : []
                    return vlmOptions.length > 0 ? (
                      <select
                        value={newVlmModel || currentVlmModel || ''}
                        onChange={(e) => { setNewVlmModel(e.target.value); setHasChanges(true) }}
                      >
                        {vlmOptions.map(m => <option key={m} value={m}>{m}</option>)}
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={newVlmModel || currentVlmModel || ''}
                        onChange={(e) => { setNewVlmModel(e.target.value); setHasChanges(true) }}
                        placeholder={
                          provider === 'remote' && ollamaModelsLoading
                            ? 'Loading models...'
                            : currentVlmModel || 'Enter VLM model name...'
                        }
                      />
                    )
                  })()}
                </div>
              )}
            </>
          )}

          {/* API Key */}
          {currentProvider?.requires_api_key && (
            <div className={styles.formGroup}>
              <label>
                API Key
                {apiKeys[provider]?.has_key ? (
                  <Badge variant="success" style={{ marginLeft: 8 }}>Configured</Badge>
                ) : (
                  <Badge variant="warning" style={{ marginLeft: 8 }}>Required</Badge>
                )}
              </label>
              {apiKeys[provider]?.has_key && (
                <div className={styles.maskedKey}>{apiKeys[provider].masked_key}</div>
              )}
              <input
                type="password"
                value={newApiKey}
                onChange={(e) => { setNewApiKey(e.target.value); setHasChanges(true) }}
                placeholder={apiKeys[provider]?.has_key ? 'Enter new key to replace...' : 'Enter API key...'}
              />
            </div>
          )}

          {/* Base URL */}
          {currentProvider?.base_url_env && (
            <div className={styles.formGroup}>
              <label>Server URL</label>
              <input
                type="text"
                value={newBaseUrl || baseUrls[provider] || ''}
                onChange={(e) => { setNewBaseUrl(e.target.value); setHasChanges(true) }}
                placeholder={provider === 'remote' ? 'http://localhost:11434' : 'Enter base URL...'}
              />
            </div>
          )}

          {/* Actions */}
          <div className={styles.sectionFooter} style={{ borderTop: 'none', paddingTop: 0 }}>
            <Button
              variant="secondary"
              onClick={handleTestConnection}
              disabled={isTesting || (provider !== 'remote' && !apiKeys[provider]?.has_key)}
              title={provider !== 'remote' && !apiKeys[provider]?.has_key ? 'API key required for testing' : ''}
            >
              {isTesting ? (
                <>
                  <Loader2 size={14} className={styles.spinning} />
                  Testing...
                </>
              ) : (
                'Test Connection'
              )}
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={isSaving || isTesting || !hasChanges}
            >
              {isSaving ? (
                <>
                  <Loader2 size={14} className={styles.spinning} />
                  Saving...
                </>
              ) : isTesting && testBeforeSave ? (
                <>
                  <Loader2 size={14} className={styles.spinning} />
                  Testing Connection...
                </>
              ) : (
                'Save'
              )}
            </Button>
          </div>

          {/* Slow Mode */}
          <hr style={{ border: 'none', borderTop: '1px solid var(--border-primary)', margin: 'var(--space-4) 0' }} />
          <div className={styles.toggleGroup}>
            <div className={styles.toggleInfo}>
              <span className={styles.toggleLabel}>Slow Mode</span>
              <span className={styles.toggleDesc}>
                Limits token usage to stay within API rate limits.
                Enable this if you experience rate limiting errors from your provider.
              </span>
            </div>
            <input
              type="checkbox"
              className={styles.toggle}
              checked={slowModeEnabled}
              onChange={(e) => {
                setSlowModeEnabled(e.target.checked)
                send('slow_mode_set', { enabled: e.target.checked })
              }}
              disabled={isLoadingSlowMode}
            />
          </div>
        </div>
      )}

      {/* Connection Test Result Modal */}
      {testResult && (
        <div className={styles.modalOverlay} onClick={() => { setTestResult(null); setTestBeforeSave(false) }}>
          <div className={styles.testResultModal} onClick={e => e.stopPropagation()}>
            <div className={`${styles.testResultIcon} ${testResult.success ? styles.success : styles.error}`}>
              {testResult.success ? <Check size={32} /> : <X size={32} />}
            </div>
            <h3 className={styles.testResultTitle}>
              {testResult.success ? (
                testBeforeSave ? 'Connection and Configuration Successful' : 'Connection Successful'
              ) : (
                'Connection Failed'
              )}
            </h3>
            <p className={styles.testResultMessage}>
              {testResult.success ? (
                testBeforeSave ? (
                  <span style={{ textAlign: 'center', display: 'block' }}>
                    <span>{testResult.message}</span>
                    <span style={{ marginTop: 12, fontWeight: 600, color: '#10b981', display: 'block' }}>
                      &#x2713; Configuration saved successfully
                    </span>
                  </span>
                ) : (
                  testResult.message
                )
              ) : (
                testResult.error || testResult.message
              )}
            </p>
            <Button variant="secondary" onClick={() => { setTestResult(null); setTestBeforeSave(false) }}>
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
