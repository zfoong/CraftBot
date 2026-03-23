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

// Provider info type
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

// API key status type
interface ApiKeyStatus {
  has_key: boolean
  masked_key: string
}

// Connection test result type
interface TestResult {
  success: boolean
  message: string
  error?: string
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

  // UI state
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [testBeforeSave, setTestBeforeSave] = useState(false)

  // Set up message handlers (runs once when connected)
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
          // Only set provider and models on initial load
          setProvider(d.llm_provider || 'anthropic')
          setApiKeys(d.api_keys || {})
          setBaseUrls(d.base_urls || {})

          // Load custom models if set, or initialize from current provider defaults
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

        // If this test is before save and it was successful, proceed with save
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
          // Test failed, don't save and reset the flag
          setTestBeforeSave(false)
        }
      }),
    ]

    return () => cleanups.forEach(cleanup => cleanup())
  }, [isConnected, onMessage, send, testBeforeSave, provider, newApiKey, newBaseUrl])

  // Load initial data only once when connected
  useEffect(() => {
    if (!isConnected || hasInitialized.current) return

    send('model_providers_get')
    send('model_settings_get')
  }, [isConnected, send])

  const currentProvider = providers.find(p => p.id === provider)
  const hasKey = apiKeys[provider]?.has_key || newApiKey.length > 0
  const needsKey = currentProvider?.requires_api_key && !hasKey

  // Update models when provider changes (only)
  useEffect(() => {
    // Find the provider definition
    const selectedProvider = providers.find(p => p.id === provider)
    if (selectedProvider && !newLlmModel) {
      setCurrentLlmModel(selectedProvider.llm_model || '')
    }
    if (selectedProvider && !newVlmModel) {
      setCurrentVlmModel(selectedProvider.vlm_model || '')
    }
  }, [provider, providers]) // Only depend on provider and providers list changes

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider)
    setNewApiKey('')
    setNewBaseUrl('')
    // Clear any edited model inputs when switching providers
    // The useEffect will automatically update currentLlmModel/currentVlmModel
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
    // Allow saving provider and model changes even without API key
    // Only test connection if adding/changing API key or base URL
    const isChangingApiKey = newApiKey.length > 0
    const isChangingBaseUrl = newBaseUrl.length > 0

    if (isChangingApiKey || isChangingBaseUrl) {
      // Test connection before saving when changing credentials
      setTestBeforeSave(true)
      setIsTesting(true)
      send('model_connection_test', {
        provider,
        apiKey: newApiKey || undefined,
        baseUrl: newBaseUrl || baseUrls[provider],
      })
    } else {
      // Save provider/model changes directly without testing
      setIsSaving(true)
      send('model_settings_update', {
        llmProvider: provider,
        vlmProvider: provider,
        llmModel: newLlmModel || currentLlmModel || undefined,
        vlmModel: newVlmModel || currentVlmModel || undefined,
      })
    }
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
                <input
                  type="text"
                  value={newLlmModel || currentLlmModel || ''}
                  onChange={(e) => { setNewLlmModel(e.target.value); setHasChanges(true) }}
                  placeholder={currentLlmModel || 'Enter LLM model name...'}
                />
              </div>
              {currentProvider.has_vlm && (
                <div className={styles.formGroup}>
                  <label>VLM Model</label>
                  <input
                    type="text"
                    value={newVlmModel || currentVlmModel || ''}
                    onChange={(e) => { setNewVlmModel(e.target.value); setHasChanges(true) }}
                    placeholder={currentVlmModel || 'Enter VLM model name...'}
                  />
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

          {/* Base URL (for Ollama/BytePlus) */}
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
          <div className={styles.sectionFooter}>
            <Button
              variant="secondary"
              onClick={handleTestConnection}
              disabled={isTesting || !apiKeys[provider]?.has_key}
              title={!apiKeys[provider]?.has_key ? 'API key required for testing' : ''}
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
                  <div style={{ textAlign: 'center' }}>
                    <div>{testResult.message}</div>
                    <div style={{ marginTop: 12, fontWeight: 600, color: '#10b981' }}>
                      ✓ Configuration saved successfully
                    </div>
                  </div>
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
