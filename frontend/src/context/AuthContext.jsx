import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import api from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const localLogin = () => axios.post('/api/auth/local')
    .then(res => {
      localStorage.setItem('valence_token', res.data.token)
      setUser(res.data.user)
      return true
    })
    .catch(() => false)

  useEffect(() => {
    const restore = async () => {
      const token = localStorage.getItem('valence_token')
      if (!token) return localLogin()
      try {
        const res = await axios.get('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        setUser(res.data)
      } catch {
        localStorage.removeItem('valence_token')
        await localLogin()
      }
    }

    restore().finally(() => setLoading(false))
  }, [])
  const login = (userData, token) => {
    localStorage.setItem('valence_token', token)
    setUser(userData)
  }

  const logout = async () => {
    try { await api.post('/auth/logout') } catch { }
    localStorage.removeItem('valence_token')
    if (!(await localLogin())) setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
