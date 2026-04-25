/**
 * Profile Page — edit username, email, and change password.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 *
 * Usage:
 *   import { ProfilePage } from './components/auth/ProfilePage'
 *   {showProfile && <ProfilePage onClose={() => setShowProfile(false)} />}
 */

import { useState } from 'react'
import { Button, Card, Alert } from '../ui'
import { useAuth } from './AuthProvider'
import { FormField } from './AuthLayout'
import { authService } from '../../services/AuthService'

interface ProfilePageProps {
  onClose?: () => void
}

export function ProfilePage({ onClose }: ProfilePageProps) {
  const { user, logout } = useAuth()

  const [username, setUsername] = useState(user?.username || '')
  const [email, setEmail] = useState(user?.email || '')
  const [profileMsg, setProfileMsg] = useState('')
  const [profileErr, setProfileErr] = useState('')
  const [profileLoading, setProfileLoading] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordMsg, setPasswordMsg] = useState('')
  const [passwordErr, setPasswordErr] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileMsg(''); setProfileErr('')
    setProfileLoading(true)
    try {
      await authService.updateProfile({ username, email })
      setProfileMsg('Profile updated')
    } catch (err) {
      setProfileErr(err instanceof Error ? err.message : 'Update failed')
    } finally {
      setProfileLoading(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordMsg(''); setPasswordErr('')
    if (newPassword !== confirmPassword) { setPasswordErr('Passwords do not match'); return }
    if (newPassword.length < 6) { setPasswordErr('Password must be at least 6 characters'); return }
    setPasswordLoading(true)
    try {
      await authService.changePassword(currentPassword, newPassword)
      setPasswordMsg('Password changed')
      setCurrentPassword(''); setNewPassword(''); setConfirmPassword('')
    } catch (err) {
      setPasswordErr(err instanceof Error ? err.message : 'Password change failed')
    } finally {
      setPasswordLoading(false)
    }
  }

  if (!user) return null

  return (
    <div style={{ maxWidth: 500, margin: '0 auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {onClose && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 'var(--font-weight-semibold)', margin: 0, color: 'var(--text-primary)' }}>Profile</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>Back</Button>
        </div>
      )}

      <Card style={{ padding: 'var(--space-4)' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)', color: 'var(--text-primary)' }}>
          Account Info
        </h3>
        {profileMsg && <Alert variant="success" style={{ marginBottom: 'var(--space-3)' }}>{profileMsg}</Alert>}
        {profileErr && <Alert variant="error" style={{ marginBottom: 'var(--space-3)' }}>{profileErr}</Alert>}
        <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <FormField label="Username" value={username} onChange={setUsername} />
          <FormField label="Email" type="email" value={email} onChange={setEmail} />
          <Button type="submit" variant="primary" loading={profileLoading}>Save Changes</Button>
        </form>
      </Card>

      <Card style={{ padding: 'var(--space-4)' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)', color: 'var(--text-primary)' }}>
          Change Password
        </h3>
        {passwordMsg && <Alert variant="success" style={{ marginBottom: 'var(--space-3)' }}>{passwordMsg}</Alert>}
        {passwordErr && <Alert variant="error" style={{ marginBottom: 'var(--space-3)' }}>{passwordErr}</Alert>}
        <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <FormField label="Current Password" type="password" value={currentPassword} onChange={setCurrentPassword} required />
          <FormField label="New Password" type="password" value={newPassword} onChange={setNewPassword} placeholder="At least 6 characters" required />
          <FormField label="Confirm New Password" type="password" value={confirmPassword} onChange={setConfirmPassword} required />
          <Button type="submit" variant="primary" loading={passwordLoading}>Change Password</Button>
        </form>
      </Card>

      <Card style={{ padding: 'var(--space-4)', borderColor: 'var(--color-error)' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-2)', color: 'var(--color-error)' }}>
          Sign Out
        </h3>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', margin: '0 0 var(--space-3)' }}>
          You will need to sign in again to access your account.
        </p>
        <Button variant="danger" onClick={logout}>Sign Out</Button>
      </Card>
    </div>
  )
}
