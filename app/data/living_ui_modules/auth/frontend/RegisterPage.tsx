/**
 * Register Page — email, username, password form using preset UI components.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 */

import { useState } from 'react'
import { Button } from '../ui'
import { useAuth } from './AuthProvider'
import { AuthLayout, FormField, AuthSwitchLink } from './AuthLayout'

interface RegisterPageProps {
  onSwitchToLogin: () => void
}

export function RegisterPage({ onSwitchToLogin }: RegisterPageProps) {
  const { register } = useAuth()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    try {
      await register(email, username, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Create Account"
      error={error}
      footer={<AuthSwitchLink text="Already have an account?" linkText="Sign in" onClick={onSwitchToLogin} />}
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <FormField label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" required />
        <FormField label="Username" value={username} onChange={setUsername} placeholder="Choose a username" required />
        <FormField label="Password" type="password" value={password} onChange={setPassword} placeholder="At least 6 characters" required />
        <FormField label="Confirm Password" type="password" value={confirmPassword} onChange={setConfirmPassword} placeholder="Re-enter your password" required />
        <Button type="submit" variant="primary" fullWidth loading={loading}>Create Account</Button>
      </form>
    </AuthLayout>
  )
}
