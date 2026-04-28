/**
 * Auth Service — handles login, registration, token storage, and authenticated requests.
 *
 * Copy this file into your project's frontend/services/ directory.
 *
 * Usage:
 *   import { authService } from './services/AuthService'
 *   await authService.login('email@example.com', 'password')
 *   const user = await authService.getMe()
 *   authService.logout()
 */

import type { AuthUser, LoginResponse, MembershipInfo, InviteInfo } from '../auth_types'

const TOKEN_KEY = 'auth_token'

class AuthService {
  private backendUrl: string

  constructor() {
    this.backendUrl = (window as any).__CRAFTBOT_BACKEND_URL__ || 'http://localhost:3101'
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  }

  private setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  }

  private clearToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  }

  isAuthenticated(): boolean {
    return !!this.getToken()
  }

  /**
   * Make an authenticated fetch request. Automatically adds the Bearer token.
   */
  async authFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getToken()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return fetch(url, { ...options, headers })
  }

  async register(email: string, username: string, password: string): Promise<LoginResponse> {
    const resp = await fetch(`${this.backendUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Registration failed' }))
      throw new Error(err.detail || 'Registration failed')
    }
    const data: LoginResponse = await resp.json()
    this.setToken(data.token)
    return data
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const resp = await fetch(`${this.backendUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail || 'Invalid email or password')
    }
    const data: LoginResponse = await resp.json()
    this.setToken(data.token)
    return data
  }

  async getMe(): Promise<AuthUser | null> {
    const token = this.getToken()
    if (!token) return null
    try {
      const resp = await this.authFetch(`${this.backendUrl}/api/auth/me`)
      if (!resp.ok) {
        this.clearToken()
        return null
      }
      const data = await resp.json()
      return data.user
    } catch {
      this.clearToken()
      return null
    }
  }

  logout(): void {
    this.clearToken()
  }

  // ── Profile ──────────────────────────────────────────────────

  async updateProfile(updates: { username?: string; email?: string }): Promise<AuthUser> {
    const resp = await this.authFetch(`${this.backendUrl}/api/auth/me`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Update failed' }))
      throw new Error(err.detail || 'Update failed')
    }
    return (await resp.json()).user
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const resp = await this.authFetch(`${this.backendUrl}/api/auth/me/password`, {
      method: 'PUT',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Password change failed' }))
      throw new Error(err.detail || 'Password change failed')
    }
  }

  // ── Membership ───────────────────────────────────────────────

  async getMembers(resourceType: string, resourceId: number): Promise<MembershipInfo[]> {
    const resp = await this.authFetch(`${this.backendUrl}/api/auth/members/${resourceType}/${resourceId}`)
    if (!resp.ok) return []
    return (await resp.json()).members || []
  }

  async addMember(resourceType: string, resourceId: number, userId: number, role = 'member'): Promise<MembershipInfo> {
    const resp = await this.authFetch(`${this.backendUrl}/api/auth/members/${resourceType}/${resourceId}`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Failed to add member' }))
      throw new Error(err.detail || 'Failed to add member')
    }
    return (await resp.json()).membership
  }

  async removeMember(resourceType: string, resourceId: number, userId: number): Promise<void> {
    const resp = await this.authFetch(`${this.backendUrl}/api/auth/members/${resourceType}/${resourceId}/${userId}`, {
      method: 'DELETE',
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Failed to remove member' }))
      throw new Error(err.detail || 'Failed to remove member')
    }
  }

  // ── Invites ──────────────────────────────────────────────────

  async createInvite(resourceType: string, resourceId: number, defaultRole = 'member', maxUses?: number): Promise<InviteInfo> {
    const resp = await this.authFetch(`${this.backendUrl}/api/auth/invites`, {
      method: 'POST',
      body: JSON.stringify({ resource_type: resourceType, resource_id: resourceId, default_role: defaultRole, max_uses: maxUses }),
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Failed to create invite' }))
      throw new Error(err.detail || 'Failed to create invite')
    }
    return (await resp.json()).invite
  }

  async acceptInvite(code: string): Promise<MembershipInfo> {
    const resp = await this.authFetch(`${this.backendUrl}/api/auth/invites/${code}/accept`, {
      method: 'POST',
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Failed to accept invite' }))
      throw new Error(err.detail || 'Failed to accept invite')
    }
    return (await resp.json()).membership
  }
}

export const authService = new AuthService()
