import React, { useState, useEffect, useRef, useMemo } from 'react'
import { X, Sparkles } from 'lucide-react'
import { Button } from './Button'
import type { LivingUICreateRequest } from '../../types'
import styles from './CreateLivingUIModal.module.css'

export interface CreateLivingUIModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: LivingUICreateRequest) => void
}

const MAX_WORDS = 5000

// Count words in a string
function countWords(text: string): number {
  const trimmed = text.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).length
}

export function CreateLivingUIModal({ isOpen, onClose, onSubmit }: CreateLivingUIModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({})

  const nameInputRef = useRef<HTMLInputElement>(null)

  // Word count for description
  const wordCount = useMemo(() => countWords(description), [description])

  // Reset form and focus on open
  useEffect(() => {
    if (isOpen) {
      setName('')
      setDescription('')
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
    } else if (wordCount > MAX_WORDS) {
      newErrors.description = `Description exceeds ${MAX_WORDS} word limit`
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
      </div>
    </div>
  )
}
