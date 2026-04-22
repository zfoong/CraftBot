/**
 * Invite Modal — create and share invite links for a resource.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 *
 * Usage:
 *   import { InviteModal } from './components/auth/InviteModal'
 *   <InviteModal
 *     resourceType="project"
 *     resourceId={project.id}
 *     isOpen={showInvite}
 *     onClose={() => setShowInvite(false)}
 *   />
 */

import { useState } from 'react'
import { Button, Input, Alert, Modal } from '../ui'
import { authService } from '../../services/AuthService'

interface InviteModalProps {
  resourceType: string
  resourceId: number
  isOpen: boolean
  onClose: () => void
}

export function InviteModal({ resourceType, resourceId, isOpen, onClose }: InviteModalProps) {
  const [inviteCode, setInviteCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  // Accept invite state
  const [joinCode, setJoinCode] = useState('')
  const [joining, setJoining] = useState(false)
  const [joinSuccess, setJoinSuccess] = useState(false)

  const handleCreateInvite = async () => {
    setLoading(true)
    setError('')
    try {
      const invite = await authService.createInvite(resourceType, resourceId)
      setInviteCode(invite.code)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create invite')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(inviteCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleJoin = async () => {
    if (!joinCode.trim()) return
    setJoining(true)
    setError('')
    try {
      await authService.acceptInvite(joinCode.trim())
      setJoinSuccess(true)
      setTimeout(() => { onClose(); setJoinSuccess(false); setJoinCode('') }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid invite code')
    } finally {
      setJoining(false)
    }
  }

  const handleClose = () => {
    setInviteCode('')
    setError('')
    setCopied(false)
    setJoinCode('')
    setJoinSuccess(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Invite & Join">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {error && <Alert variant="error">{error}</Alert>}

        {/* Create Invite Section */}
        <div>
          <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-2)', color: 'var(--text-primary)' }}>
            Create Invite Link
          </h4>
          {inviteCode ? (
            <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
              <Input value={inviteCode} readOnly style={{ flex: 1, fontFamily: 'monospace', fontSize: 'var(--text-sm)' }} />
              <Button size="sm" variant={copied ? 'primary' : 'secondary'} onClick={handleCopy}>
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </div>
          ) : (
            <Button variant="primary" onClick={handleCreateInvite} loading={loading} fullWidth>
              Generate Invite Code
            </Button>
          )}
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-1)', margin: 'var(--space-1) 0 0' }}>
            Share this code with others so they can join.
          </p>
        </div>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border-primary)' }} />
          <span>or</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border-primary)' }} />
        </div>

        {/* Join Section */}
        <div>
          <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-2)', color: 'var(--text-primary)' }}>
            Join with Code
          </h4>
          {joinSuccess ? (
            <Alert variant="success">Joined successfully!</Alert>
          ) : (
            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              <Input
                value={joinCode}
                onChange={e => setJoinCode(e.target.value)}
                placeholder="Paste invite code"
                style={{ flex: 1 }}
              />
              <Button variant="primary" onClick={handleJoin} loading={joining} disabled={!joinCode.trim()}>
                Join
              </Button>
            </div>
          )}
        </div>
      </div>
    </Modal>
  )
}
