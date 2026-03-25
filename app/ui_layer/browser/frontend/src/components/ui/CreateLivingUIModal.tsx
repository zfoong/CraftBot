import React, { useState, useEffect, useRef } from 'react'
import { X, Sparkles, BarChart3, FormInput, Zap, Globe, Bell } from 'lucide-react'
import { Button } from './Button'
import type { LivingUICreateRequest } from '../../types'
import styles from './CreateLivingUIModal.module.css'

export interface CreateLivingUIModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: LivingUICreateRequest) => void
}

interface FeatureOption {
  id: string
  label: string
  icon: React.ReactNode
  description: string
}

const featureOptions: FeatureOption[] = [
  { id: 'data-display', label: 'Data Display', icon: <BarChart3 size={16} />, description: 'Tables, charts, visualizations' },
  { id: 'forms', label: 'Forms', icon: <FormInput size={16} />, description: 'User input and data entry' },
  { id: 'realtime', label: 'Real-time', icon: <Zap size={16} />, description: 'Live updates and streaming' },
  { id: 'api', label: 'API Integration', icon: <Globe size={16} />, description: 'External data sources' },
  { id: 'notifications', label: 'Notifications', icon: <Bell size={16} />, description: 'Alerts and reminders' },
]

export function CreateLivingUIModal({ isOpen, onClose, onSubmit }: CreateLivingUIModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([])
  const [dataSource, setDataSource] = useState('')
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system')
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({})

  const nameInputRef = useRef<HTMLInputElement>(null)

  // Reset form and focus on open
  useEffect(() => {
    if (isOpen) {
      setName('')
      setDescription('')
      setSelectedFeatures([])
      setDataSource('')
      setTheme('system')
      setErrors({})
      // Focus name input after a brief delay for animation
      setTimeout(() => nameInputRef.current?.focus(), 100)
    }
  }, [isOpen])

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const toggleFeature = (featureId: string) => {
    setSelectedFeatures(prev =>
      prev.includes(featureId)
        ? prev.filter(f => f !== featureId)
        : [...prev, featureId]
    )
  }

  const validate = (): boolean => {
    const newErrors: { name?: string; description?: string } = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    } else if (name.length > 50) {
      newErrors.name = 'Name must be 50 characters or less'
    }

    if (!description.trim()) {
      newErrors.description = 'Description is required'
    } else if (description.length < 10) {
      newErrors.description = 'Please provide more detail (at least 10 characters)'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    onSubmit({
      name: name.trim(),
      description: description.trim(),
      features: selectedFeatures,
      dataSource: dataSource.trim() || undefined,
      theme,
    })
  }

  if (!isOpen) return null

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.headerTitle}>
            <Sparkles size={20} className={styles.headerIcon} />
            <h3>Create Living UI</h3>
          </div>
          <button className={styles.modalClose} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            {/* Project Name */}
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

            {/* Description */}
            <div className={styles.formGroup}>
              <label htmlFor="living-ui-description" className={styles.label}>
                What should this UI do? <span className={styles.required}>*</span>
              </label>
              <textarea
                id="living-ui-description"
                className={`${styles.textarea} ${errors.description ? styles.inputError : ''}`}
                placeholder="Describe what you want the Living UI to display and do. Be specific about the data, layout, and interactions..."
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={4}
              />
              {errors.description && <span className={styles.errorText}>{errors.description}</span>}
            </div>

            {/* Features */}
            <div className={styles.formGroup}>
              <label className={styles.label}>Features (optional)</label>
              <div className={styles.featureGrid}>
                {featureOptions.map(feature => (
                  <button
                    key={feature.id}
                    type="button"
                    className={`${styles.featureOption} ${selectedFeatures.includes(feature.id) ? styles.featureSelected : ''}`}
                    onClick={() => toggleFeature(feature.id)}
                    title={feature.description}
                  >
                    <span className={styles.featureIcon}>{feature.icon}</span>
                    <span className={styles.featureLabel}>{feature.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Data Source */}
            <div className={styles.formGroup}>
              <label htmlFor="living-ui-datasource" className={styles.label}>
                Data Source (optional)
              </label>
              <input
                id="living-ui-datasource"
                type="text"
                className={styles.input}
                placeholder="API URL or description of data source..."
                value={dataSource}
                onChange={e => setDataSource(e.target.value)}
              />
              <span className={styles.hint}>Leave empty to use mock data or agent-generated data</span>
            </div>

            {/* Theme */}
            <div className={styles.formGroup}>
              <label className={styles.label}>Theme</label>
              <div className={styles.themeOptions}>
                {(['system', 'light', 'dark'] as const).map(themeOption => (
                  <button
                    key={themeOption}
                    type="button"
                    className={`${styles.themeOption} ${theme === themeOption ? styles.themeSelected : ''}`}
                    onClick={() => setTheme(themeOption)}
                  >
                    {themeOption.charAt(0).toUpperCase() + themeOption.slice(1)}
                  </button>
                ))}
              </div>
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
      </div>
    </div>
  )
}
