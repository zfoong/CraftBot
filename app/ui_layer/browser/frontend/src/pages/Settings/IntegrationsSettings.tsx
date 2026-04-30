import React, { useState, useEffect } from 'react'
import * as LucideIcons from 'lucide-react'
import {
  Globe,
  Package,
  AlertTriangle,
  Loader2,
  Plus,
  RotateCcw,
  X,
  Power,
  Wrench,
} from 'lucide-react'
import { Button, Badge, ConfirmModal } from '../../components/ui'
import { useToast } from '../../contexts/ToastContext'
import { useConfirmModal } from '../../hooks'
import styles from './SettingsPage.module.css'
import { useSettingsWebSocket } from './useSettingsWebSocket'

// Types
interface IntegrationField {
  key: string
  label: string
  placeholder: string
  password: boolean
}

interface IntegrationAccount {
  display: string
  id: string
}

interface Integration {
  id: string
  name: string
  description: string
  auth_type: 'oauth' | 'token' | 'both' | 'interactive' | 'token_with_interactive'
  connected: boolean
  accounts: IntegrationAccount[]
  fields: IntegrationField[]
  icon?: string  // Lucide icon name supplied by the backend handler
}

// Integration icon component. Lookup order:
//   1. Hand-crafted brand SVG keyed by integration id (defined below)
//   2. Lucide icon by name from the backend's ``icon`` field
//   3. Generic globe fallback
const IntegrationIcon = ({ id, icon, size = 20 }: { id: string; icon?: string; size?: number }) => {
  const icons: Record<string, React.ReactNode> = {
    google: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
      </svg>
    ),
    slack: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313z" fill="#E01E5A"/>
        <path d="M8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312z" fill="#36C5F0"/>
        <path d="M18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zm-1.27 0a2.528 2.528 0 0 1-2.522 2.521 2.528 2.528 0 0 1-2.52-2.521V2.522A2.528 2.528 0 0 1 15.165 0a2.528 2.528 0 0 1 2.521 2.522v6.312z" fill="#2EB67D"/>
        <path d="M15.165 18.956a2.528 2.528 0 0 1 2.521 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zm0-1.27a2.527 2.527 0 0 1-2.52-2.522 2.527 2.527 0 0 1 2.52-2.52h6.313A2.528 2.528 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.521h-6.313z" fill="#ECB22E"/>
      </svg>
    ),
    notion: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
        <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.98-.7-2.055-.606L3.01 2.612c-.466.046-.56.28-.373.466l1.822 1.13zm.793 3.08v13.904c0 .746.373 1.026 1.213.98l14.523-.84c.839-.046.932-.559.932-1.166V6.382c0-.606-.233-.932-.746-.886l-15.176.886c-.56.047-.746.327-.746.886zm14.337.699c.094.42 0 .84-.42.886l-.699.14v10.264c-.607.327-1.166.513-1.632.513-.746 0-.933-.234-1.493-.933l-4.574-7.186v6.953l1.446.327s0 .84-1.166.84l-3.22.186c-.093-.187 0-.653.326-.746l.84-.233V9.854L7.828 9.62c-.094-.42.14-1.026.793-1.073l3.453-.234 4.76 7.28V9.107l-1.213-.14c-.093-.513.28-.886.746-.932l3.222-.186z" fillRule="evenodd"/>
      </svg>
    ),
    linkedin: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="#0A66C2">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
      </svg>
    ),
    zoom: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="#2D8CFF">
        <path d="M24 12c0 6.627-5.373 12-12 12S0 18.627 0 12 5.373 0 12 0s12 5.373 12 12zm-5.2-3.2v4.8c0 .88-.72 1.6-1.6 1.6H8.4c-.88 0-1.6-.72-1.6-1.6V8.8c0-.88.72-1.6 1.6-1.6h8.8c.88 0 1.6.72 1.6 1.6zm-3.2 4.8V10.4l2.4-1.6v6.4l-2.4-1.6z"/>
      </svg>
    ),
    discord: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="#5865F2">
        <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"/>
      </svg>
    ),
    telegram: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="#26A5E4">
        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
      </svg>
    ),
    whatsapp: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="#25D366">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
      </svg>
    ),
    whatsapp_business: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="#25D366">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
      </svg>
    ),
    twitter: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
      </svg>
    ),
    jira: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="#0052CC">
        <path d="M11.571 11.513H0a5.218 5.218 0 0 0 5.232 5.215h2.13v2.057A5.215 5.215 0 0 0 12.575 24V12.518a1.005 1.005 0 0 0-1.005-1.005z"/>
        <path d="M6.348 6.349H-5.224a5.218 5.218 0 0 0 5.232 5.215h2.13v2.057a5.215 5.215 0 0 0 5.215 5.215V7.354a1.005 1.005 0 0 0-1.005-1.005z" transform="translate(5.224)"/>
        <path d="M11.571 0H0a5.218 5.218 0 0 0 5.232 5.215h2.13v2.057A5.215 5.215 0 0 0 12.575 12.487V1.005A1.005 1.005 0 0 0 11.571 0z" transform="translate(.348 1.164)"/>
      </svg>
    ),
    github: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
      </svg>
    ),
    recall: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        <circle cx="12" cy="10" r="3"/>
        <path d="M12 14c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg>
    ),
  }
  // 1. Brand SVG keyed by the backend's ``icon`` name (e.g. "github",
  //    "google", "notion") — the integration file owns this declaration.
  if (icon && icons[icon]) {
    return <span className={styles.integrationIconSvg}>{icons[icon]}</span>
  }
  // 2. Backwards-compat: legacy lookup by integration id, in case any
  //    integration hasn't declared ``icon`` yet.
  if (icons[id]) {
    return <span className={styles.integrationIconSvg}>{icons[id]}</span>
  }
  // 3. Lucide fallback for non-brand icons (e.g. "Inbox", "Send").
  if (icon) {
    const lucideMap = LucideIcons as unknown as Record<string, React.ComponentType<{ size?: number }>>
    const LucideIcon = lucideMap[icon]
    if (LucideIcon) {
      return <span className={styles.integrationIconSvg}><LucideIcon size={size} /></span>
    }
  }
  // 4. Generic fallback
  return <span className={styles.integrationIconSvg}><Globe size={size} /></span>
}

export function IntegrationsSettings() {
  const { send, onMessage, isConnected } = useSettingsWebSocket()
  const { showToast } = useToast()

  // State
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [totalIntegrations, setTotalIntegrations] = useState(0)
  const [connectedCount, setConnectedCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  // Search
  const [searchQuery, setSearchQuery] = useState('')

  // Reload state
  const [isReloading, setIsReloading] = useState(false)
  const isReloadingRef = React.useRef(false)

  // Connect modal state
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [credentials, setCredentials] = useState<Record<string, string>>({})
  const [connectError, setConnectError] = useState('')
  const [isConnecting, setIsConnecting] = useState(false)

  // Manage modal state
  const [showManageModal, setShowManageModal] = useState(false)
  const [managingIntegration, setManagingIntegration] = useState<Integration | null>(null)

  // WhatsApp QR code state
  const [whatsappQrCode, setWhatsappQrCode] = useState<string | null>(null)
  const [whatsappSessionId, setWhatsappSessionId] = useState<string | null>(null)
  const [whatsappStatus, setWhatsappStatus] = useState<'idle' | 'loading' | 'qr_ready' | 'connected' | 'error'>('idle')
  const [whatsappError, setWhatsappError] = useState<string | null>(null)
  const whatsappPollRef = React.useRef<ReturnType<typeof setInterval> | null>(null)

  // Confirm modal
  const { modalProps: confirmModalProps, confirm } = useConfirmModal()

  // Load data when connected
  useEffect(() => {
    if (!isConnected) return

    const cleanups = [
      onMessage('integration_list', (data: unknown) => {
        const d = data as { success: boolean; integrations?: Integration[]; total?: number; connected?: number; error?: string }
        const wasReloading = isReloadingRef.current
        setIsLoading(false)
        setIsReloading(false)
        isReloadingRef.current = false
        if (d.success && d.integrations) {
          setIntegrations(d.integrations)
          setTotalIntegrations(d.total ?? d.integrations.length)
          setConnectedCount(d.connected ?? d.integrations.filter(i => i.connected).length)
          if (wasReloading) {
            showToast('success', 'Integrations reloaded')
          }
        } else if (d.error) {
          showToast('error', d.error)
        }
      }),
      onMessage('integration_connect_result', (data: unknown) => {
        const d = data as { success: boolean; message?: string; error?: string; id?: string }
        setIsConnecting(false)
        if (d.success) {
          showToast('success', d.message || 'Connected successfully')
          setShowConnectModal(false)
          setCredentials({})
          setConnectError('')
        } else {
          setConnectError(d.error || d.message || 'Connection failed')
        }
      }),
      onMessage('integration_disconnect_result', (data: unknown) => {
        const d = data as { success: boolean; message?: string; error?: string }
        if (d.success) {
          showToast('success', d.message || 'Disconnected successfully')
          setShowManageModal(false)
          setManagingIntegration(null)
        } else {
          showToast('error', d.error || 'Failed to disconnect')
        }
      }),
      onMessage('integration_info', (data: unknown) => {
        const d = data as { success: boolean; integration?: Integration; error?: string }
        if (d.success && d.integration) {
          setManagingIntegration(d.integration)
          setShowManageModal(true)
        } else {
          showToast('error', d.error || 'Failed to get integration info')
        }
      }),
      // WhatsApp QR code handlers
      onMessage('whatsapp_qr_result', (data: unknown) => {
        const d = data as { success: boolean; session_id?: string; qr_code?: string; status?: string; message?: string }
        if (d.success && d.qr_code) {
          setWhatsappQrCode(d.qr_code)
          setWhatsappSessionId(d.session_id || null)
          setWhatsappStatus('qr_ready')
          setWhatsappError(null)
        } else {
          setWhatsappStatus('error')
          setWhatsappError(d.message || 'Failed to get QR code')
        }
      }),
      onMessage('whatsapp_status_result', (data: unknown) => {
        const d = data as { success: boolean; status?: string; connected?: boolean; message?: string }
        if (d.connected) {
          setWhatsappStatus('connected')
          setShowConnectModal(false)
          showToast('success', d.message || 'WhatsApp connected successfully')
          if (whatsappPollRef.current) {
            clearInterval(whatsappPollRef.current)
            whatsappPollRef.current = null
          }
          setWhatsappQrCode(null)
          setWhatsappSessionId(null)
          setWhatsappStatus('idle')
        } else if (d.status === 'error' || d.status === 'disconnected') {
          setWhatsappStatus('error')
          setWhatsappError(d.message || 'Session failed')
          if (whatsappPollRef.current) {
            clearInterval(whatsappPollRef.current)
            whatsappPollRef.current = null
          }
        }
      }),
      onMessage('whatsapp_cancel_result', (_data: unknown) => {
        setWhatsappQrCode(null)
        setWhatsappSessionId(null)
        setWhatsappStatus('idle')
        setWhatsappError(null)
      }),
    ]

    send('integration_list')

    return () => cleanups.forEach(c => c())
  }, [isConnected, send, onMessage])

  // Start WhatsApp polling when QR is ready
  useEffect(() => {
    if (whatsappStatus === 'qr_ready' && whatsappSessionId) {
      startWhatsAppPolling(whatsappSessionId)
    }
    return () => {
      if (whatsappPollRef.current) {
        clearInterval(whatsappPollRef.current)
        whatsappPollRef.current = null
      }
    }
  }, [whatsappStatus, whatsappSessionId])

  // Handlers
  const handleReload = () => {
    setIsReloading(true)
    isReloadingRef.current = true
    send('integration_list')
  }

  const handleOpenConnect = (integration: Integration) => {
    setSelectedIntegration(integration)
    setCredentials({})
    setConnectError('')
    setShowConnectModal(true)

    if (integration.auth_type === 'interactive' && integration.id === 'whatsapp_web') {
      handleStartWhatsAppQR()
    }
  }

  const handleStartWhatsAppQR = () => {
    setWhatsappStatus('loading')
    setWhatsappQrCode(null)
    setWhatsappSessionId(null)
    setWhatsappError(null)
    send('whatsapp_start_qr')
  }

  const startWhatsAppPolling = (sessionId: string) => {
    if (whatsappPollRef.current) {
      clearInterval(whatsappPollRef.current)
    }
    whatsappPollRef.current = setInterval(() => {
      send('whatsapp_check_status', { session_id: sessionId })
    }, 2000)
  }

  const handleCancelWhatsApp = () => {
    if (whatsappPollRef.current) {
      clearInterval(whatsappPollRef.current)
      whatsappPollRef.current = null
    }
    if (whatsappSessionId) {
      send('whatsapp_cancel', { session_id: whatsappSessionId })
    }
    setWhatsappQrCode(null)
    setWhatsappSessionId(null)
    setWhatsappStatus('idle')
    setWhatsappError(null)
    setShowConnectModal(false)
  }

  const handleOpenManage = (integration: Integration) => {
    send('integration_info', { id: integration.id })
  }

  const handleConnectToken = () => {
    if (!selectedIntegration) return
    setIsConnecting(true)
    setConnectError('')
    send('integration_connect_token', {
      id: selectedIntegration.id,
      credentials,
    })
  }

  const handleConnectOAuth = () => {
    if (!selectedIntegration) return
    setIsConnecting(true)
    setConnectError('')
    send('integration_connect_oauth', { id: selectedIntegration.id })
  }

  const handleConnectInteractive = () => {
    if (!selectedIntegration) return
    setIsConnecting(true)
    setConnectError('')
    send('integration_connect_interactive', { id: selectedIntegration.id })
  }

  const handleDisconnect = (accountId?: string) => {
    if (!managingIntegration) return
    send('integration_disconnect', {
      id: managingIntegration.id,
      account_id: accountId,
    })
  }

  const handleAddAnother = () => {
    if (!managingIntegration) return
    setShowManageModal(false)
    handleOpenConnect(managingIntegration)
  }

  const filteredIntegrations = integrations
    .filter(integration => {
      if (!searchQuery) return true
      const query = searchQuery.toLowerCase()
      return integration.name.toLowerCase().includes(query) ||
        integration.description.toLowerCase().includes(query)
    })
    .sort((a, b) => a.name.localeCompare(b.name))

  if (isLoading) {
    return (
      <div className={styles.settingsSection}>
        <div className={styles.loadingState}>
          <Loader2 className={styles.spinner} />
          <span>Loading integrations...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.settingsSection}>
      {/* Header */}
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTitleRow}>
          <h3>External Integrations</h3>
          <Badge variant="default">{connectedCount}/{totalIntegrations} connected</Badge>
        </div>
        <p>Connect to external services and tools</p>
      </div>

      {/* Toolbar */}
      <div className={styles.integrationsToolbar}>
        <div className={styles.integrationsSearch}>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Search integrations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleReload}
          disabled={isReloading}
          icon={<RotateCcw size={14} className={isReloading ? styles.spinning : ''} />}
        >
          Reload
        </Button>
      </div>

      {/* Integrations list */}
      <div className={styles.integrationsList}>
        {filteredIntegrations.length === 0 ? (
          <div className={styles.emptyState}>
            <Package size={24} />
            <span>
              {searchQuery ? 'No integrations match your search' : 'No integrations available'}
            </span>
          </div>
        ) : (
          filteredIntegrations.map(integration => (
            <div
              key={integration.id}
              className={`${styles.integrationItem} ${!integration.connected ? styles.integrationItemDisabled : ''}`}
            >
              <div className={styles.integrationItemIcon}>
                <IntegrationIcon id={integration.id} icon={integration.icon} size={24} />
              </div>
              <div className={styles.integrationItemMain}>
                <div className={styles.integrationItemHeader}>
                  <span className={styles.integrationItemName}>{integration.name}</span>
                  <Badge variant={integration.connected ? 'success' : 'default'}>
                    {integration.connected ? 'Connected' : 'Not connected'}
                  </Badge>
                  {integration.connected && integration.accounts.length > 0 && (
                    <Badge variant="info">{integration.accounts.length} account{integration.accounts.length > 1 ? 's' : ''}</Badge>
                  )}
                </div>
                <p className={styles.integrationItemDesc}>{integration.description}</p>
              </div>
              <div className={styles.integrationItemActions}>
                {integration.connected ? (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenManage(integration)}
                      icon={<Wrench size={14} />}
                      title="Manage accounts"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        confirm({
                          title: 'Disconnect Integration',
                          message: `Disconnect all accounts from ${integration.name}?`,
                          confirmText: 'Disconnect',
                          variant: 'danger',
                        }, () => {
                          send('integration_disconnect', { id: integration.id })
                        })
                      }}
                      icon={<Power size={14} />}
                      title="Disconnect"
                    />
                  </>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleOpenConnect(integration)}
                    icon={<Plus size={14} />}
                  >
                    Connect
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Connect Modal */}
      {showConnectModal && selectedIntegration && (
        <div className={styles.modalOverlay} onClick={() => setShowConnectModal(false)}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>Connect {selectedIntegration.name}</h3>
              <button className={styles.modalClose} onClick={() => setShowConnectModal(false)}>
                <X size={18} />
              </button>
            </div>
            <div className={styles.modalBody}>
              {/* OAuth-only integrations */}
              {selectedIntegration.auth_type === 'oauth' && (
                <div className={styles.connectForm}>
                  <p className={styles.connectDesc}>
                    Click the button below to sign in with {selectedIntegration.name}.
                    A browser window will open for authentication.
                  </p>
                  {connectError && (
                    <div className={styles.formError}>{connectError}</div>
                  )}
                  <Button
                    variant="primary"
                    onClick={handleConnectOAuth}
                    disabled={isConnecting}
                  >
                    {isConnecting ? (
                      <>
                        <Loader2 size={16} className={styles.spinning} />
                        Connecting...
                      </>
                    ) : (
                      <>Sign in with {selectedIntegration.name}</>
                    )}
                  </Button>
                </div>
              )}

              {/* Token-only integrations */}
              {selectedIntegration.auth_type === 'token' && (
                <div className={styles.connectForm}>
                  {selectedIntegration.fields.map(field => (
                    <div key={field.key} className={styles.formGroup}>
                      <label className={styles.formLabel}>{field.label}</label>
                      <input
                        type={field.password ? 'password' : 'text'}
                        className={styles.formInput}
                        placeholder={field.placeholder}
                        value={credentials[field.key] || ''}
                        onChange={(e) => setCredentials(prev => ({
                          ...prev,
                          [field.key]: e.target.value
                        }))}
                      />
                    </div>
                  ))}
                  {connectError && (
                    <div className={styles.formError}>{connectError}</div>
                  )}
                  <Button
                    variant="primary"
                    onClick={handleConnectToken}
                    disabled={isConnecting}
                  >
                    {isConnecting ? (
                      <>
                        <Loader2 size={16} className={styles.spinning} />
                        Connecting...
                      </>
                    ) : (
                      'Connect'
                    )}
                  </Button>
                </div>
              )}

              {/* Both OAuth and Token integrations */}
              {selectedIntegration.auth_type === 'both' && (
                <div className={styles.connectForm}>
                  {selectedIntegration.fields.map(field => (
                    <div key={field.key} className={styles.formGroup}>
                      <label className={styles.formLabel}>{field.label}</label>
                      <input
                        type={field.password ? 'password' : 'text'}
                        className={styles.formInput}
                        placeholder={field.placeholder}
                        value={credentials[field.key] || ''}
                        onChange={(e) => setCredentials(prev => ({
                          ...prev,
                          [field.key]: e.target.value
                        }))}
                      />
                    </div>
                  ))}
                  {connectError && (
                    <div className={styles.formError}>{connectError}</div>
                  )}
                  <Button
                    variant="primary"
                    onClick={handleConnectToken}
                    disabled={isConnecting}
                  >
                    {isConnecting ? (
                      <>
                        <Loader2 size={16} className={styles.spinning} />
                        Connecting...
                      </>
                    ) : (
                      'Connect with Token'
                    )}
                  </Button>
                  <div className={styles.connectFormDivider}>or</div>
                  <Button
                    variant="secondary"
                    onClick={handleConnectOAuth}
                    disabled={isConnecting}
                  >
                    Use OAuth Instead
                  </Button>
                </div>
              )}

              {/* Token + Interactive QR integrations (Telegram) */}
              {selectedIntegration.auth_type === 'token_with_interactive' && (
                <div className={styles.connectForm}>
                  {selectedIntegration.fields.map(field => (
                    <div key={field.key} className={styles.formGroup}>
                      <label className={styles.formLabel}>{field.label}</label>
                      <input
                        type={field.password ? 'password' : 'text'}
                        className={styles.formInput}
                        placeholder={field.placeholder}
                        value={credentials[field.key] || ''}
                        onChange={(e) => setCredentials(prev => ({
                          ...prev,
                          [field.key]: e.target.value
                        }))}
                      />
                    </div>
                  ))}
                  {connectError && (
                    <div className={styles.formError}>{connectError}</div>
                  )}
                  <Button
                    variant="primary"
                    onClick={handleConnectToken}
                    disabled={isConnecting}
                  >
                    {isConnecting ? (
                      <>
                        <Loader2 size={16} className={styles.spinning} />
                        Connecting...
                      </>
                    ) : (
                      'Connect Bot'
                    )}
                  </Button>
                  <div className={styles.connectFormDivider}>or</div>
                  <p className={styles.connectDesc}>
                    Connect a personal account via QR code. A QR code window will open separately on your machine.
                  </p>
                  <Button
                    variant="secondary"
                    onClick={handleConnectInteractive}
                    disabled={isConnecting}
                  >
                    {isConnecting ? (
                      <>
                        <Loader2 size={16} className={styles.spinning} />
                        Waiting for QR scan...
                      </>
                    ) : (
                      'Connect User Account (QR Code)'
                    )}
                  </Button>
                </div>
              )}

              {/* Interactive integrations: generic dispatcher for non-WhatsApp */}
              {selectedIntegration.auth_type === 'interactive' && selectedIntegration.id !== 'whatsapp_web' && (
                <div className={styles.connectForm}>
                  <p className={styles.connectDesc}>
                    {selectedIntegration.description}
                  </p>
                  <Button
                    variant="primary"
                    onClick={handleConnectInteractive}
                    disabled={isConnecting}
                  >
                    {isConnecting ? (
                      <><Loader2 size={16} className={styles.spinning} /> Connecting...</>
                    ) : (
                      <>Connect {selectedIntegration.name}</>
                    )}
                  </Button>
                  {connectError && (
                    <div className={styles.connectError}>{connectError}</div>
                  )}
                </div>
              )}

              {/* WhatsApp Web QR-specific interactive flow */}
              {selectedIntegration.auth_type === 'interactive' && selectedIntegration.id === 'whatsapp_web' && (
                <div className={styles.connectForm}>
                  {whatsappStatus === 'loading' && (
                    <div className={styles.whatsappLoading}>
                      <Loader2 size={32} className={styles.spinning} />
                      <p>Starting WhatsApp Web session...</p>
                    </div>
                  )}

                  {whatsappStatus === 'qr_ready' && whatsappQrCode && (
                    <div className={styles.whatsappQrContainer}>
                      <p className={styles.connectDesc}>
                        Scan this QR code with your WhatsApp mobile app to connect.
                      </p>
                      <div className={styles.whatsappQrCode}>
                        <img src={whatsappQrCode} alt="WhatsApp QR Code" />
                      </div>
                      <p className={styles.whatsappQrHint}>
                        Open WhatsApp &rarr; Settings &rarr; Linked Devices &rarr; Link a Device
                      </p>
                    </div>
                  )}

                  {whatsappStatus === 'error' && (
                    <div className={styles.whatsappError}>
                      <AlertTriangle size={24} />
                      <p>{whatsappError || 'Failed to connect to WhatsApp'}</p>
                      <Button variant="primary" onClick={handleStartWhatsAppQR}>
                        Try Again
                      </Button>
                    </div>
                  )}

                  {whatsappStatus === 'idle' && (
                    <div className={styles.whatsappIdle}>
                      <p className={styles.connectDesc}>
                        Click the button below to generate a QR code for WhatsApp Web.
                      </p>
                      <Button variant="primary" onClick={handleStartWhatsAppQR}>
                        Generate QR Code
                      </Button>
                    </div>
                  )}

                  {(whatsappStatus === 'loading' || whatsappStatus === 'qr_ready') && (
                    <Button variant="secondary" onClick={handleCancelWhatsApp}>
                      Cancel
                    </Button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Manage Modal */}
      {showManageModal && managingIntegration && (
        <div className={styles.modalOverlay} onClick={() => setShowManageModal(false)}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>Manage {managingIntegration.name}</h3>
              <button className={styles.modalClose} onClick={() => setShowManageModal(false)}>
                <X size={18} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <h4 className={styles.manageSubtitle}>Connected Accounts</h4>
              {managingIntegration.accounts.length === 0 ? (
                <p className={styles.noAccounts}>No accounts connected</p>
              ) : (
                <div className={styles.accountsList}>
                  {managingIntegration.accounts.map(account => (
                    <div key={account.id} className={styles.accountItem}>
                      <span className={styles.accountName}>{account.display}</span>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDisconnect(account.id)}
                      >
                        Disconnect
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <div className={styles.modalActions}>
                <Button variant="secondary" onClick={handleAddAnother} icon={<Plus size={14} />}>
                  Add Another Account
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal {...confirmModalProps} />
    </div>
  )
}
