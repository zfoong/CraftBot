import React, { ReactNode } from 'react'
import { TopBar } from './TopBar'
import { NavBar } from './NavBar'
import { useFullscreen } from '../../contexts/FullscreenContext'
import styles from './Layout.module.css'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const { isFullscreen } = useFullscreen()
  return (
    <div className={styles.layout}>
      {!isFullscreen && <TopBar />}
      {!isFullscreen && <NavBar />}
      <main className={styles.content}>
        {children}
      </main>
    </div>
  )
}
