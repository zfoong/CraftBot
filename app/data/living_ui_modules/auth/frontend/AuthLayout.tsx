/**
 * Auth Layout — shared wrapper for login, register, and profile pages.
 * Also exports FormField for consistent label + input pairs.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 */

import { ReactNode } from 'react'
import { Card, Input, Alert } from '../ui'

// ── Centered card layout for auth pages ────────────────────────

interface AuthLayoutProps {
  title: string
  children: ReactNode
  error?: string
  footer?: ReactNode
}

export function AuthLayout({ title, children, error, footer }: AuthLayoutProps) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: 'var(--bg-primary)', padding: 'var(--space-4)',
    }}>
      <Card style={{ width: '100%', maxWidth: 400, padding: 'var(--space-6)' }}>
        <h2 style={{
          fontSize: 'var(--text-xl)', fontWeight: 'var(--font-weight-semibold)',
          textAlign: 'center', marginBottom: 'var(--space-6)', color: 'var(--text-primary)',
        }}>
          {title}
        </h2>
        {error && <Alert variant="error" style={{ marginBottom: 'var(--space-4)' }}>{error}</Alert>}
        {children}
        {footer}
      </Card>
    </div>
  )
}

// ── Label + Input pair ─────────────────────────────────────────

interface FormFieldProps {
  label: string
  type?: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
  readOnly?: boolean
}

const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: 'var(--text-sm)',
  fontWeight: 'var(--font-weight-medium)' as any,
  marginBottom: 'var(--space-1)', color: 'var(--text-secondary)',
}

export function FormField({ label, type = 'text', value, onChange, placeholder, required, readOnly }: FormFieldProps) {
  return (
    <div>
      <label style={labelStyle}>{label}</label>
      <Input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        readOnly={readOnly}
      />
    </div>
  )
}

// ── Switch link ("Don't have an account? Sign up") ─────────────

interface AuthSwitchLinkProps {
  text: string
  linkText: string
  onClick: () => void
}

export function AuthSwitchLink({ text, linkText, onClick }: AuthSwitchLinkProps) {
  return (
    <p style={{
      textAlign: 'center', marginTop: 'var(--space-4)',
      fontSize: 'var(--text-sm)', color: 'var(--text-muted)',
    }}>
      {text}{' '}
      <button
        onClick={onClick}
        style={{
          background: 'none', border: 'none', color: 'var(--color-primary)',
          cursor: 'pointer', fontSize: 'inherit', fontFamily: 'inherit',
          textDecoration: 'underline',
        }}
      >
        {linkText}
      </button>
    </p>
  )
}
