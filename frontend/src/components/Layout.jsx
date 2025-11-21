import React, { useState, useEffect } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LogOut, Home, FileText, TestTube2, ListChecks, ChevronDown, ChevronRight, XCircle, Sparkles } from 'lucide-react'

export default function Layout() {
  const { logout, jiraUrl } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [epicAnalysisExpanded, setEpicAnalysisExpanded] = useState(false)
  const [testTicketsExpanded, setTestTicketsExpanded] = useState(false)
  const [testGenExpanded, setTestGenExpanded] = useState(false)
  const [epicAnalysisHistory, setEpicAnalysisHistory] = useState([])
  const [testTicketsHistory, setTestTicketsHistory] = useState([])
  const [testCasesHistory, setTestCasesHistory] = useState([])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Load histories from sessionStorage
  useEffect(() => {
    const loadHistories = () => {
      try {
        const epicHistory = sessionStorage.getItem('epicAnalysisHistory')
        if (epicHistory) {
          setEpicAnalysisHistory(JSON.parse(epicHistory))
        }

        const ticketsHistory = sessionStorage.getItem('testTicketsHistory')
        if (ticketsHistory) {
          setTestTicketsHistory(JSON.parse(ticketsHistory))
        }

        const casesHistory = sessionStorage.getItem('testCasesHistory')
        if (casesHistory) {
          setTestCasesHistory(JSON.parse(casesHistory))
        }
      } catch (e) {
        console.error('Failed to load histories:', e)
      }
    }

    loadHistories()

    // Listen for custom events to update when new items are added
    const handleStorageChange = () => loadHistories()
    window.addEventListener('epicAnalysisHistoryUpdated', handleStorageChange)
    window.addEventListener('testTicketsHistoryUpdated', handleStorageChange)
    window.addEventListener('testCasesHistoryUpdated', handleStorageChange)

    return () => {
      window.removeEventListener('epicAnalysisHistoryUpdated', handleStorageChange)
      window.removeEventListener('testTicketsHistoryUpdated', handleStorageChange)
      window.removeEventListener('testCasesHistoryUpdated', handleStorageChange)
    }
  }, [])

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
  ]

  const handleEpicAnalysisClick = (epicKey) => {
    // Load the selected epic analysis state
    const history = JSON.parse(sessionStorage.getItem('epicAnalysisHistory') || '[]')
    const selectedEpic = history.find(item => item.epicKey === epicKey)
    if (selectedEpic) {
      sessionStorage.setItem('epicAnalysisState', JSON.stringify(selectedEpic))
      navigate('/epic-analysis')
    }
  }

  const handleTestTicketClick = (epicKey) => {
    // Load the selected test tickets state
    const history = JSON.parse(sessionStorage.getItem('testTicketsHistory') || '[]')
    const selectedTickets = history.find(item => item.epicKey === epicKey)
    if (selectedTickets) {
      sessionStorage.setItem('testTicketsState', JSON.stringify(selectedTickets))
      navigate('/test-tickets')
    }
  }

  const handleTestCaseClick = (ticketKey) => {
    // Load the selected test case state
    const history = JSON.parse(sessionStorage.getItem('testCasesHistory') || '[]')
    const selectedCase = history.find(item => item.ticketKey === ticketKey)
    if (selectedCase) {
      sessionStorage.setItem('testGenerationState', JSON.stringify(selectedCase))
      // Dispatch event to notify TestGeneration page to reload state
      window.dispatchEvent(new Event('testGenerationStateUpdated'))
      navigate('/test-generation')
    }
  }

  const handleClearHistory = () => {
    if (window.confirm('Clear all navigation history? This will remove all saved epic analyses, test tickets, and test cases from the sidebar.')) {
      // Clear all histories
      sessionStorage.removeItem('epicAnalysisHistory')
      sessionStorage.removeItem('testTicketsHistory')
      sessionStorage.removeItem('testCasesHistory')
      sessionStorage.removeItem('epicAnalysisState')
      sessionStorage.removeItem('testTicketsState')
      sessionStorage.removeItem('testGenerationState')

      // Update state
      setEpicAnalysisHistory([])
      setTestTicketsHistory([])
      setTestCasesHistory([])

      // Collapse all menus
      setEpicAnalysisExpanded(false)
      setTestTicketsExpanded(false)
      setTestGenExpanded(false)

      // Dispatch events to update any listeners
      window.dispatchEvent(new Event('epicAnalysisHistoryUpdated'))
      window.dispatchEvent(new Event('testTicketsHistoryUpdated'))
      window.dispatchEvent(new Event('testCasesHistoryUpdated'))

      // Dispatch events to clear page state
      window.dispatchEvent(new Event('epicAnalysisHistoryCleared'))
      window.dispatchEvent(new Event('testTicketsHistoryCleared'))
      window.dispatchEvent(new Event('testCasesHistoryCleared'))

      // Reload the page to ensure all state is cleared
      window.location.reload()
    }
  }

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
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
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

          {/* Epic Analysis with submenu */}
          <div>
            <button
              onClick={() => {
                if (epicAnalysisHistory.length === 0) {
                  navigate('/epic-analysis')
                } else {
                  setEpicAnalysisExpanded(!epicAnalysisExpanded)
                }
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
                location.pathname === '/epic-analysis'
                  ? 'bg-primary-500 text-white shadow-nebula'
                  : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-3">
                <FileText size={20} />
                <span className="font-medium">Epic Analysis</span>
              </div>
              {epicAnalysisHistory.length > 0 && (
                epicAnalysisExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
              )}
            </button>

            {/* Submenu for epic analysis history */}
            {epicAnalysisExpanded && epicAnalysisHistory.length > 0 && (
              <div className="ml-4 mt-1 space-y-1">
                {epicAnalysisHistory.map((item) => (
                  <button
                    key={item.epicKey}
                    onClick={() => handleEpicAnalysisClick(item.epicKey)}
                    className="w-full text-left px-4 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-dark-800 rounded-lg transition-colors truncate"
                    title={`${item.epicKey}: ${item.epicSummary || 'Epic Analysis'}`}
                  >
                    <div className="flex items-center space-x-2">
                      <FileText size={14} />
                      <span className="truncate">{item.epicKey}</span>
                    </div>
                    {item.epicSummary && (
                      <div className="text-xs text-gray-500 truncate ml-5 mt-0.5">
                        {item.epicSummary}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Test Tickets with submenu */}
          <div>
            <button
              onClick={() => {
                if (testTicketsHistory.length === 0) {
                  navigate('/test-tickets')
                } else {
                  setTestTicketsExpanded(!testTicketsExpanded)
                }
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
                location.pathname === '/test-tickets'
                  ? 'bg-primary-500 text-white shadow-nebula'
                  : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-3">
                <ListChecks size={20} />
                <span className="font-medium">Test Tickets</span>
              </div>
              {testTicketsHistory.length > 0 && (
                testTicketsExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
              )}
            </button>

            {/* Submenu for test tickets history */}
            {testTicketsExpanded && testTicketsHistory.length > 0 && (
              <div className="ml-4 mt-1 space-y-1">
                {testTicketsHistory.map((item) => (
                  <button
                    key={item.epicKey}
                    onClick={() => handleTestTicketClick(item.epicKey)}
                    className="w-full text-left px-4 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-dark-800 rounded-lg transition-colors truncate"
                    title={`${item.epicKey}: ${item.epicSummary || 'Test Tickets'}`}
                  >
                    <div className="flex items-center space-x-2">
                      <ListChecks size={14} />
                      <span className="truncate">{item.epicKey}</span>
                    </div>
                    {item.epicSummary && (
                      <div className="text-xs text-gray-500 truncate ml-5 mt-0.5">
                        {item.epicSummary}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Ticket Improver */}
          <Link
            to="/ticket-improver"
            className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/ticket-improver'
                ? 'bg-primary-500 text-white shadow-nebula'
                : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
            }`}
          >
            <Sparkles size={20} />
            <span className="font-medium">Ticket Improver</span>
          </Link>

          {/* Test Generation with submenu */}
          <div>
            <button
              onClick={() => {
                if (testCasesHistory.length === 0) {
                  navigate('/test-generation')
                } else {
                  setTestGenExpanded(!testGenExpanded)
                }
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
                location.pathname === '/test-generation'
                  ? 'bg-primary-500 text-white shadow-nebula'
                  : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-3">
                <TestTube2 size={20} />
                <span className="font-medium">Test Generation</span>
              </div>
              {testCasesHistory.length > 0 && (
                testGenExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
              )}
            </button>

            {/* Submenu for test cases history */}
            {testGenExpanded && testCasesHistory.length > 0 && (
              <div className="ml-4 mt-1 space-y-1">
                {testCasesHistory.map((item) => (
                  <button
                    key={item.ticketKey}
                    onClick={() => handleTestCaseClick(item.ticketKey)}
                    className="w-full text-left px-4 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-dark-800 rounded-lg transition-colors truncate"
                    title={`${item.ticketKey}: ${item.ticket?.fields?.summary || 'Test Cases'}`}
                  >
                    <div className="flex items-center space-x-2">
                      <FileText size={14} />
                      <span className="truncate">{item.ticketKey}</span>
                    </div>
                    {item.ticket?.fields?.summary && (
                      <div className="text-xs text-gray-500 truncate ml-5 mt-0.5">
                        {item.ticket.fields.summary}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-dark-800 space-y-2">
          <div className="p-3 bg-dark-800 rounded-lg">
            <p className="text-xs text-gray-400">Connected to</p>
            <p className="text-sm text-primary-400 font-mono truncate">{jiraUrl}</p>
          </div>

          {/* Clear History Button */}
          {(epicAnalysisHistory.length > 0 || testTicketsHistory.length > 0 || testCasesHistory.length > 0) && (
            <button
              onClick={handleClearHistory}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-400 hover:text-gray-200 rounded-lg transition-colors text-sm"
              title="Clear all navigation history"
            >
              <XCircle size={16} />
              <span>Clear History</span>
            </button>
          )}

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
