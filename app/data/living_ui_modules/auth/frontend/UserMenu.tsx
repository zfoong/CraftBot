/**
 * User Menu — dropdown showing current user with logout option.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 * Place in your app's header/nav bar.
 *
 * Usage:
 *   import { UserMenu } from './components/auth/UserMenu'
 *   <header>
 *     <h1>My App</h1>
 *     <UserMenu />
 *   </header>
 */

import { useState, useRef, useEffect } from 'react'
import { useAuth } from './AuthProvider'
import { Badge } from '../ui'

export function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (!user) return null

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
          background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-md)', padding: 'var(--space-1) var(--space-3)',
          cursor: 'pointer', fontSize: 'var(--text-sm)', color: 'var(--text-primary)',
          fontFamily: 'inherit',
        }}
      >
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: 'var(--color-primary)', color: 'var(--color-white)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 'var(--text-xs)', fontWeight: 'var(--font-weight-semibold)',
        }}>
          {user.username.charAt(0).toUpperCase()}
        </div>
        <span>{user.username}</span>
      </button>

      {open && (
        <div style={{
          position: 'absolute', right: 0, top: '100%', marginTop: 'var(--space-1)',
          background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
          minWidth: 200, zIndex: 50, overflow: 'hidden',
        }}>
          <div style={{
            padding: 'var(--space-3) var(--space-4)',
            borderBottom: '1px solid var(--border-primary)',
          }}>
            <div style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-medium)', color: 'var(--text-primary)' }}>
              {user.username}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 2 }}>
              {user.email}
            </div>
            <Badge variant={user.role === 'admin' ? 'primary' : 'default'} style={{ marginTop: 'var(--space-1)' }}>
              {user.role}
            </Badge>
          </div>
          <button
            onClick={() => { logout(); setOpen(false) }}
            style={{
              display: 'block', width: '100%', textAlign: 'left',
              padding: 'var(--space-2) var(--space-4)',
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 'var(--text-sm)', color: 'var(--color-error)',
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-tertiary)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'none')}
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}
