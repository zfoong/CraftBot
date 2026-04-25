/**
 * Auth TypeScript interfaces.
 *
 * Copy this file into your project's frontend/ directory.
 */

export interface AuthUser {
  id: number
  email: string
  username: string
  role: 'admin' | 'member'
  isActive: boolean
  createdAt: string
}

export interface AuthState {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
}

export interface LoginResponse {
  user: AuthUser
  token: string
}

export interface MembershipInfo {
  id: number
  userId: number
  resourceType: string
  resourceId: number
  role: string
  joinedAt: string
  user: AuthUser | null
}

export interface InviteInfo {
  id: number
  code: string
  resourceType: string
  resourceId: number
  defaultRole: string
  isActive: boolean
  maxUses: number | null
  useCount: number
  createdAt: string
}
