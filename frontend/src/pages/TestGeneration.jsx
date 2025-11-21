import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Search, Loader2, TestTube2, XCircle, CheckCircle, Sparkles, ArrowLeft, ArrowRight, FileText } from 'lucide-react'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'
import TestCaseEditor from '../components/TestCaseEditor'
import ProgressIndicator from '../components/ProgressIndicator'
import ReadinessAssessment from '../components/ReadinessAssessment'
import clsx from 'clsx'

// Helper function to safely extract text from Jira description
const extractDescription = (description) => {
  if (!description) return ''
  if (typeof description === 'string') return description

  // Handle Atlassian Document Format (ADF)
  if (description.type === 'doc' && description.content) {
    return extractTextFromADF(description)
  }

  return JSON.stringify(description)
}

const extractTextFromADF = (adf) => {
  if (!adf || !adf.content) return ''

  const extractFromNode = (node) => {
    let text = ''

    // Handle text nodes
    if (node.type === 'text' && node.text) {
      return node.text
    }

    // Handle nodes with content arrays
    if (node.content && Array.isArray(node.content)) {
      for (const child of node.content) {
        text += extractFromNode(child)
      }
    }

    // Add line breaks after certain node types
    if (node.type === 'paragraph' || node.type === 'heading') {
      text += '\n'
    } else if (node.type === 'listItem') {
      text = '• ' + text + '\n'
    } else if (node.type === 'codeBlock') {
      text = '\n' + text + '\n'
    } else if (node.type === 'hardBreak') {
      text += '\n'
    }

    return text
  }

  let result = ''
  for (const node of adf.content) {
    result += extractFromNode(node)
  }

  return result.trim()
}

export default function TestGeneration() {
  const location = useLocation()
  const navigate = useNavigate()
  const [ticketKey, setTicketKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [ticket, setTicket] = useState(null)
  const [readiness, setReadiness] = useState(null)
  const [testCases, setTestCases] = useState(null)
  const [error, setError] = useState('')
  const [currentStep, setCurrentStep] = useState(0)
  const { progress, clearProgress } = useWebSocket()

  // Listen for history clear events
  useEffect(() => {
    const handleHistoryClear = () => {
      // Clear all state when history is cleared
      setTicket(null)
      setTestCases(null)
      setReadiness(null)
      setTicketKey('')
      setCurrentStep(0)
    }

    window.addEventListener('testCasesHistoryCleared', handleHistoryClear)
    return () => window.removeEventListener('testCasesHistoryCleared', handleHistoryClear)
  }, [])

  // Restore state from sessionStorage on mount and when sidebar navigation occurs
  useEffect(() => {
    const loadState = () => {
      const savedState = sessionStorage.getItem('testGenerationState')
      if (savedState) {
        try {
          const parsed = JSON.parse(savedState)
          // Create new object references to force React to detect changes
          const { ticket: savedTicket, testCases: savedTestCases, readiness: savedReadiness, ticketKey: savedKey, currentStep: savedStep } = parsed

          // Use JSON parse/stringify to create deep copies and ensure new references
          setTicket(savedTicket ? JSON.parse(JSON.stringify(savedTicket)) : null)
          setTestCases(savedTestCases ? JSON.parse(JSON.stringify(savedTestCases)) : null)
          setReadiness(savedReadiness ? JSON.parse(JSON.stringify(savedReadiness)) : null)
          setTicketKey(savedKey || '')
          setCurrentStep(savedStep !== undefined ? savedStep : 0)
        } catch (e) {
          console.error('Failed to restore test generation state:', e)
        }
      }
    }

    loadState()

    // Listen for custom event from sidebar navigation
    window.addEventListener('testGenerationStateUpdated', loadState)
    return () => window.removeEventListener('testGenerationStateUpdated', loadState)
  }, [])

  // Save state to sessionStorage when it changes
  useEffect(() => {
    if (ticket || testCases || readiness) {
      const stateToSave = {
        ticket,
        testCases,
        readiness,
        ticketKey,
        currentStep
      }
      sessionStorage.setItem('testGenerationState', JSON.stringify(stateToSave))

      // If test cases exist, also save to history for quick access
      if (testCases && ticketKey) {
        const history = JSON.parse(sessionStorage.getItem('testCasesHistory') || '[]')

        // Check if this ticket already exists in history
        const existingIndex = history.findIndex(item => item.ticketKey === ticketKey)

        if (existingIndex !== -1) {
          // Update existing entry in place (don't reorder)
          history[existingIndex] = stateToSave
          sessionStorage.setItem('testCasesHistory', JSON.stringify(history))
        } else {
          // New entry - add to the beginning
          history.unshift(stateToSave)
          // Keep only the last 10 entries
          const trimmedHistory = history.slice(0, 10)
          sessionStorage.setItem('testCasesHistory', JSON.stringify(trimmedHistory))
        }

        // Dispatch custom event to notify Layout component
        window.dispatchEvent(new Event('testCasesHistoryUpdated'))
      }
    }
  }, [ticket, testCases, readiness, ticketKey, currentStep])

  // Handle incoming test cases from navigation (e.g., from TestTickets page)
  useEffect(() => {
    if (location.state?.testCases) {
      setTestCases({
        test_cases: location.state.testCases,
        ticket_info: location.state.ticketInfo,
        requirements: location.state.requirements
      })
      // Automatically advance to step 3 to show the test cases
      setCurrentStep(3)
    }
  }, [location.state])

  // Determine where to navigate back to
  const handleBack = () => {
    if (location.state?.sourceType === 'test_ticket') {
      // If we came from test tickets, go back there
      navigate('/test-tickets')
    } else {
      // Otherwise use browser back
      navigate(-1)
    }
  }

  const handleLoadTicket = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setReadiness(null)
    setTestCases(null)
    setCurrentStep(0)
    clearProgress()

    try {
      // Load Ticket
      const ticketResponse = await api.get(`/tickets/${ticketKey}`)
      console.log('=== TICKET LOADED ===')
      console.log('Ticket response:', ticketResponse.data)
      console.log('Has acceptance_criteria?', 'acceptance_criteria' in ticketResponse.data)
      console.log('Acceptance criteria value:', ticketResponse.data.acceptance_criteria)
      setTicket(ticketResponse.data)

      // Assess Readiness
      const readinessResponse = await api.post(`/tickets/${ticketKey}/analyze`)
      setReadiness(readinessResponse.data.assessment)

      // Clear progress after successful load
      setTimeout(() => clearProgress(), 1000)

      // Advance to first step (Ticket Overview)
      setCurrentStep(1)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load ticket')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateTestCases = async () => {
    setError('')
    setGenerating(true)
    clearProgress()

    try {
      const response = await api.post('/test-cases/generate', {
        ticket_key: ticketKey,
        include_attachments: true
      })

      setTestCases(response.data)
    } catch (err) {
      console.error('Test case generation error:', err)
      setError(err.response?.data?.detail || 'Failed to generate test cases')
    } finally {
      setGenerating(false)
    }
  }

  const clearTestGeneration = () => {
    setTicketKey('')
    setTicket(null)
    setReadiness(null)
    setTestCases(null)
    setCurrentStep(0)
    setError('')
    // Clear current state only (keep history)
    sessionStorage.removeItem('testGenerationState')
  }

  const steps = [
    { number: 1, name: 'Ticket Overview', description: 'Review ticket details' },
    { number: 2, name: 'Readiness Assessment', description: 'Evaluate ticket quality' },
    { number: 3, name: 'Test Generation', description: 'Generate test cases' }
  ]

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 mb-2">Test Case Generation</h1>
          <p className="text-gray-400">
            Load a ticket and let our AI system guide you through readiness assessment and test case generation
          </p>
        </div>
        {ticket && (
          <button
            onClick={clearTestGeneration}
            className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 font-medium rounded-lg transition-colors flex items-center space-x-2 border border-dark-700"
          >
            <Search size={16} />
            <span>New Analysis</span>
          </button>
        )}
      </div>

      {/* Compact Ticket Info - Show at top when navigating steps */}
      {ticket && (
        <div className="bg-dark-900 border border-dark-800 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="text-primary-400" size={20} />
              <div>
                <h3 className="font-semibold text-gray-100">{ticket.key}: {ticket.fields.summary}</h3>
                <p className="text-sm text-gray-400">
                  {ticket.fields.issuetype?.name} • {ticket.fields.priority?.name} • {ticket.fields.status?.name}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step Indicator - Show only when we have a ticket loaded */}
      {ticket && (
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <React.Fragment key={step.number}>
                <div className="flex items-center space-x-4">
                  <div
                    className={clsx(
                      'flex items-center justify-center w-10 h-10 rounded-full font-semibold transition-all',
                      currentStep >= step.number
                        ? 'bg-primary-500 text-white'
                        : 'bg-dark-800 text-gray-400 border border-dark-700'
                    )}
                  >
                    {currentStep > step.number ? (
                      <CheckCircle size={20} />
                    ) : (
                      step.number
                    )}
                  </div>
                  <div className="hidden sm:block">
                    <div className={clsx(
                      'font-medium',
                      currentStep >= step.number ? 'text-gray-100' : 'text-gray-500'
                    )}>
                      {step.name}
                    </div>
                    <div className="text-sm text-gray-500">{step.description}</div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={clsx(
                      'flex-1 h-0.5 mx-4 transition-all',
                      currentStep > step.number ? 'bg-primary-500' : 'bg-dark-700'
                    )}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Search Form - Hide when ticket is loaded */}
      {!ticket && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
          <form onSubmit={handleLoadTicket} className="flex gap-4">
            <div className="flex-1">
              <label htmlFor="ticketKey" className="block text-sm font-medium text-gray-300 mb-2">
                Ticket Key
              </label>
              <div className="relative">
                <TestTube2 className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  id="ticketKey"
                  value={ticketKey}
                  onChange={(e) => setTicketKey(e.target.value.toUpperCase())}
                  placeholder="e.g., UEX-326"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-nebula flex items-center space-x-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Search size={18} />
                    <span>Analyze Ticket</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-start space-x-2">
              <XCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>
      )}

      {/* Progress Indicator */}
      {progress && <ProgressIndicator progress={progress} />}

      {/* Step 1: Ticket Overview */}
      {ticket && currentStep === 1 && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-100 mb-1">
                {ticket.key}: {ticket.fields?.summary}
              </h2>
              <p className="text-gray-400">
                {ticket.fields?.issuetype?.name} • {ticket.fields?.priority?.name}
              </p>
            </div>
            <div className="px-3 py-1 bg-primary-500/10 border border-primary-500/20 rounded-full">
              <span className="text-primary-400 text-sm font-medium">{ticket.fields?.status?.name}</span>
            </div>
          </div>

          {ticket.fields?.description && (
            <div className="mt-4 p-4 bg-dark-800 rounded-lg">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Description</h3>
              <div className="text-gray-400 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                {extractDescription(ticket.fields.description)}
              </div>
            </div>
          )}

          {ticket.acceptance_criteria && (
            <div className="mt-4 p-4 bg-dark-800 rounded-lg border-l-4 border-primary-500">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Acceptance Criteria</h3>
              <div className="text-gray-400 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                {ticket.acceptance_criteria}
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-end mt-6 pt-6 border-t border-dark-800">
            <button
              onClick={() => setCurrentStep(2)}
              disabled={!readiness}
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-dark-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              <span>Continue to Readiness Assessment</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Readiness Assessment */}
      {readiness && ticket && currentStep === 2 && (
        <div className="mb-8">
          <ReadinessAssessment
            assessment={readiness}
            epicData={{
              key: ticket.key,
              summary: ticket.fields.summary,
              description: extractDescription(ticket.fields.description)
            }}
            itemType="Ticket"
          />

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-6">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-6 py-3 bg-dark-800 hover:bg-dark-700 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              <ArrowLeft size={18} />
              <span>Back to Ticket Overview</span>
            </button>
            <button
              onClick={() => {
                setCurrentStep(3)
                // Only generate test cases if we haven't already
                if (!testCases) {
                  handleGenerateTestCases()
                }
              }}
              disabled={generating}
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-dark-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              {generating ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Generating Test Cases...</span>
                </>
              ) : (
                <>
                  <span>Continue to Test Generation</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Test Generation */}
      {currentStep === 3 && (
        <div>
          {testCases ? (
            <TestCaseEditor
              key={ticketKey}
              testCases={testCases.test_cases}
              ticketInfo={testCases.ticket_info}
              requirements={testCases.requirements}
              improvedTicket={testCases.improved_ticket}
            />
          ) : (
            <div className="bg-dark-900 border border-dark-800 rounded-xl p-12 text-center">
              <Loader2 className="animate-spin mx-auto mb-4 text-primary-400" size={48} />
              <h3 className="text-xl font-semibold text-gray-100 mb-2">Generating Test Cases...</h3>
              <p className="text-gray-400">Please wait while we generate comprehensive test cases for your ticket</p>
            </div>
          )}

          {/* Navigation Buttons */}
          {testCases && (
            <div className="flex justify-start mt-6">
              <button
                onClick={() => setCurrentStep(2)}
                className="px-6 py-3 bg-dark-800 hover:bg-dark-700 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
              >
                <ArrowLeft size={18} />
                <span>Back to Readiness Assessment</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
