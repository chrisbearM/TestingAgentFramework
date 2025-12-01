import React, { createContext, useState, useContext, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [jiraUrl, setJiraUrl] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    checkAuthStatus()
  }, [])

  // Listen for auth-error events from API client
  useEffect(() => {
    const handleAuthError = (event) => {
      console.log('[AuthContext] Auth error event received:', event.detail)
      setIsAuthenticated(false)
      setJiraUrl(null)
      navigate('/login', { replace: true })
    }

    window.addEventListener('auth-error', handleAuthError)
    return () => window.removeEventListener('auth-error', handleAuthError)
  }, [navigate])

  const checkAuthStatus = async () => {
    console.log('[AuthContext] Checking auth status...')
    try {
      const response = await api.get('/auth/status')
      console.log('[AuthContext] Auth status response:', response.data)
      setIsAuthenticated(response.data.authenticated)
      setJiraUrl(response.data.jira_url)
    } catch (error) {
      console.error('[AuthContext] Auth status check failed:', error)
      setIsAuthenticated(false)
    } finally {
      setLoading(false)
    }
  }

  const login = async (credentials) => {
    console.log('[AuthContext] Login attempt starting')
    console.log('[AuthContext] Credentials:', {
      base_url: credentials.base_url,
      email: credentials.email,
      api_token_length: credentials.api_token?.length || 0
    })

    try {
      console.log('[AuthContext] Sending POST /auth/login...')
      const response = await api.post('/auth/login', credentials)
      console.log('[AuthContext] Login response:', response.data)

      setIsAuthenticated(true)
      setJiraUrl(credentials.base_url)
      console.log('[AuthContext] Login successful!')
      return { success: true }
    } catch (error) {
      console.error('[AuthContext] Login failed:', error)
      console.error('[AuthContext] Error response:', error.response?.data)
      console.error('[AuthContext] Error status:', error.response?.status)

      return {
        success: false,
        error: error.response?.data?.detail || 'Authentication failed'
      }
    }
  }

  const logout = () => {
    setIsAuthenticated(false)
    setJiraUrl(null)
  }

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      loading,
      jiraUrl,
      login,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
