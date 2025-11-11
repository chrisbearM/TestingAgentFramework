import React, { useState, useEffect } from 'react'
import { useLocation, useSearchParams, useNavigate } from 'react-router-dom'
import { FileText, CheckCircle, XCircle, TrendingUp, Loader2, ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'
import ProgressIndicator from '../components/ProgressIndicator'
import ValidationReport from '../components/ValidationReport'
import CoverageReviewPanel from '../components/CoverageReviewPanel'

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
  const [loading, setLoading] = useState(true)
  const [expandedTicket, setExpandedTicket] = useState(null)
  const [generatingTestCases, setGeneratingTestCases] = useState(null)
  const [error, setError] = useState('')

  const epicKey = searchParams.get('epic') || location.state?.epicKey

  useEffect(() => {
    loadTestTickets()
  }, [epicKey])

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
            <h1 className="text-3xl font-bold text-gray-100 mb-2">Generated Test Tickets</h1>
            {epicKey && (
              <p className="text-gray-400">
                Test tickets for Epic: <span className="text-primary-400 font-medium">{epicKey}</span>
              </p>
            )}
          </div>

          {testTickets.length > 0 && (
            <div className="px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-lg">
              <p className="text-sm text-primary-400 font-medium">
                {testTickets.length} {testTickets.length === 1 ? 'Ticket' : 'Tickets'}
              </p>
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
            onFixesApplied={(appliedTickets, updatedCoverageReview) => {
              // Merge applied tickets (both new and updated) into the existing list
              // Create a map of existing tickets by ID
              const ticketMap = new Map(testTickets.map(t => [t.id, t]))

              // Update existing tickets or add new ones
              appliedTickets.forEach(ticket => {
                ticketMap.set(ticket.id, ticket)
              })

              // Convert map back to array
              setTestTickets(Array.from(ticketMap.values()))

              // Update coverage review with recalculated coverage percentage
              if (updatedCoverageReview) {
                setCoverageReview(updatedCoverageReview)
              }
            }}
          />
        </div>
      )}

      {/* Test Tickets List */}
      {testTickets.length === 0 ? (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-12 text-center">
          <FileText className="mx-auto text-gray-600 mb-4" size={48} />
          <p className="text-gray-400 mb-2">No test tickets generated yet</p>
          <p className="text-gray-500 text-sm">
            Analyze an Epic and select a strategic option to generate test tickets
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {testTickets.map((ticket) => {
            const isExpanded = expandedTicket === ticket.id
            const isGenerating = generatingTestCases === ticket.id
            const qualityScore = ticket.quality_score || 0

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
                        <h3 className="text-xl font-semibold text-gray-100">
                          {ticket.id}: {ticket.summary}
                        </h3>

                        {ticket.analyzed && (
                          <div className="px-2 py-1 bg-green-500/10 border border-green-500/30 rounded-md flex items-center space-x-1">
                            <CheckCircle size={14} className="text-green-400" />
                            <span className="text-xs text-green-400 font-medium">Analyzed</span>
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
                        <p className="text-gray-400 text-sm whitespace-pre-wrap">{ticket.description}</p>
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
    </div>
  )
}
