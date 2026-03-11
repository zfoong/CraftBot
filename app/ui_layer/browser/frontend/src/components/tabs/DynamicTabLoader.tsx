import React, { useEffect, lazy, Suspense } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useDynamicTabs } from '../../hooks/useDynamicTabs'
import { DynamicTabType } from '../../types/dynamicTabs'
import styles from './DynamicTab.module.css'

const VALID_TYPES: DynamicTabType[] = ['code', 'stock', 'planner', 'custom']

const CodeTab = lazy(() => import('../tabs/CodeTab').then(m => ({ default: m.CodeTab })))
const StockTab = lazy(() => import('../tabs/StockTab').then(m => ({ default: m.StockTab })))
const PlannerTab = lazy(() => import('../tabs/PlannerTab').then(m => ({ default: m.PlannerTab })))
const CustomTab = lazy(() => import('../tabs/CustomTab').then(m => ({ default: m.CustomTab })))

const TAB_COMPONENTS: Record<DynamicTabType, React.LazyExoticComponent<React.ComponentType<{ tabId: string }>>> = {
  code: CodeTab,
  stock: StockTab,
  planner: PlannerTab,
  custom: CustomTab,
}

/**
 * Handles URL-based tab restoration.
 * When navigating to /dynamic/:type/:id and the tab doesn't exist in state,
 * this component auto-creates it. If the tab already exists (race with route
 * matching), renders the tab component directly instead of showing a fallback.
 */
export function DynamicTabLoader() {
  const { type, id } = useParams<{ type: string; id: string }>()
  const { tabs, createTab } = useDynamicTabs()
  const navigate = useNavigate()

  // Check if this tab already exists (race with route matching)
  const existingTab = tabs.find(t => t.path === `/dynamic/${type}/${id}`)

  useEffect(() => {
    if (!type || !id) {
      navigate('/', { replace: true })
      return
    }

    // Tab already exists — no action needed, we render it directly below
    if (existingTab) return

    // Validate tab type
    if (!VALID_TYPES.includes(type as DynamicTabType)) {
      navigate('/', { replace: true })
      return
    }

    // Create the tab and navigate to it
    const tab = createTab(type as DynamicTabType)
    navigate(tab.path, { replace: true })
  }, [type, id, existingTab, createTab, navigate])

  // If tab exists, render its component directly (handles the race condition)
  if (existingTab) {
    const Component = TAB_COMPONENTS[existingTab.type] ?? CustomTab
    return (
      <Suspense fallback={<DynamicTabFallback />}>
        <Component tabId={existingTab.id} />
      </Suspense>
    )
  }

  return <DynamicTabFallback />
}

/**
 * Loading fallback shown while lazy tab components load.
 */
export function DynamicTabFallback() {
  return (
    <div className={styles.tabContainer}>
      <div className={styles.placeholder}>
        <p>Loading...</p>
      </div>
    </div>
  )
}
