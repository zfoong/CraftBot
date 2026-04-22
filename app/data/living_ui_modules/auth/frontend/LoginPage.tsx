/**
 * Login Page — email + password form using preset UI components.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 */

import { useState } from 'react'
import { Button } from '../ui'
import { useAuth } from './AuthProvider'
import { AuthLayout, FormField, AuthSwitchLink } from './AuthLayout'

interface LoginPageProps {
  onSwitchToRegister: () => void
}

export function LoginPage({ onSwitchToRegister }: LoginPageProps) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Sign In"
      error={error}
      footer={<AuthSwitchLink text="Don't have an account?" linkText="Sign up" onClick={onSwitchToRegister} />}
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <FormField label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" required />
        <FormField label="Password" type="password" value={password} onChange={setPassword} placeholder="Enter your password" required />
        <Button type="submit" variant="primary" fullWidth loading={loading}>Sign In</Button>
      </form>
    </AuthLayout>
  )
}
