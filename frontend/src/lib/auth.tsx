import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { api } from './api'

interface User {
  id: string
  email: string
  username: string
  is_guest: boolean
  balance_cents: number
  balance_display: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<string | null>
  register: (email: string, username: string, password: string) => Promise<string | null>
  loginAsGuest: () => Promise<void>
  logout: () => void
  refreshBalance: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

const TOKEN_KEY = 'lc_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async (tok: string) => {
    try {
      const res = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${tok}` } })
      if (res.ok) {
        setUser(await res.json())
      } else {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUser(null)
      }
    } catch {
      setUser(null)
    }
  }, [])

  useEffect(() => {
    if (token) {
      fetchUser(token).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token, fetchUser])

  const login = async (email: string, password: string): Promise<string | null> => {
    try {
      const data = await api.post<{ user: User; token: string }>('/api/auth/login', { email, password })
      localStorage.setItem(TOKEN_KEY, data.token)
      setToken(data.token)
      setUser(data.user)
      return null
    } catch (e: any) {
      return e.message || 'Login failed'
    }
  }

  const register = async (email: string, username: string, password: string): Promise<string | null> => {
    try {
      const data = await api.post<{ user: User; token: string }>('/api/auth/register', { email, username, password })
      localStorage.setItem(TOKEN_KEY, data.token)
      setToken(data.token)
      setUser(data.user)
      return null
    } catch (e: any) {
      return e.message || 'Registration failed'
    }
  }

  const loginAsGuest = async () => {
    try {
      const data = await api.post<{ user: User; token: string }>('/api/auth/guest')
      localStorage.setItem(TOKEN_KEY, data.token)
      setToken(data.token)
      setUser(data.user)
    } catch {}
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  const refreshBalance = async () => {
    if (!token) return
    try {
      const data = await api.get<{ balance_cents: number; balance_display: string }>('/api/auth/balance')
      setUser(u => u ? { ...u, ...data } : null)
    } catch {}
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, loginAsGuest, logout, refreshBalance }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
