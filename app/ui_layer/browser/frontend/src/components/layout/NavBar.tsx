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

  // Create dynamic nav items for Living UIs
  const livingUINavItems: NavItem[] = livingUIProjects.map(project => ({
    id: `living-ui-${project.id}`,
    label: project.name,
    icon: project.status === 'creating' ? <Loader2 size={16} className={styles.spinner} /> : <Box size={16} />,
    path: `/living-ui/${project.id}`,
  }))

  // Combine static and Living UI nav items
  const allNavItems = [...staticNavItems, ...livingUINavItems]

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const handleCreateSubmit = (data: LivingUICreateRequest) => {
    createLivingUI(data)
    setShowCreateModal(false)
  }

  return (
    <>
      <nav
        className={styles.navBar}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className={styles.navItems}>
          {allNavItems.map(item => (
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
            title="Create Living UI"
          >
            <Plus size={16} />
          </button>
        </div>

      </nav>

      <CreateLivingUIModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateSubmit}
      />
    </>
  )
}
