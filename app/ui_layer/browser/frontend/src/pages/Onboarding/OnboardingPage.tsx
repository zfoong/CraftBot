import React, { useEffect, useState, useCallback } from 'react'
import {
  Check,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  SkipForward,
  // Icons for MCP servers and Skills
  Folder,
  Search,
  Github,
  Globe,
  FileText,
  MessageSquare,
  Mail,
  Calendar,
  CheckSquare,
  Gem,
  FlaskConical,
  Pencil,
  ClipboardList,
  Cloud,
  Sheet,
  Download,
  Play,
  Wifi,
  WifiOff,
  RefreshCw,
  type LucideIcon,
} from 'lucide-react'
import { Button } from '../../components/ui'
import { useWebSocket } from '../../contexts/WebSocketContext'
import type { OnboardingStep, OnboardingStepOption } from '../../types'
import styles from './OnboardingPage.module.css'

// Icon mapping for dynamic rendering
const ICON_MAP: Record<string, LucideIcon> = {
  Folder,
  Search,
  Github,
  Globe,
  FileText,
  MessageSquare,
  Mail,
  Calendar,
  CheckSquare,
  Gem,
  FlaskConical,
  Pencil,
  ClipboardList,
  Cloud,
  Sheet,
}

const STEP_NAMES = ['Provider', 'API Key', 'Agent Name', 'MCP Servers', 'Skills']

// ── Ollama local-setup component ─────────────────────────────────────────────

interface OllamaSetupProps {
  defaultUrl: string
  onConnected: (url: string) => void
}

function OllamaSetup({ defaultUrl, onConnected }: OllamaSetupProps) {
  const { localLLM, checkLocalLLM, testLocalLLMConnection, installLocalLLM, startLocalLLM, pullOllamaModel } = useWebSocket()
  const [url, setUrl] = useState(defaultUrl)
  const [selectedModel, setSelectedModel] = useState('llama3.2:3b')
  const [modelSearch, setModelSearch] = useState('')

  // Auto-check on mount
  useEffect(() => {
    checkLocalLLM()
  }, [checkLocalLLM])

  // Pre-select the recommended model when the list loads
  useEffect(() => {
    if (localLLM.suggestedModels.length > 0) {
      const rec = localLLM.suggestedModels.find(m => m.recommended)
      if (rec) setSelectedModel(rec.name)
    }
  }, [localLLM.suggestedModels])

  // Notify parent when connected
  useEffect(() => {
    if (localLLM.phase === 'connected' && localLLM.testResult?.success) {
      onConnected(url)
    }
  }, [localLLM.phase, localLLM.testResult, url, onConnected])

  const { phase, installProgress, testResult, error } = localLLM

  const isWorking = phase === 'checking' || phase === 'installing' || phase === 'starting' || phase === 'pulling_model'

  // ── Checking ──
  if (phase === 'idle' || phase === 'checking') {
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaChecking}>
          <div className={styles.spinner} />
          <span>Checking if Ollama is running…</span>
        </div>
      </div>
    )
  }

  // ── Not installed ──
  if (phase === 'not_installed') {
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaStatusRow}>
          <WifiOff size={18} className={styles.iconError} />
          <span className={styles.ollamaStatusLabel}>Ollama is not installed</span>
        </div>
        <p className={styles.ollamaHint}>
          Ollama lets you run AI models locally — no cloud needed. We'll install it automatically for you.
        </p>
        <Button variant="primary" onClick={installLocalLLM} icon={<Download size={16} />}>
          Install Ollama
        </Button>
      </div>
    )
  }

  // ── Installing ──
  if (phase === 'installing') {
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaStatusRow}>
          <div className={styles.spinnerSmall} />
          <span className={styles.ollamaStatusLabel}>Installing Ollama…</span>
        </div>
        <div className={styles.installLog}>
          {installProgress.length === 0 && <span className={styles.installLogLine}>Starting…</span>}
          {installProgress.map((line, i) => (
            <span key={i} className={styles.installLogLine}>{line}</span>
          ))}
        </div>
      </div>
    )
  }

  // ── Installed but not running ──
  if (phase === 'not_running') {
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaStatusRow}>
          <WifiOff size={18} className={styles.iconWarning} />
          <span className={styles.ollamaStatusLabel}>Ollama is installed but not running</span>
        </div>
        <p className={styles.ollamaHint}>Click below to start the Ollama server.</p>
        <Button variant="primary" onClick={startLocalLLM} icon={<Play size={16} />}>
          Start Ollama
        </Button>
      </div>
    )
  }

  // ── Starting ──
  if (phase === 'starting') {
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaStatusRow}>
          <div className={styles.spinnerSmall} />
          <span className={styles.ollamaStatusLabel}>Starting Ollama…</span>
        </div>
      </div>
    )
  }

  // ── Error ──
  if (phase === 'error') {
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaStatusRow}>
          <AlertCircle size={18} className={styles.iconError} />
          <span className={styles.ollamaStatusLabel}>Something went wrong</span>
        </div>
        {error && <p className={styles.ollamaHint}>{error}</p>}
        <Button variant="secondary" onClick={checkLocalLLM} icon={<RefreshCw size={16} />}>
          Retry
        </Button>
      </div>
    )
  }

  // ── Select model ──
  if (phase === 'selecting_model') {
    const allModels = localLLM.suggestedModels.length > 0 ? localLLM.suggestedModels : []
    const filteredModels = allModels.filter(m =>
      m.name.toLowerCase().includes(modelSearch.toLowerCase()) ||
      m.label.toLowerCase().includes(modelSearch.toLowerCase())
    )
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaStatusRow}>
          <Wifi size={18} className={styles.iconMuted} />
          <span className={styles.ollamaStatusLabel}>Ollama is running — no models yet</span>
        </div>
        <p className={styles.ollamaHint}>Select a model to download so you can start chatting:</p>
        <input
          className={styles.modelSearchInput}
          type="text"
          placeholder="Find model..."
          value={modelSearch}
          onChange={e => setModelSearch(e.target.value)}
        />
        <div className={styles.modelList}>
          {filteredModels.map(m => (
            <label key={m.name} className={`${styles.modelOption} ${selectedModel === m.name ? styles.modelOptionSelected : ''}`}>
              <input
                type="radio"
                name="ollama_model"
                value={m.name}
                checked={selectedModel === m.name}
                onChange={() => setSelectedModel(m.name)}
              />
              <span className={styles.modelOptionName}>{m.label}</span>
              <span className={styles.modelOptionSize}>{m.size}</span>
              {m.recommended && <span className={styles.modelOptionBadge}>Recommended</span>}
            </label>
          ))}
          {filteredModels.length === 0 && (
            <p className={styles.ollamaHint}>No models match "{modelSearch}"</p>
          )}
        </div>
        <Button variant="primary" onClick={() => pullOllamaModel(selectedModel)} disabled={!selectedModel} icon={<Download size={16} />}>
          Download {selectedModel || 'Model'}
        </Button>
      </div>
    )
  }

  // ── Pulling model ──
  if (phase === 'pulling_model') {
    const bytes = localLLM.pullBytes
    const fmtBytes = (n: number) => {
      if (n >= 1073741824) return `${(n / 1073741824).toFixed(1)} GB`
      if (n >= 1048576) return `${(n / 1048576).toFixed(0)} MB`
      return `${(n / 1024).toFixed(0)} KB`
    }
    const latestStatus = localLLM.pullProgress[localLLM.pullProgress.length - 1] ?? 'Starting download…'
    return (
      <div className={styles.ollamaBox}>
        <div className={styles.ollamaStatusRow}>
          <div className={styles.spinnerSmall} />
          <span className={styles.ollamaStatusLabel}>Downloading {selectedModel}…</span>
        </div>
        {bytes && bytes.total > 0 ? (
          <>
            <div className={styles.downloadProgressBar}>
              <div className={styles.downloadProgressFill} style={{ width: `${bytes.percent}%` }} />
            </div>
            <div className={styles.downloadProgressInfo}>
              <span>{fmtBytes(bytes.completed)} / {fmtBytes(bytes.total)}</span>
              <span>{bytes.percent}%</span>
            </div>
          </>
        ) : (
          <div className={styles.downloadProgressBar}>
            <div className={styles.downloadProgressFill} style={{ width: '0%' }} />
          </div>
        )}
        <p className={styles.downloadStatus}>{latestStatus}</p>
      </div>
    )
  }

  // ── Running — show URL field + test button ──
  const connected = phase === 'connected' && testResult?.success

  return (
    <div className={styles.ollamaBox}>
      <div className={styles.ollamaStatusRow}>
        {connected
          ? <Wifi size={18} className={styles.iconSuccess} />
          : <Wifi size={18} className={styles.iconMuted} />}
        <span className={styles.ollamaStatusLabel}>
          {connected ? 'Connected to Ollama' : 'Ollama is running'}
        </span>
      </div>

      {connected && testResult?.message && (
        <p className={styles.ollamaSuccessMsg}>{testResult.message}</p>
      )}

      {!connected && (
        <>
          <label className={styles.ollamaLabel}>Ollama server URL</label>
          <div className={styles.ollamaInputRow}>
            <input
              className={styles.ollamaInput}
              type="text"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="http://localhost:11434"
              disabled={isWorking}
            />
            <Button
              variant="secondary"
              onClick={() => testLocalLLMConnection(url)}
              disabled={!url || isWorking}
              icon={<Wifi size={15} />}
            >
              Test
            </Button>
          </div>
          {testResult && !testResult.success && (
            <p className={styles.ollamaError}>{testResult.error}</p>
          )}
        </>
      )}
    </div>
  )
}

// ── Main onboarding page ──────────────────────────────────────────────────────

export function OnboardingPage() {
  const {
    connected,
    onboardingStep,
    onboardingError,
    onboardingLoading,
    requestOnboardingStep,
    submitOnboardingStep,
    skipOnboardingStep,
    goBackOnboardingStep,
    localLLM,
  } = useWebSocket()

  // Local form state
  const [selectedValue, setSelectedValue] = useState<string | string[]>('')
  const [textValue, setTextValue] = useState('')
  // URL submitted from OllamaSetup
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434')
  const [ollamaConnected, setOllamaConnected] = useState(false)

  // Request first step when connected
  useEffect(() => {
    if (connected && !onboardingStep && !onboardingLoading) {
      requestOnboardingStep()
    }
  }, [connected, onboardingStep, onboardingLoading, requestOnboardingStep])

  // Reset local state when step changes
  useEffect(() => {
    if (onboardingStep) {
      setOllamaConnected(false)

      if (onboardingStep.name === 'mcp' || onboardingStep.name === 'skills') {
        setSelectedValue(Array.isArray(onboardingStep.default) ? onboardingStep.default : [])
      } else if (onboardingStep.options.length > 0) {
        const defaultOption = onboardingStep.options.find(opt => opt.default)
        setSelectedValue(defaultOption?.value || onboardingStep.options[0]?.value || '')
      } else {
        setSelectedValue('')
        setTextValue(typeof onboardingStep.default === 'string' ? onboardingStep.default : '')
      }
    }
  }, [onboardingStep])

  // Keep ollamaUrl in sync with step default
  useEffect(() => {
    if (onboardingStep?.name === 'api_key' && onboardingStep.provider === 'remote') {
      const def = typeof onboardingStep.default === 'string' ? onboardingStep.default : 'http://localhost:11434'
      setOllamaUrl(def)
    }
  }, [onboardingStep])

  const handleOllamaConnected = useCallback((url: string) => {
    setOllamaUrl(url)
    setOllamaConnected(true)
  }, [])

  const handleOptionSelect = useCallback((value: string) => {
    if (!onboardingStep) return
    if (onboardingStep.name === 'mcp' || onboardingStep.name === 'skills') {
      setSelectedValue(prev => {
        const arr = Array.isArray(prev) ? prev : []
        return arr.includes(value) ? arr.filter(v => v !== value) : [...arr, value]
      })
    } else {
      setSelectedValue(value)
    }
  }, [onboardingStep])

  const handleSubmit = useCallback(() => {
    if (!onboardingStep) return
    const isOllamaStep = onboardingStep.name === 'api_key' && onboardingStep.provider === 'remote'

    if (isOllamaStep) {
      submitOnboardingStep(ollamaUrl)
    } else if (onboardingStep.options.length > 0) {
      submitOnboardingStep(selectedValue)
    } else {
      submitOnboardingStep(textValue)
    }
  }, [onboardingStep, selectedValue, textValue, ollamaUrl, submitOnboardingStep])

  const handleSkip = useCallback(() => skipOnboardingStep(), [skipOnboardingStep])
  const handleBack = useCallback(() => goBackOnboardingStep(), [goBackOnboardingStep])

  const isMultiSelect = onboardingStep?.name === 'mcp' || onboardingStep?.name === 'skills'
  const isWideStep = isMultiSelect
  const isLastStep = onboardingStep ? onboardingStep.index === onboardingStep.total - 1 : false

  const isOllamaStep =
    onboardingStep?.name === 'api_key' && onboardingStep?.provider === 'remote'

  const canSubmit = (() => {
    if (!onboardingStep) return false
    if (onboardingLoading) return false
    if (isOllamaStep) {
      return ollamaConnected || (localLLM.phase === 'connected' && !!localLLM.testResult?.success)
    }
    if (onboardingStep.options.length > 0) {
      return isMultiSelect ? true : !!selectedValue
    }
    return onboardingStep.required ? textValue.trim().length > 0 : true
  })()

  // Loading
  if (!connected || (!onboardingStep && onboardingLoading)) {
    return (
      <div className={styles.container}>
        <div className={styles.content}>
          <div className={styles.loading}>
            <div className={styles.spinner} />
            <div className={styles.loadingText}>
              {!connected ? 'Connecting...' : 'Loading...'}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Render step form ──────────────────────────────────────────────────────
  const renderStepForm = () => {
    if (!onboardingStep) return null

    // Ollama local setup
    if (isOllamaStep) {
      return (
        <div className={styles.formGroup}>
          <OllamaSetup
            defaultUrl={ollamaUrl}
            onConnected={handleOllamaConnected}
          />
        </div>
      )
    }

    // Option-based step
    if (onboardingStep.options.length > 0) {
      return (
        <div className={styles.formGroup}>
          <div className={styles.optionsList}>
            {onboardingStep.options.map((option: OnboardingStepOption) => {
              const isSelected = isMultiSelect
                ? Array.isArray(selectedValue) && selectedValue.includes(option.value)
                : selectedValue === option.value

              return (
                <div
                  key={option.value}
                  className={`${styles.optionItem} ${isSelected ? styles.selected : ''}`}
                  onClick={() => handleOptionSelect(option.value)}
                >
                  <div className={isMultiSelect ? styles.optionCheckbox : styles.optionRadio}>
                    {isMultiSelect && isSelected && <Check size={12} />}
                  </div>
                  <div className={styles.optionContent}>
                    <div className={styles.optionLabel}>
                      {option.icon && ICON_MAP[option.icon] && (
                        <span className={styles.optionIcon}>
                          {React.createElement(ICON_MAP[option.icon], { size: 16 })}
                        </span>
                      )}
                      {option.label}
                      {option.requires_setup && (
                        <span className={styles.setupBadge}>Setup required</span>
                      )}
                    </div>
                    {option.description && (
                      <div className={styles.optionDescription}>{option.description}</div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )
    }

    // Text input step
    const isApiKey = onboardingStep.name === 'api_key'
    return (
      <div className={styles.formGroup}>
        <input
          type={isApiKey ? 'password' : 'text'}
          className={`${styles.textInput} ${onboardingError ? styles.error : ''}`}
          value={textValue}
          onChange={e => setTextValue(e.target.value)}
          placeholder={isApiKey ? 'Enter your API key' : 'Enter a name'}
          autoFocus
          onKeyDown={e => { if (e.key === 'Enter' && canSubmit) handleSubmit() }}
        />
        {isApiKey && (
          <div className={styles.inputHint}>
            Your API key will be wiped once the session is over.
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Progress Bar */}
      <div className={styles.progressBar}>
        {STEP_NAMES.map((name, index) => {
          const currentIndex = onboardingStep?.index ?? 0
          const isActive = index === currentIndex
          const isCompleted = index < currentIndex

          return (
            <React.Fragment key={name}>
              <div className={styles.stepIndicator}>
                <div className={`${styles.stepDot} ${isActive ? styles.active : ''} ${isCompleted ? styles.completed : ''}`}>
                  {isCompleted ? <Check size={14} /> : index + 1}
                </div>
                <span className={`${styles.stepLabel} ${isActive ? styles.active : ''}`}>{name}</span>
              </div>
              {index < STEP_NAMES.length - 1 && (
                <div className={`${styles.stepConnector} ${isCompleted ? styles.completed : ''} ${index === currentIndex - 1 ? styles.active : ''}`} />
              )}
            </React.Fragment>
          )
        })}
      </div>

      {/* Main Content */}
      <div className={styles.content}>
        <div className={`${styles.card} ${isWideStep ? styles.wide : ''}`}>
          {onboardingStep && (
            <>
              <h2 className={styles.stepTitle}>
                {onboardingStep.title}
                {!onboardingStep.required && (
                  <span className={styles.optionalBadge}>Optional</span>
                )}
              </h2>
              <p className={styles.stepDescription}>
                {isOllamaStep ? (() => {
                  switch (localLLM.phase) {
                    case 'not_installed': return "Ollama isn't installed yet — we'll download and install it automatically."
                    case 'installing':    return "Installing Ollama on your machine. This may take a minute…"
                    case 'not_running':   return "Ollama is installed but not running. Click below to start the server."
                    case 'starting':      return "Starting the Ollama server…"
                    case 'running':       return "Ollama is running. Enter the server URL and test the connection."
                    case 'selecting_model': return "Ollama is connected but has no models yet. Pick one to download."
                    case 'pulling_model': return "Downloading your model — this may take a few minutes depending on size."
                    case 'connected': {
                      const n = localLLM.testResult?.models?.length ?? 0
                      return `Connected to Ollama — ${n} model${n === 1 ? '' : 's'} available.`
                    }
                    case 'error':         return localLLM.error ?? "Something went wrong. Check the error below and retry."
                    default:              return "Checking Ollama status…"
                  }
                })() : onboardingStep.description}
              </p>

              {/* Error Message */}
              {onboardingError && (
                <div className={styles.errorMessage}>
                  <AlertCircle size={16} />
                  {onboardingError}
                </div>
              )}

              {/* Step Form */}
              {renderStepForm()}

              {/* Navigation Buttons */}
              <div className={styles.buttons}>
                <div className={styles.buttonsLeft}>
                  {onboardingStep.index > 0 && (
                    <Button variant="ghost" onClick={handleBack} disabled={onboardingLoading} icon={<ChevronLeft size={16} />}>
                      Back
                    </Button>
                  )}
                </div>
                <div className={styles.buttonsRight}>
                  {!onboardingStep.required && (
                    <Button variant="secondary" onClick={handleSkip} disabled={onboardingLoading} icon={<SkipForward size={16} />}>
                      Skip
                    </Button>
                  )}
                  <Button
                    variant="primary"
                    onClick={handleSubmit}
                    disabled={!canSubmit}
                    loading={onboardingLoading}
                    icon={<ChevronRight size={16} />}
                    iconPosition="right"
                  >
                    {onboardingLoading && onboardingStep?.name === 'api_key'
                      ? (isOllamaStep ? 'Connecting…' : 'Testing API Key…')
                      : isLastStep ? 'Finish' : 'Next'}
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
