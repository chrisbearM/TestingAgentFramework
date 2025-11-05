import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Lock, Mail, Link as LinkIcon, AlertCircle } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [formData, setFormData] = useState({
    base_url: '',
    email: '',
    api_token: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    console.log('[Login] Form submitted')
    console.log('[Login] Form data:', {
      base_url: formData.base_url,
      email: formData.email,
      api_token_length: formData.api_token?.length || 0,
      api_token_starts_with: formData.api_token?.substring(0, 4) || 'N/A'
    })

    const result = await login(formData)

    console.log('[Login] Login result:', result)

    if (result.success) {
      console.log('[Login] Login successful, navigating to /')
      navigate('/')
    } else {
      console.error('[Login] Login failed:', result.error)
      setError(result.error)
    }

    setLoading(false)
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary-500 mb-2">AI Tester Framework</h1>
          <p className="text-gray-400">Sign in with your Jira credentials</p>
        </div>

        {/* Login Card */}
        <div className="bg-dark-900 border border-dark-800 rounded-xl shadow-nebula-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Jira URL */}
            <div>
              <label htmlFor="base_url" className="block text-sm font-medium text-gray-300 mb-2">
                Jira Base URL
              </label>
              <div className="relative">
                <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="url"
                  id="base_url"
                  name="base_url"
                  value={formData.base_url}
                  onChange={handleChange}
                  placeholder="https://your-domain.atlassian.net"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="your.email@company.com"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* API Token */}
            <div>
              <label htmlFor="api_token" className="block text-sm font-medium text-gray-300 mb-2">
                API Token
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="password"
                  id="api_token"
                  name="api_token"
                  value={formData.api_token}
                  onChange={handleChange}
                  placeholder="Your Jira API token"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-start space-x-3 p-4 bg-red-900/20 border border-red-800 rounded-lg">
                <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-400 mb-1">Authentication Failed</p>
                  <p className="text-sm text-red-300">{error}</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-nebula"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Help Text */}
          <div className="mt-6 pt-6 border-t border-dark-800">
            <p className="text-sm text-gray-400 text-center">
              Don't have an API token?{' '}
              <a
                href="https://id.atlassian.com/manage-profile/security/api-tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-400 hover:text-primary-300"
              >
                Create one here
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
