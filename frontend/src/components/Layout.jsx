import React from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LogOut, Home, FileText, TestTube2, ListChecks } from 'lucide-react'

export default function Layout() {
  const { logout, jiraUrl } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/epic-analysis', icon: FileText, label: 'Epic Analysis' },
    { path: '/test-tickets', icon: ListChecks, label: 'Test Tickets' },
    { path: '/test-generation', icon: TestTube2, label: 'Test Generation' },
  ]

  return (
    <div className="min-h-screen bg-dark-950 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-900 border-r border-dark-800 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-dark-800">
          <h1 className="text-2xl font-bold text-primary-500">AI Tester</h1>
          <p className="text-sm text-gray-400 mt-1">Framework v3.0</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-500 text-white shadow-nebula'
                    : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-dark-800">
          <div className="mb-3 p-3 bg-dark-800 rounded-lg">
            <p className="text-xs text-gray-400">Connected to</p>
            <p className="text-sm text-primary-400 font-mono truncate">{jiraUrl}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
