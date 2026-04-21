/**
 * Auth Provider — React context for authentication state.
 *
 * Copy this file into your project's frontend/components/auth/ directory.
 *
 * Usage in App.tsx:
 *   import { AuthProvider, useAuth } from './components/auth/AuthProvider'
 *
 *   function App() {
 *     return (
 *       <AuthProvider>
 *         <AppContent />
 *       </AuthProvider>
 *     )
 *   }
 *
 *   function AppContent() {
 *     const { user, isAuthenticated, logout } = useAuth()
 *     if (!isAuthenticated) return <LoginPage />
 *     return <MainView />
 *   }
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import type { AuthUser, AuthState } from '../../auth_types'
import { authService } from '../../services/AuthService'

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: authService.getToken(),
    isAuthenticated: false,
    loading: true,
  })

  // Validate existing token on mount
  useEffect(() => {
    const validate = async () => {
      const user = await authService.getMe()
      setState({
        user,
        token: authService.getToken(),
        isAuthenticated: !!user,
        loading: false,
      })
    }
    validate()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { user, token } = await authService.login(email, password)
    setState({ user, token, isAuthenticated: true, loading: false })
  }, [])

  const register = useCallback(async (email: string, username: string, password: string) => {
    const { user, token } = await authService.register(email, username, password)
    setState({ user, token, isAuthenticated: true, loading: false })
  }, [])

  const logout = useCallback(() => {
    authService.logout()
    setState({ user: null, token: null, isAuthenticated: false, loading: false })
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
