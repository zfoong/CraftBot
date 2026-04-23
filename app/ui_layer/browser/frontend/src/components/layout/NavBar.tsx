import React, { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  MessageSquare,
  ListTodo,
  LayoutDashboard,
  FolderOpen,
  Settings,
  Plus,
  Box,
  Loader2
} from 'lucide-react'
import { useWebSocket } from '../../contexts/WebSocketContext'
import { CreateLivingUIModal } from '../ui/CreateLivingUIModal'
import type { LivingUICreateRequest } from '../../types'
import styles from './NavBar.module.css'

interface NavItem {
  id: string
  label: string
  icon: React.ReactNode
  path: string
}

const staticNavItems: NavItem[] = [
  { id: 'chat', label: 'Chat', icon: <MessageSquare size={16} />, path: '/' },
  { id: 'tasks', label: 'Tasks', icon: <ListTodo size={16} />, path: '/tasks' },
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={16} />, path: '/dashboard' },
  { id: 'workspace', label: 'Workspace', icon: <FolderOpen size={16} />, path: '/workspace' },
  { id: 'settings', label: 'Settings', icon: <Settings size={16} />, path: '/settings' },
]

export function NavBar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { livingUIProjects, createLivingUI } = useWebSocket()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const hasLivingUI = livingUIProjects.length > 0

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const isOnLivingUI = location.pathname.startsWith('/living-ui')

  const handleCreateSubmit = (data: LivingUICreateRequest) => {
    createLivingUI(data)
    setShowCreateModal(false)
  }

  return (
    <>
      <div
        className={styles.navWrapper}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Primary nav row */}
        <nav className={styles.navBar}>
          <div className={styles.navItems}>
            {staticNavItems.map(item => (
              <button
                key={item.id}
                className={`${styles.navItem} ${isActive(item.path) ? styles.active : ''}`}
                onClick={() => navigate(item.path)}
                title={item.label}
              >
                <span className={styles.icon}>{item.icon}</span>
                <span className={styles.label}>{item.label}</span>
              </button>
            ))}

            {/* Add Living UI button */}
            <button
              className={`${styles.addButton} ${isHovered ? styles.visible : ''}`}
              onClick={() => setShowCreateModal(true)}
              title="Add Living UI"
            >
              <Plus size={16} />
            </button>
          </div>
        </nav>

        {/* Secondary Living UI tab strip */}
        {hasLivingUI && (
          <div className={`${styles.livingUIStrip} ${isOnLivingUI ? styles.stripActive : ''}`}>
            <div className={styles.stripTabs}>
              {livingUIProjects.map(project => {
                const path = `/living-ui/${project.id}`
                const active = isActive(path)
                return (
                  <button
                    key={project.id}
                    className={`${styles.stripTab} ${active ? styles.stripTabActive : ''}`}
                    onClick={() => navigate(path)}
                    title={project.name}
                  >
                    <span className={styles.stripTabIcon}>
                      {project.status === 'creating'
                        ? <Loader2 size={13} className={styles.spinner} />
                        : <Box size={13} />}
                    </span>
                    <span className={styles.stripTabLabel}>{project.name}</span>
                    {project.status === 'creating' && (
                      <span className={styles.stripTabBadge}>installing</span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <CreateLivingUIModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateSubmit}
        onInstalled={(projectId) => navigate(`/living-ui/${projectId}`)}
      />
    </>
  )
}
