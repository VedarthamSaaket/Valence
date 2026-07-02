import { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('valence_token')
    if (token) {
      api.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => localStorage.removeItem('valence_token'))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])
  const login = (userData, token) => {
    localStorage.setItem('valence_token', token)
    setUser(userData)
  }

  const logout = async () => {
    try { await api.post('/auth/logout') } catch { }
    localStorage.removeItem('valence_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
