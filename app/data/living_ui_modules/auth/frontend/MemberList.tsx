/**
 * Member List — shows members of a resource with role badges and remove button.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 *
 * Usage:
 *   import { MemberList } from './components/auth/MemberList'
 *   <MemberList resourceType="project" resourceId={project.id} />
 */

import { useState, useEffect, useCallback } from 'react'
import { Button, Badge, Alert } from '../ui'
import { useAuth } from './AuthProvider'
import { authService } from '../../services/AuthService'
import type { MembershipInfo } from '../../auth_types'

interface MemberListProps {
  resourceType: string
  resourceId: number
  currentUserRole?: string  // caller's role in this resource (for showing remove buttons)
}

export function MemberList({ resourceType, resourceId, currentUserRole }: MemberListProps) {
  const { user } = useAuth()
  const [members, setMembers] = useState<MembershipInfo[]>([])
  const [error, setError] = useState('')
  const [removing, setRemoving] = useState<number | null>(null)

  const canManage = currentUserRole === 'owner' || currentUserRole === 'admin' || user?.role === 'admin'

  const loadMembers = useCallback(async () => {
    try {
      const data = await authService.getMembers(resourceType, resourceId)
      setMembers(data)
    } catch {
      setError('Failed to load members')
    }
  }, [resourceType, resourceId])

  useEffect(() => { loadMembers() }, [loadMembers])

  const handleRemove = async (userId: number) => {
    setRemoving(userId)
    try {
      await authService.removeMember(resourceType, resourceId, userId)
      setMembers(prev => prev.filter(m => m.userId !== userId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove member')
    } finally {
      setRemoving(null)
    }
  }

  if (error) return <Alert variant="error">{error}</Alert>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      {members.length === 0 ? (
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', margin: 0 }}>No members yet</p>
      ) : (
        members.map(member => (
          <div
            key={member.id}
            style={{
              display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
              padding: 'var(--space-2) var(--space-3)',
              background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)',
            }}
          >
            {/* Avatar */}
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'var(--color-primary)', color: 'var(--color-white)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 'var(--text-xs)', fontWeight: 'var(--font-weight-semibold)',
              flexShrink: 0,
            }}>
              {member.user?.username?.charAt(0).toUpperCase() || '?'}
            </div>

            {/* Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-medium)', color: 'var(--text-primary)' }}>
                {member.user?.username || `User #${member.userId}`}
                {member.userId === user?.id && (
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginLeft: 'var(--space-1)' }}>(you)</span>
                )}
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                {member.user?.email}
              </div>
            </div>

            {/* Role badge */}
            <Badge variant={member.role === 'owner' ? 'primary' : member.role === 'admin' ? 'warning' : 'default'}>
              {member.role}
            </Badge>

            {/* Remove button */}
            {canManage && member.role !== 'owner' && member.userId !== user?.id && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleRemove(member.userId)}
                loading={removing === member.userId}
                style={{ color: 'var(--color-error)', padding: 'var(--space-1)' }}
              >
                Remove
              </Button>
            )}
          </div>
        ))
      )}
    </div>
  )
}
