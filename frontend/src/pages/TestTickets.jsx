import React, { useState, useEffect } from 'react'
import { useLocation, useSearchParams, useNavigate } from 'react-router-dom'
import { FileText, CheckCircle, XCircle, TrendingUp, Loader2, ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'
import ProgressIndicator from '../components/ProgressIndicator'
import ValidationReport from '../components/ValidationReport'
import CoverageReviewPanel from '../components/CoverageReviewPanel'
import E2ETicketModal from '../components/E2ETicketModal'

// Helper function to render markdown bold text (**text**) as HTML
const renderMarkdownBold = (text) => {
  if (!text) return ''
  // Replace **text** with <strong>text</strong> and escape HTML first
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // Then convert **bold** to <strong>bold</strong>
  return escaped.replace(/\*\*([^*]+)\*\*/g, '<strong class="text-gray-200 font-semibold">$1</strong>')
}

export default function TestTickets() {
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { progress, clearProgress } = useWebSocket()

  const [testTickets, setTestTickets] = useState([])
  const [validation, setValidation] = useState(null)
  const [coverageReview, setCoverageReview] = useState(null)
  const [epicData, setEpicData] = useState(null)
  const [childTickets, setChildTickets] = useState([])
  const [existingTestTickets, setExistingTestTickets] = useState([])
  const [epicAttachments, setEpicAttachments] = useState([])
  const [childAttachments, setChildAttachments] = useState({})
  const [loading, setLoading] = useState(true)
  const [expandedTicket, setExpandedTicket] = useState(null)
  const [generatingTestCases, setGeneratingTestCases] = useState(null)
  const [error, setError] = useState('')
  const [isClearing, setIsClearing] = useState(false)  // Track if we're clearing history
  const [hasFixedCoverageGaps, setHasFixedCoverageGaps] = useState(false)  // Track if gaps have been fixed
  const [ticketFilter, setTicketFilter] = useState('all')  // 'all', 'generated', 'existing'
  const [generatingE2E, setGeneratingE2E] = useState(false)
  const [e2eTicket, setE2eTicket] = useState(null)  // Backwards compatible
  const [e2eTickets, setE2eTickets] = useState([])  // Multiple functional area E2E tickets
  const [e2eScenarios, setE2eScenarios] = useState([])
  const [showE2EModal, setShowE2EModal] = useState(false)
  const [totalAcsExtracted, setTotalAcsExtracted] = useState(0)
  const [totalAcsPreserved, setTotalAcsPreserved] = useState(0)

  const epicKey = searchParams.get('epic') || location.state?.epicKey

  // Listen for history clear events
  useEffect(() => {
    const handleHistoryClear = () => {
      // Set clearing flag to prevent auto-save
      setIsClearing(true)

      // Clear all state when history is cleared
      setTestTickets([])
      setValidation(null)
      setCoverageReview(null)
      setEpicData(null)
      setChildTickets([])
      setExistingTestTickets([])
      setEpicAttachments([])
      setChildAttachments({})
    }

    window.addEventListener('testTicketsHistoryCleared', handleHistoryClear)
    return () => window.removeEventListener('testTicketsHistoryCleared', handleHistoryClear)
  }, [])

  // Load state from sessionStorage on mount
  useEffect(() => {
    try {
      const savedState = sessionStorage.getItem('testTicketsState')
      if (savedState && !location.state?.testTickets) {
        const state = JSON.parse(savedState)
        if (state.testTickets) setTestTickets(state.testTickets)
        if (state.validation) setValidation(state.validation)
        if (state.coverageReview) setCoverageReview(state.coverageReview)
        if (state.epicData) setEpicData(state.epicData)
        if (state.childTickets) setChildTickets(state.childTickets)
        if (state.existingTestTickets) setExistingTestTickets(state.existingTestTickets)
        if (state.epicAttachments) setEpicAttachments(state.epicAttachments)
        if (state.childAttachments) setChildAttachments(state.childAttachments)
        if (state.hasFixedCoverageGaps !== undefined) setHasFixedCoverageGaps(state.hasFixedCoverageGaps)
        setLoading(false)
        return
      }
    } catch (e) {
      console.error('Failed to load test tickets state:', e)
    }
    // Load from navigation state if available
    if (location.state?.testTickets) {
      console.log('DEBUG: Loading from location.state')
      console.log('DEBUG: testTickets from state:', location.state.testTickets.length)
      console.log('DEBUG: existingTestTickets from state:', location.state.existingTestTickets?.length || 0)

      setTestTickets(location.state.testTickets)
      setExistingTestTickets(location.state.existingTestTickets || [])

      if (location.state.existingTestTickets?.length > 0) {
        console.log('DEBUG: First existing ticket from state:', {
          id: location.state.existingTestTickets[0].id,
          summary: location.state.existingTestTickets[0].summary?.substring(0, 50),
          ac_count: location.state.existingTestTickets[0].acceptance_criteria?.length || 0
        })
      }
    }

    loadTestTickets()
  }, [epicKey])

  // Save state to sessionStorage and history whenever it changes
  useEffect(() => {
    // Don't save if we're in the process of clearing history
    if (isClearing) return

    if (testTickets.length > 0 && epicKey) {
      const stateToSave = {
        epicKey,
        testTickets,
        validation,
        coverageReview,
        epicData,
        childTickets,
        existingTestTickets,
        epicAttachments,
        childAttachments,
        epicSummary: epicData?.fields?.summary || '',
        hasFixedCoverageGaps
      }

      sessionStorage.setItem('testTicketsState', JSON.stringify(stateToSave))

      // Save to history
      const history = JSON.parse(sessionStorage.getItem('testTicketsHistory') || '[]')

      // Check if this epic already exists in history
      const existingIndex = history.findIndex(item => item.epicKey === epicKey)

      if (existingIndex !== -1) {
        // Update existing entry in place (don't reorder)
        history[existingIndex] = stateToSave
        sessionStorage.setItem('testTicketsHistory', JSON.stringify(history))
      } else {
        // New entry - add to the beginning
        history.unshift(stateToSave)
        // Keep only the last 10 entries
        const trimmedHistory = history.slice(0, 10)
        sessionStorage.setItem('testTicketsHistory', JSON.stringify(trimmedHistory))
      }

      window.dispatchEvent(new Event('testTicketsHistoryUpdated'))
    }
  }, [testTickets, validation, coverageReview, epicData, childTickets, existingTestTickets, epicAttachments, childAttachments, epicKey, isClearing, hasFixedCoverageGaps])

  const loadTestTickets = async () => {
    setLoading(true)
    setError('')

    try {
      // Check if we have tickets in location state (just generated)
      if (location.state?.testTickets) {
        console.log('Using tickets from location state:', location.state.testTickets)
        setTestTickets(location.state.testTickets)
        setValidation(location.state.validation || null)
        setCoverageReview(location.state.coverageReview || null)
        setEpicData(location.state.epicData || null)
        setChildTickets(location.state.childTickets || [])
        setExistingTestTickets(location.state.existingTestTickets || [])
        setEpicAttachments(location.state.epicAttachments || [])
        setChildAttachments(location.state.childAttachments || {})
        setLoading(false)
        return
      }

      // Otherwise fetch from API
      if (epicKey) {
        console.log('Fetching tickets for epic:', epicKey)
        const response = await api.get(`/test-tickets?epic_key=${epicKey}`)
        setTestTickets(response.data.test_tickets || [])
      } else {
        // Fetch all tickets
        const response = await api.get('/test-tickets')
        setTestTickets(response.data.test_tickets || [])
      }
    } catch (err) {
      console.error('Failed to load test tickets:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to load test tickets')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateTestCases = async (ticketId) => {
    setGeneratingTestCases(ticketId)
    clearProgress()

    try {
      console.log('Generating test cases for ticket:', ticketId)

      const response = await api.post(`/test-tickets/${ticketId}/generate-test-cases`)

      console.log('Test cases generated:', response.data)

      // Update ticket with test cases
      setTestTickets(tickets => tickets.map(ticket =>
        ticket.id === ticketId
          ? {
              ...ticket,
              test_cases: response.data.test_cases,
              requirements: response.data.requirements,
              analyzed: true
            }
          : ticket
      ))

      // Navigate to test generation page with the generated test cases
      navigate('/test-generation', {
        state: {
          testCases: response.data.test_cases,
          ticketInfo: response.data.ticket_info,
          requirements: response.data.requirements,
          sourceType: 'test_ticket',
          sourceId: ticketId
        }
      })

    } catch (err) {
      console.error('Failed to generate test cases:', err)
      const errorMsg = err.response?.data?.detail || err.message
      alert(`Failed to generate test cases: ${errorMsg}`)
    } finally {
      setGeneratingTestCases(null)
    }
  }

  const handleGenerateE2E = async () => {
    setGeneratingE2E(true)
    clearProgress()

    try {
      console.log('Generating E2E tickets for epic:', epicKey)

      const response = await api.post('/test-tickets/generate-e2e', {
        epic_key: epicKey,
        test_tickets: testTickets,
        existing_test_tickets: existingTestTickets,
        epic_data: epicData
      })

      console.log('E2E tickets generated:', response.data)

      // Handle new format with multiple functional area E2E tickets
      if (response.data.e2e_tickets) {
        setE2eTickets(response.data.e2e_tickets)
        setTotalAcsExtracted(response.data.total_acs_extracted || 0)
        setTotalAcsPreserved(response.data.total_acs_preserved || 0)
      }

      // Backwards compatible - also set single ticket
      setE2eTicket(response.data.e2e_ticket)
      setE2eScenarios(response.data.all_scenarios || response.data.scenarios || [])
      setShowE2EModal(true)

    } catch (err) {
      console.error('Failed to generate E2E tickets:', err)
      const errorMsg = err.response?.data?.detail || err.message
      alert(`Failed to generate E2E tickets: ${errorMsg}`)
    } finally {
      setGeneratingE2E(false)
    }
  }

  const getQualityColor = (score) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getQualityBg = (score) => {
    if (score >= 80) return 'bg-green-500/10 border-green-500/30'
    if (score >= 60) return 'bg-yellow-500/10 border-yellow-500/30'
    return 'bg-red-500/10 border-red-500/30'
  }

  // Merge tickets for display
  const allTicketsForDisplay = React.useMemo(() => {
    console.log('DEBUG: testTickets count:', testTickets.length)
    console.log('DEBUG: existingTestTickets count:', existingTestTickets.length)

    if (existingTestTickets.length > 0) {
      console.log('DEBUG: First existing ticket:', {
        id: existingTestTickets[0].id,
        summary: existingTestTickets[0].summary?.substring(0, 50),
        ac_count: existingTestTickets[0].acceptance_criteria?.length || 0,
        ticket_source: existingTestTickets[0].ticket_source
      })
    }

    const merged = [
      ...testTickets.map(t => ({ ...t, ticket_source: t.ticket_source || 'generated' })),
      ...existingTestTickets.map(t => ({ ...t, ticket_source: 'existing' }))
    ]

    // Sort: generated first, then existing
    return merged.sort((a, b) => {
      if (a.ticket_source === 'generated' && b.ticket_source === 'existing') return -1
      if (a.ticket_source === 'existing' && b.ticket_source === 'generated') return 1
      return 0
    })
  }, [testTickets, existingTestTickets])

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin text-primary-500" size={32} />
          <span className="ml-3 text-gray-400">Loading test tickets...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center space-x-2 text-gray-400 hover:text-gray-200 mb-4 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back</span>
        </button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-100 mb-2">Test Tickets</h1>
            {epicKey && (
              <p className="text-gray-400">
                Test tickets for Epic: <span className="text-primary-400 font-medium">{epicKey}</span>
              </p>
            )}
          </div>

          {allTicketsForDisplay.length > 0 && (
            <div className="flex items-center space-x-4">
              {/* Filter Buttons */}
              <div className="flex items-center space-x-2 bg-dark-800 rounded-lg p-1">
                <button
                  onClick={() => setTicketFilter('all')}
                  className={clsx(
                    'px-3 py-1 rounded text-sm font-medium transition-colors',
                    ticketFilter === 'all' ? 'bg-primary-500 text-white' : 'text-gray-400 hover:text-gray-200'
                  )}
                >
                  All ({allTicketsForDisplay.length})
                </button>
                <button
                  onClick={() => setTicketFilter('generated')}
                  className={clsx(
                    'px-3 py-1 rounded text-sm font-medium transition-colors',
                    ticketFilter === 'generated' ? 'bg-green-500 text-white' : 'text-gray-400 hover:text-gray-200'
                  )}
                >
                  New ({testTickets.length})
                </button>
                <button
                  onClick={() => setTicketFilter('existing')}
                  className={clsx(
                    'px-3 py-1 rounded text-sm font-medium transition-colors',
                    ticketFilter === 'existing' ? 'bg-blue-500 text-white' : 'text-gray-400 hover:text-gray-200'
                  )}
                >
                  Existing ({existingTestTickets.length})
                </button>
              </div>

              {/* E2E Generation Button */}
              {testTickets.length > 0 && (
                <button
                  onClick={handleGenerateE2E}
                  disabled={generatingE2E}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors shadow-lg flex items-center space-x-2"
                >
                  {generatingE2E ? (
                    <>
                      <Loader2 className="animate-spin" size={16} />
                      <span>Generating E2E...</span>
                    </>
                  ) : (
                    <>
                      <span>Create E2E Test Ticket</span>
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-start space-x-2">
          <XCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Progress Indicator */}
      {progress && <ProgressIndicator progress={progress} />}

      {/* Validation Report */}
      {validation && (
        <ValidationReport
          validation={validation}
          testTickets={testTickets}
          epicKey={epicKey}
          onRegenerate={() => {
            // TODO: Implement regeneration logic
            alert('Regeneration will be implemented in the next step')
          }}
        />
      )}

      {/* Coverage Review */}
      {coverageReview && (
        <div className="mb-8">
          <CoverageReviewPanel
            coverageReview={coverageReview}
            testTickets={testTickets}
            epicData={epicData}
            childTickets={childTickets}
            existingTestTickets={existingTestTickets}
            epicAttachments={epicAttachments}
            childAttachments={childAttachments}
            hasFixedCoverageGaps={hasFixedCoverageGaps}
            onHasFixedChanged={setHasFixedCoverageGaps}
            onFixesApplied={(appliedTickets, updatedCoverageReview, removedTicketIds = []) => {
              console.log('onFixesApplied called in TestTickets:', {
                appliedCount: appliedTickets?.length || 0,
                removedCount: removedTicketIds?.length || 0,
                removedIds: removedTicketIds,
                currentTicketCount: testTickets.length
              })

              // Merge applied tickets (both new and updated) into the existing list
              // Create a map of existing tickets by ID
              const ticketMap = new Map(testTickets.map(t => [t.id, t]))

              console.log('Before removal - ticket IDs:', Array.from(ticketMap.keys()))

              // Remove consolidated/deleted tickets first
              removedTicketIds.forEach(ticketId => {
                console.log('Removing ticket:', ticketId)
                ticketMap.delete(ticketId)
              })

              console.log('After removal - ticket IDs:', Array.from(ticketMap.keys()))

              // Update existing tickets or add new ones
              appliedTickets.forEach(ticket => {
                ticketMap.set(ticket.id, ticket)
              })

              console.log('After adding new tickets - ticket IDs:', Array.from(ticketMap.keys()))

              // Convert map back to array
              const newTickets = Array.from(ticketMap.values())
              console.log('Final ticket count:', newTickets.length)
              setTestTickets(newTickets)

              // Update coverage review with recalculated coverage percentage
              if (updatedCoverageReview) {
                setCoverageReview(updatedCoverageReview)
              }
            }}
          />
        </div>
      )}

      {/* Test Tickets List */}
      {allTicketsForDisplay.length === 0 ? (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-12 text-center">
          <FileText className="mx-auto text-gray-600 mb-4" size={48} />
          <p className="text-gray-400 mb-2">No test tickets found</p>
          <p className="text-gray-500 text-sm">
            Analyze an Epic and select a strategic option to generate test tickets
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {allTicketsForDisplay
            .filter(ticket => {
              if (ticketFilter === 'all') return true
              return ticket.ticket_source === ticketFilter
            })
            .map((ticket) => {
            const isExpanded = expandedTicket === ticket.id
            const isGenerating = generatingTestCases === ticket.id
            const qualityScore = ticket.quality_score || 0
            const isExisting = ticket.ticket_source === 'existing'

            return (
              <div
                key={ticket.id}
                className="bg-dark-900 border border-dark-800 rounded-xl overflow-hidden hover:border-dark-700 transition-colors"
              >
                {/* Ticket Header */}
                <div
                  className="p-6 cursor-pointer"
                  onClick={() => setExpandedTicket(isExpanded ? null : ticket.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {/* Source Badge */}
                        {isExisting ? (
                          <div className="px-2 py-1 bg-blue-500/10 border border-blue-500/30 rounded-md flex items-center space-x-1">
                            <span className="text-xs text-blue-400 font-medium">Existing</span>
                          </div>
                        ) : (
                          <div className="px-2 py-1 bg-green-500/10 border border-green-500/30 rounded-md flex items-center space-x-1">
                            <span className="text-xs text-green-400 font-medium">New</span>
                          </div>
                        )}

                        <h3 className="text-xl font-semibold text-gray-100">
                          {ticket.id}: {ticket.summary}
                        </h3>

                        {ticket.analyzed && (
                          <div className="px-2 py-1 bg-green-500/10 border border-green-500/30 rounded-md flex items-center space-x-1">
                            <CheckCircle size={14} className="text-green-400" />
                            <span className="text-xs text-green-400 font-medium">Analyzed</span>
                          </div>
                        )}

                        {ticket.is_e2e_ticket && (
                          <div className="px-2 py-1 bg-purple-500/10 border border-purple-500/30 rounded-md flex items-center space-x-1">
                            <span className="text-xs text-purple-400 font-medium">E2E</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        {ticket.functional_area && (
                          <span>Area: {ticket.functional_area}</span>
                        )}
                        {ticket.stats?.ac_count > 0 && (
                          <span>{ticket.stats.ac_count} Acceptance Criteria</span>
                        )}
                        {ticket.child_tickets?.length > 0 && (
                          <span>{ticket.child_tickets.length} Source Tickets</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 ml-4">
                      {/* Quality Score */}
                      {qualityScore > 0 && (
                        <div className={clsx('px-4 py-2 border rounded-lg', getQualityBg(qualityScore))}>
                          <div className="flex items-center space-x-2">
                            <TrendingUp size={16} className={getQualityColor(qualityScore)} />
                            <span className={clsx('text-xl font-bold', getQualityColor(qualityScore))}>
                              {qualityScore}
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">Quality</p>
                        </div>
                      )}

                      {/* Expand Button */}
                      <button className="p-2 hover:bg-dark-800 rounded-lg transition-colors">
                        {isExpanded ? (
                          <ChevronUp size={20} className="text-gray-400" />
                        ) : (
                          <ChevronDown size={20} className="text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="border-t border-dark-800 p-6 space-y-6">
                    {/* Description */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Description</h4>
                      <div className="bg-dark-800 rounded-lg p-4">
                        <p
                          className="text-gray-400 text-sm whitespace-pre-wrap"
                          dangerouslySetInnerHTML={{ __html: renderMarkdownBold(ticket.description) }}
                        />
                      </div>
                    </div>

                    {/* Acceptance Criteria */}
                    {ticket.acceptance_criteria?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">
                          Acceptance Criteria ({ticket.acceptance_criteria.length})
                        </h4>
                        <div className="bg-dark-800 rounded-lg p-4 space-y-2">
                          {ticket.acceptance_criteria.map((ac, i) => (
                            <div key={i} className="flex items-start space-x-2">
                              <span className="text-primary-400 font-medium">{i + 1}.</span>
                              <span className="text-gray-400 text-sm">{ac}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Source Child Tickets */}
                    {ticket.child_tickets?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">
                          Source Tickets ({ticket.child_tickets.length})
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {ticket.child_tickets.map((child, i) => (
                            <div key={i} className="bg-dark-800 rounded-lg p-3">
                              <span className="text-primary-400 font-medium text-sm">{child.key}</span>
                              <p className="text-gray-400 text-xs mt-1">{child.summary}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Review Feedback */}
                    {ticket.review_feedback && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">Review Feedback</h4>
                        <div className="bg-dark-800 rounded-lg p-4 space-y-3">
                          {ticket.review_feedback.strengths?.length > 0 && (
                            <div>
                              <p className="text-xs text-gray-500 mb-1">Strengths:</p>
                              <ul className="space-y-1">
                                {ticket.review_feedback.strengths.map((strength, i) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <span className="text-green-400 text-xs">✓</span>
                                    <span className="text-gray-400 text-xs">{strength}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {ticket.review_feedback.issues?.length > 0 && (
                            <div>
                              <p className="text-xs text-gray-500 mb-1">Issues:</p>
                              <ul className="space-y-1">
                                {ticket.review_feedback.issues.map((issue, i) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <span className="text-yellow-400 text-xs">!</span>
                                    <span className="text-gray-400 text-xs">{issue}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Test Cases (if already generated) */}
                    {ticket.test_cases?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">
                          Generated Test Cases ({ticket.test_cases.length})
                        </h4>
                        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                          <p className="text-green-400 text-sm mb-2">
                            Test cases have been generated for this ticket
                          </p>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              navigate('/test-generation', {
                                state: {
                                  testCases: ticket.test_cases,
                                  ticketInfo: { id: ticket.id, summary: ticket.summary },
                                  requirements: ticket.requirements,
                                  sourceType: 'test_ticket',
                                  sourceId: ticket.id
                                }
                              })
                            }}
                            className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white text-sm font-medium rounded-lg transition-colors"
                          >
                            View Test Cases
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex justify-end space-x-3 pt-4 border-t border-dark-800">
                      {!ticket.analyzed && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleGenerateTestCases(ticket.id)
                          }}
                          disabled={isGenerating}
                          className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-nebula flex items-center space-x-2"
                        >
                          {isGenerating ? (
                            <>
                              <Loader2 className="animate-spin" size={18} />
                              <span>Generating Test Cases...</span>
                            </>
                          ) : (
                            <span>Generate Test Cases</span>
                          )}
                        </button>
                      )}

                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          const criteriaText = ticket.acceptance_criteria.map((ac, i) => `${i + 1}. ${ac}`).join('\n')
                          const jiraFormat = `*Summary:* ${ticket.summary}\n\n*Description:*\n${ticket.description}\n\n*Acceptance Criteria:*\n${criteriaText}`
                          navigator.clipboard.writeText(jiraFormat)
                          alert('Ticket copied to clipboard in Jira format!')
                        }}
                        className="px-6 py-3 bg-dark-800 hover:bg-dark-700 text-gray-300 font-medium rounded-lg transition-colors"
                      >
                        Copy to Clipboard
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* E2E Ticket Modal */}
      {showE2EModal && (e2eTickets.length > 0 || e2eTicket) && (
        <E2ETicketModal
          e2eTicket={e2eTicket}
          e2eTickets={e2eTickets}
          scenarios={e2eScenarios}
          totalAcsExtracted={totalAcsExtracted}
          totalAcsPreserved={totalAcsPreserved}
          onClose={() => setShowE2EModal(false)}
          onAccept={(ticketsToAdd) => {
            // Add selected E2E tickets to test tickets list
            // ticketsToAdd is an array of tickets from the modal
            const ticketsArray = Array.isArray(ticketsToAdd) ? ticketsToAdd : [ticketsToAdd]
            setTestTickets(tickets => [...tickets, ...ticketsArray])
            setShowE2EModal(false)
            alert(`${ticketsArray.length} E2E ticket(s) added to test tickets list!`)
          }}
        />
      )}
    </div>
  )
}
