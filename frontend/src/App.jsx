import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import './styles/global.css'

import Navbar from './components/layout/Navbar'
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import Tests from './pages/Tests'
import Questionnaire from './pages/Questionnaire'
import Results from './pages/Results'
import DeepDive from './pages/DeepDive'
import Dashboard from './pages/Dashboard'
import AuthCallback from './pages/AuthCallback'
import Acknowledgements from './pages/Acknowledgements'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <div className="spinner" style={{ width: 40, height: 40 }} />
    </div>
  )
  if (!user) return <Navigate to="/auth" replace />
  return children
}

function AppRoutes() {
  const { user } = useAuth()

  const location = useLocation()

  return (
    <>
      {}
      <Navbar />
      <Routes location={location}>
        <Route path="/"
          element={<Landing key={location.key} />}
        />
        <Route path="/auth"
          element={user ? <Navigate to="/dashboard" /> : <Auth key={location.key} />}
        />
        <Route path="/auth/callback"
          element={<AuthCallback key={location.key} />}
        />
        <Route path="/tests"
          element={<ProtectedRoute><Tests key={location.key} /></ProtectedRoute>}
        />
        <Route path="/tests/:testId"
          element={<ProtectedRoute><Questionnaire key={location.key} /></ProtectedRoute>}
        />
        <Route path="/results/:resultId"
          element={<ProtectedRoute><Results key={location.key} /></ProtectedRoute>}
        />
        <Route path="/deep-dive/:resultId"
          element={<ProtectedRoute><DeepDive key={location.key} /></ProtectedRoute>}
        />
        <Route path="/dashboard"
          element={<ProtectedRoute><Dashboard key={location.key} /></ProtectedRoute>}
        />
        <Route path="/acknowledgements"
          element={<Acknowledgements key={location.key} />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
